file = open('Coding.txt','r')
print(file.read())
file.close()

file = open('Coding.txt','r')
print("\n Readin parts \n")
print(file.read(8))
file.close

file = open('Coding.txt','a')
file.write("Hi! I am Penguin and I am 1 year old.")
file.close