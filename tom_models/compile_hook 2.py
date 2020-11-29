import builtins # import builtins
from copy import deepcopy
from forbiddenfruit import curse

old_compile = deepcopy(builtins.compile)

def new_compile(*args, **kwargs):
    print("in new compile")
    ret = old_compile(*args, **kwargs)
    print("compiled " + str(ret))
    print()
    return ret

# builtins.compile = new_compile
# curse(__builtins__, "compile", new_compile)
builtins.compile = new_compile
print("hooooked!")