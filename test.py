class Alpha:
    one = 1
    two = 2

alp = Alpha()


print(getattr(alp, "three", "default values"))
print(getattr(alp, "two", "default values"))