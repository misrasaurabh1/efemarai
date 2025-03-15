import re
from functools import lru_cache


class DictLiteral(dict):
    pass


class ListLiteral(list):
    pass


class TupleLiteral(tuple):
    pass


class CreateCall(tuple):
    pass


def convert(spec, xs):
    """Converts data according to provided spec."""
    env = {}
    ys = eval(spec, xs, env)
    return ys


# Some syntactic sugar (rewriting macros)
def call(*args, **kwargs):
    """Escapes names of kwargs with a '."""
    return *args, *(DictLiteral({"'" + name: value}) for name, value in kwargs.items())


def create(*args, **kwargs):
    if args[0] is dict:
        return CreateCall(call(DictLiteral, **kwargs))

    if args[0] is list:
        return CreateCall(call(ListLiteral, *args[1:]))

    if args[0] is tuple:
        return CreateCall(call(TupleLiteral, *args[1:]))

    return CreateCall(call(*args, **kwargs))


def eval(term, x, env):
    # Access data fields
    if isinstance(term, str):
        return eval_str(term, x, env)

    # Handle literal data structs specified by the user
    term_type = type(term)
    if term_type is DictLiteral:
        return {eval(name, x, env): eval(value, x, env) for name, value in term.items()}

    if term_type is ListLiteral:
        return [eval(item, x, env) for item in term]

    if term_type is TupleLiteral:
        return tuple(eval(item, x, env) for item in term)

    if isinstance(term, tuple):
        # if first element is callable then call a function (a la LISP),
        # otherwise perform eval on each element
        if not callable(term[0]):
            return tuple(eval(t, v, env) for t, v in zip(term, x))

        return eval_call(term, x, env)

    # Iterate over a list and process every element
    if isinstance(term, list):
        return [eval(term[0], item, env) for item in x]

    # Data transformation
    if isinstance(term, dict):
        key, value = next(iter(term.items()))

        if isinstance(key, int):
            key = f"[{key}]"

        return eval(value, eval(key, x, env), env)

    # Handle leaf functions as plain function application
    if callable(term):
        return term(x)

    # Default to treating the term as a constant
    return term


def eval_str(term: str, x: any, env: dict):
    # Escaped strings (i.e. 'str or 'str') are literals so return them
    if term.startswith("'"):
        if term.endswith("'"):
            return term[1:-1]
        else:
            return term[1:]

    # Handle multiple accessors
    accessors = extract_accessors(term)

    # Handle nested accessors
    if len(accessors) > 1:
        res = eval(accessors[0], x, env)
        return eval("".join(accessors[1:]), res, env)

    # Latest result (same as ipython)
    if term == "_":
        return x

    # Class attribute access
    if term.startswith("."):
        return getattr(x, term[1:])

    # Item access with [ ]
    if term.startswith("[") and term.endswith("]"):
        term = term[1:-1]

    # Integer index access
    if term.isdigit() or (term.startswith("-") and term[1:].isdigit()):
        term = int(term)

    return x[term]


def eval_call(term: tuple, x: any, env: dict):
    fn, *rest = term
    args = []
    kwargs = {}

    for arg in rest:
        if isinstance(arg, DictLiteral):
            kwargs.update(eval(arg, x, env))
        else:
            args.append(eval(arg, x, env))

    return fn(*args, **kwargs)


@lru_cache(None)
def extract_accessors(term):
    # Find multiple accessors in a single string.
    return re.findall(r"\[[0-9]+\]|\.?[^\W0-9]\w+", term)
