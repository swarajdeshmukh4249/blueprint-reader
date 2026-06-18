n=int(input("enter the num to find factorial:"))

def fact(n):
    if n==0 or n==1:
        facto=1
    else:
        facto=n*fact(n-1)
    return facto

x=fact(n)
print(x)