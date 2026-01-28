import ast
from io import StringIO
from types import FunctionType
from inspect import iscoroutine
from traceback import print_exc
from contextlib import redirect_stdout
from typing import Any, Iterable, Sequence, TypeVar

T = TypeVar("T")


async def execute(code: str, globals: dict[str, Any] = {}) -> str:
    output = StringIO()
    try:
        code = compile(code, "<message>", "exec", ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        func = FunctionType(code, globals)
        with redirect_stdout(output):
            coro = func()
            if iscoroutine(coro):
                await coro
    except Exception:
        print_exc(file=output)
    return output.getvalue()


def chunks(lst: Sequence[T], n: int) -> Iterable[Sequence[T]]:
    for i in range(0, len(lst), n):
        yield lst[i : i + n]  # noqa: E203
