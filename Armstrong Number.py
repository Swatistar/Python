number = int(input("Input your number: "))
digits = len(str(number))
resultNumber = 0
temp = number
while temp > 0:
    digits = temp % 10
    resultNumber += digits ** digits
    temp //= 10
if number == resultNumber:
    print(number, "is an Armstrong number")
else:
    print(number, "is not an Armstrong number")