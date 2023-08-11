from pdsf import *

with AspectHooks():
    from test2 import g
    from test3 import SomeClass

def around_f(target, *args, **kwargs):
    print("before " + target.__name__)
    ret = target(*args, **kwargs)
    print("after " + target.__name__)
    return ret

def mark_invocation(target, *args, **kwargs):
    print(target, target.__name__)

AspectHooks.add_prelude("functotest", mark_invocation)
# AspectHooks.add_around("functotest", around_f)
# f()
# C().f()
# g(f)
# f()
SomeClass().functotest()
