from inspect import isfunction, isclass, ismethod
import re
import builtins
from functools import wraps, partial, reduce
from copy import deepcopy
import ast
from textwrap import dedent
import copy
import inspect
from types import FunctionType


class AspectHooks:

    pre_rules = list()
    around_rules = list()
    post_rules = list()
    error_handling_rules = list()
    fuzzers = list()

    def __enter__(self, *args, **kwargs):
        self.old_import = __import__
        import builtins
        builtins.__import__ = self.__import__

    def final_around(self, target, *args, **kwargs):
        return target(*args, **kwargs)


    def __import__(self, *args, **kwargs):
        mod = self.old_import(*args, **kwargs)

        def build_wrapper(target):

            class CouldNotFuzzException(Exception):
                pass

            @wraps(target)
            def wrapper(*args, **kwargs):

                pre, around, post, error_handlers, fuzzers = self.get_rules(target.__name__)
                old_target_code = copy.deepcopy(target.__code__)

                def reset_code_to_previous():
                    if not isinstance(target, FunctionType):
                        target.__func__.__code__ = old_target_code
                    else:
                        target.__code__ = old_target_code

                try:

                    if fuzzers is not None and fuzzers != []:
                        code = dedent(inspect.getsource(target))
                        target_ast = ast.parse(code)
                        funcbody_steps = target_ast.body[0].body  # Assume we've got a module object containing only a function definition.

                        for fuzzer in fuzzers:
                            non_inline_changed_steps = fuzzer(funcbody_steps, *args, **kwargs)

                            if non_inline_changed_steps:
                                funcbody_steps = non_inline_changed_steps

                        print(funcbody_steps)
                        compiled_fuzzed_target = compile(target_ast, "<ast>", "exec")
                        if not isinstance(target, FunctionType):
                            target.__func__.__code__ =  compiled_fuzzed_target.co_consts[0]
                        else:
                            target.__code__ = compiled_fuzzed_target.co_consts[0]

                    # Run pre advice
                    [advice(target, *args, **kwargs) for advice in pre]

                    def nest_around_call(nested_around, next_around):
                        return partial(next_around, nested_around)

                    # NOTE. The signature of around functions is around(next_around_function, target, *args, **kwargs),
                    # ... and they MUST make the call next_around_function(target*args, **kwargs)
                    # for around_index in range(len(around-1)):
                    #     around[around_index] = partial(around[around_index], around_index[around_index+1])
                    # around[-1] = partial(around[-1], self.final_around)

                    nested_around = reduce(nest_around_call,
                                           around[::-1],
                                           self.final_around)

                    ret = nested_around(target, *args, **kwargs)

                    for advice in post:
                        post_return = advice(target, ret, *args, **kwargs)
                        ret = ret if post_return is None else post_return

                    reset_code_to_previous()

                    return ret
                except Exception as exception:

                    # Oh no! We might have fuzzed and then thrown an exception before we could replace the fuzzed code object. Make sure that's done now.
                    reset_code_to_previous()

                    prevent_raising = False
                    for handler in error_handlers:
                        prevent_raising = prevent_raising or handler(target, exception, *args, **kwargs)
                    if not prevent_raising:
                        raise exception

            return wrapper

        def apply_hooks(target_object):
            for item_name in filter(lambda p: isinstance(p, str) and len(p) > 1 and p[:2] != "__", dir(target_object)):
                item = getattr(target_object, item_name)
                if isfunction(item) or ismethod(item):
                    setattr(target_object, item_name, build_wrapper(item))
                elif isclass(item):
                    apply_hooks(item)

        apply_hooks(mod)

        return mod

    @classmethod
    def add_prelude(cls, rule, advice, urgency=0):
        AspectHooks.pre_rules.append((re.compile(rule), advice, urgency))

    @classmethod
    def add_around(cls, rule, advice, urgency=0):
        AspectHooks.around_rules.append((re.compile(rule), advice, urgency))

    @classmethod
    def add_encore(cls, rule, advice, urgency=0):
        AspectHooks.post_rules.append((re.compile(rule), advice, urgency))

    @classmethod
    def add_error_handler(cls, rule, advice, urgency=0):
        AspectHooks.error_handling_rules.append((re.compile(rule), advice, urgency))

    @classmethod
    def add_fuzzer(self, rule, advice, urgency=0):
        AspectHooks.fuzzers.append((re.compile(rule), advice, urgency))

    def get_rules(self, methodname):
        pre, around, post, error_handlers, fuzzers = list(), list(), list(), list(), list()
        for pattern, advice, urgency in AspectHooks.pre_rules:
            if pattern.match(methodname) is not None:
                pre.append((advice, urgency))

        for pattern, advice, urgency in AspectHooks.around_rules:
            if pattern.match(methodname) is not None:
                around.append((advice, urgency))

        for pattern, advice, urgency in AspectHooks.post_rules:
            if pattern.match(methodname) is not None:
                post.append((advice, urgency))

        for pattern, advice, urgency in AspectHooks.error_handling_rules:
            if pattern.match(methodname) is not None:
                error_handlers.append((advice, urgency))

        for pattern, advice, urgency in AspectHooks.fuzzers:
            if pattern.match(methodname):
                fuzzers.append((advice, urgency))

        urgencykey = lambda ad_urg_tuple: -ad_urg_tuple[1]  # Negative so we get the highest urgency first
        first = lambda x: x[0]
        pre, around, post, error_handlers, fuzzers = sorted(pre, key=urgencykey), sorted(around, key=urgencykey), sorted(post, key=urgencykey), sorted(error_handlers, key=urgencykey), sorted(fuzzers, key=urgencykey)
        advice_functions = list(map(first, pre)), list(map(first, around)), list(map(first, post)), list(map(first, error_handlers)), list(map(first, fuzzers))
        return advice_functions


    def __exit__(self, *args, **kwargs):
        builtins.__import__ = self.old_import

if __name__ == "__main__":
    from math import pow
    with AspectHooks():
        import testmod
    invocations = 0
    def encore(*args, **kwargs):
        global invocations
        invocations += 1
    def loggingaround(next_around, target, *args, **kwargs):
        print("running " + str(target))
        ret = next_around(target, *args, **kwargs)
        print(str(target) + " returned " + str(ret))
        return ret
    def switch_to_power_of_two(next_around, target, *args, **kwargs):
        return next_around(partial(pow, 2), *args, **kwargs)

    def remove_final_statement(steps, *args, **kwargs):
        steps.pop()

    AspectHooks.add_encore(".*", encore)
    AspectHooks.add_around(".*", loggingaround)
    assert testmod.dosomething() is None
    assert testmod.Calc().triple(4) == 12

    assert testmod.double(5) == 10
    AspectHooks.add_around("double", switch_to_power_of_two)
    assert testmod.double(5) == 32

    AspectHooks.add_fuzzer('triple', remove_final_statement)
    assert testmod.Calc().triple(5) is None

    assert invocations == 5

