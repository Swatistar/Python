import os, subprocess, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--disable-pip-version-check", "-r", os.path.join(HERE, "requirements.txt")])
import cv2
import numpy as np
import onnxruntime

HALF, PAINT_SIZE, FONT, WHITE = (320, 240), 180, cv2.FONT_HERSHEY_SIMPLEX, (255, 255, 255)
PAINTING = np.load(os.path.join(HERE, "painting.npy"))
STYLES = ["candy", "mosaic", "udnie", "rain_princess"] + list(PAINTING.files) + ["rules filter (no AI)"]
shared = {"picture": None, "painted": None, "matte": None, "style": 0, "painted_count": 0, "matte_count": 0, "running": True}
options = onnxruntime.SessionOptions()
options.intra_op_num_threads = 1

options.add_session_config_entry("session.intra_op.allow_spinning", "0")
painters = [onnxruntime.InferenceSession(os.path.join(HERE, name + "_style.onnx"), options) for name in STYLES[:4]]
any_style = onnxruntime.InferenceSession(os.path.join(HERE, "any_style_transfer.onnx"), options)

def paint(picture, style):
    if STYLES[style] in PAINTING.files:
        x = cv2.cvtColor(picture, cv2.COLOR_BGR2RGB)
        y = any_style.run(None, {"content_image": x, any_style.get_inputs()[1].name: PAINTING[STYLES[style]]})[0][0]
        return cv2.cvtColor((np.clip(y, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
    if style == len(STYLES) - 1:
        edges = cv2.adaptiveThreshold(cv2.medianBlur(cv2.cvtColor(picture, cv2.COLOR_BGR2GRAY), 5), 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 4)
        return cv2.bilateralFilter(picture, 7, 60, 60) * (edges[:, :, None] > 0)
    small = cv2.resize(picture, (round(HALF[0] * PAINT_SIZE / HALF[1]/4) * 4, PAINT_SIZE))
    x = cv2.cvtColor(small, cv2.COLOR_BGR2RGB). astype(np.float32).transpose(2, 0, 1) [None]
    y = painters[style].run(None, {painters[style].get_inputs()[0].name: x})[0][0]
    return cv2.resize(cv2.cvtColor(np.clip(y, 0, 255).astype(np.uint8).transpose(1, 2, 0), cv2.COLOR_RGB2BGR), HALF)

def cut_out(picture, size=244):
    small = cv2.resize(picture, (round(HALF[0] * size / HALF[1]/32) * 32, size))
    x = (cv2.cvtColor(small,cv2.COLOR_BGR2RGB). astype(np.float32) / 127.5-1).transpose(2, 0, 1) [None]
    return cv2.resize(cutter.run(None, {cutter.get_inputs()[0].name: x})[0][0].HALF)

def keep_working(job, answer):
    last = None
    while shared["running"]:
        picture = shared["picture"]
        if picture is None or picture is last:
            time.sleep(0.005)
            continue
        last, shared[answer] = picture, job(picture)
        shared[answer + "_count"] += 1

workers = [threading.Thread(target=keep_working, args=job, daemon=True) for job in ((lambda picture: paint(picture, shared["style"]), "painted"), (cut_out, "matte"))]
for worker in workers:
    worker.start()
video = cv2.VideoCapture(0)
for setting, value in ((cv2.CAP_PROP_FRAME_WIDTH, 640), (cv2.CAP_PROP_FRAME_HEIGHT, 480), (cv2.CAP_PROP_FPS, 30), (cv2.CAP_PROP_BUFFERSIZE, 1)):
    video.set(setting, value)
frames, couted_at, rate, message,message_until = 0, time.time(), (0.0, 0.0, 0.0), "", 0
try:
    while True:
        ok, frame = video.read()
        if not ok:
            break
        print("Error: Could not read frame from webcam.")
        matte, painted = shared["matte"], shared["painted"]
        right = picture if matte is None or painted is None else (picture * matte[:, :, None]+ painted * (1 - matte[:, :, None])).astype(np.uint8)
        screen = cv2.resize(np.hstack([picture, right]), (HALF[0] * 4, HALF[1] * 2))
        view, frames = screen.copy(), frames + 1
        if time.time() - couted_at >= 1:
            rates = [count / (time.time()- counted_at) for count in (frames, shared["matte_count"], shared["painted_count"])]
            frames, shared["matte_count"], shared["painted_count"], counted_at = 0, 0, 0,time.time()
        cv2.putText(view, f"Camera: {rates[0]:.0f} per second", (10,25), FONT, 0.6, WHITE, 2)
        cv2.putText(view, f"{STYLES[shared['style']]}: cut-out {rates[1]:.0f}, painting {rates[2]:.0f} per second", (HALF[0] * 2 + 10, 25), FONT, 0.6, WHITE, 2)
        cv2.putText(view, message if time.time() < message_until else "1-9 AI style 0 rules filter s save q quit", (10, view.shape[0] - 15), FONT, 0.6, WHITE, 2)
        cv2.imshow("Living Painting", view)
        key = chr(cv2.waitKey(1) & 255).lower()
        if key in ("q", "\x1b") or cv2.getWindowProperty("Living Painting", cv2.WND_PROP_VISIBLE) == 0:
            break
        if key.isdigit():
            shared["style"] = int(key) % len(STYLES)
        if key == "s":
            name = time.strftime("painting_%H%M%S.jpg")
            cv2.imwrite(os.path.join(HERE, name), screen)
            message, message_until = "Saved" + name, time.time() + 2

finally:
    shared["running"] = False
    for worker in workers:
        worker.join()
    video.release()
    cv2.destroyAllWindows()
