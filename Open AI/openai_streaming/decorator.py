from collections.abc import AsyncGenerator
from inspect import iscoroutinefunction
from types import FunctionType
from typing import Generator, get_origin, Union, Optional, Any
from typing import get_args
from .openai_function import openai_function


def openai_streaming_function(func: FunctionType) -> Any:
    """
    Decorator that converts a function to an OpenAI streaming function using the `openai-function-call` package.
    It simply "reduces" the type of the arguments to the Generator type, and uses `openai_function` to do the rest.

    :param func: The function to convert
    :return: Wrapped function with a `openai_schema` attribute
    """
    if not iscoroutinefunction(func):
        raise ValueError("openai_streaming_function can only be applied to async functions")

    for key, val in func.__annotations__.items():
        optional = False

        args = get_args(val)
        if get_origin(val) is Union and len(args) == 2:
            gen = None
            other = None
            for arg in args:
                if isinstance(arg, type(None)):
                    optional = True
                if get_origin(arg) is get_origin(Generator) or get_origin(arg) is AsyncGenerator:
                    gen = arg
                else:
                    other = arg
            if gen is not None and (get_args(gen)[0] is other or optional):
                val = gen

        args = get_args(val)
        if get_origin(val) is get_origin(Generator):
            raise ValueError("openai_streaming_function does not support Generator type. Use AsyncGenerator instead.")
        if get_origin(val) is AsyncGenerator:
            val = args[0]

        if optional:
            val = Optional[val]
        func.__annotations__[key] = val

    wrapped = openai_function(func)
    if hasattr(wrapped, "model") and "self" in wrapped.model.model_fields:
        del wrapped.model.model_fields["self"]
    if hasattr(wrapped, "openai_schema") and "self" in wrapped.openai_schema["parameters"]["properties"]:
        del wrapped.openai_schema["parameters"]["properties"]["self"]
        for i, required in enumerate(wrapped.openai_schema["parameters"]["required"]):
            if required == "self":
                del wrapped.openai_schema["parameters"]["required"][i]
                break
    return wrapped
