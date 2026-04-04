def power(a,b):
    if b == 0:
        return 1
    if b % 2 == 0:
        half = power(a, b // 2)
        return half * half
    else:
        return a * power(a, b - 1)
a = int(input("Enter base: "))
b = int(input("Enter exponent: "))
print("Result:", power(a, b))