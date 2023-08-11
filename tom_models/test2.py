import test3

def g(f):
    print(f == test3.f)
    f()
    return test3.f()