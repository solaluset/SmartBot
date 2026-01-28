from string import digits, ascii_uppercase
from typing import Callable, Literal
from decimal import (
    ROUND_CEILING,
    ROUND_DOWN,
    ROUND_FLOOR,
    ROUND_HALF_DOWN,
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
    ROUND_UP,
    Decimal,
)

DEFAULT_ALPHABET = digits + ascii_uppercase
DEFAULT_SIGNS = ("+", "-")
BUILTIN_FORMATS = {2: "b", 8: "o", 10: "", 16: "X"}
SUPPORTED_ROUNDINGS = (
    ROUND_UP,
    ROUND_CEILING,
    ROUND_DOWN,
    ROUND_FLOOR,
    ROUND_HALF_DOWN,
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
)


class Context:
    __slots__ = (
        "alphabet",
        "signs",
        "rounding",
        "radix_point",
        "uses_default_alphabet",
        "_parser",
        "_cache",
        "dec_signs",
    )
    _parser: Callable[[str, int], int]

    def __init__(
        self,
        alphabet: str | None = None,
        signs: tuple[str, str] = DEFAULT_SIGNS,
        rounding: str = ROUND_HALF_EVEN,
        radix_point: str = ".",
    ):
        self.uses_default_alphabet = alphabet is None
        if self.uses_default_alphabet:
            self.alphabet = DEFAULT_ALPHABET
            self._parser = int
        else:
            self.alphabet = alphabet
            self._parser = self._decode_int
            self._cache: dict[int, dict[str, int]] = {}
        assert (
            isinstance(signs, tuple) and len(signs) == 2
        ), "signs must be a tuple of two strings"
        self.signs = signs
        # replace empty strings with empty tuples to make .startswith() always fail
        self.dec_signs = tuple(sign if sign else () for sign in signs)
        assert rounding in SUPPORTED_ROUNDINGS, f"unsupported rounding: {rounding}"
        self.rounding = rounding
        self.radix_point = radix_point

    def parse_int(self, number: str, base: int) -> tuple[Literal[0, 1], int | None]:
        sign: Literal[0, 1]
        if number.startswith(self.dec_signs[1]):
            sign = 1
            number = number.replace(self.dec_signs[1], "", 1)
        else:
            sign = 0
            if number.startswith(self.dec_signs[0]):
                number = number.replace(self.dec_signs[0], "", 1)
        if number.startswith(DEFAULT_SIGNS) and self.uses_default_alphabet:
            raise ValueError("invalid number: unexpected sign")
        return sign, self._parser(number, base) if number else None

    def _decode_int(self, number: str, base: int) -> int:
        try:
            alphabet = self._cache[base]
        except KeyError:
            alphabet = self._cache[base] = {
                k: v for v, k in enumerate(self.alphabet[:base])
            }

        multiplier = 1
        result = 0
        for digit in reversed(number):
            try:
                result += alphabet[digit] * multiplier
            except KeyError as e:
                raise ValueError(
                    f"invalid literal for parse_int() with base {base}: {number!r}"
                ) from e
            multiplier *= base
        return result


_default_dectx = Context()
_default_enctx = Context(signs=("", "-"))


def convert_base(
    number: str | int | float | Decimal,
    to_base: int = 10,
    from_base: int = 10,
    *,
    precision: int = 16,
    decoding_ctx: Context = _default_dectx,
    encoding_ctx: Context = _default_enctx,
) -> str:
    assert (
        isinstance(number, str) or from_base == 10 and decoding_ctx is _default_dectx
    ), "non-default from_base or decoding_ctx accept number only as string"
    assert from_base >= 2 and to_base >= 2, "bases must be >= 2"
    assert (
        len(decoding_ctx.alphabet) >= from_base
    ), f"decoding alphabet too small for base {from_base}"
    assert (
        len(encoding_ctx.alphabet) >= to_base
    ), f"encoding alphabet too small for base {to_base}"

    result: list[str] = []

    if isinstance(number, int):
        if number < 0:
            number = -number
            sign = 1
        else:
            sign = 0
    else:
        if isinstance(number, float):
            number = Decimal.from_float(number)
        if isinstance(number, Decimal):
            number = f"{number:f}"

        number, _, fractional = number.partition(decoding_ctx.radix_point)
        if decoding_ctx.uses_default_alphabet:
            number = number.strip()
            fractional = fractional.strip()
        sign, number = decoding_ctx.parse_int(number, from_base)
        if number is None:
            if not fractional:
                raise ValueError(
                    "invalid number: both integral and fractional parts are missing"
                )
            number = 0
        if fractional:
            fractional, rounded_up = _convert_fractional(
                sign,
                number,
                fractional,
                to_base,
                from_base,
                precision,
                decoding_ctx,
                encoding_ctx,
            )
            if fractional:
                result.extend((fractional, encoding_ctx.radix_point))
            if rounded_up:
                number += 1

    if to_base in BUILTIN_FORMATS and encoding_ctx.uses_default_alphabet:
        result.append(f"{number:{BUILTIN_FORMATS[to_base]}}")
    else:
        while number:
            number, i = divmod(number, to_base)
            result.append(encoding_ctx.alphabet[i])

    result.append(encoding_ctx.signs[sign])

    result.reverse()
    return "".join(result)


def _convert_fractional(
    sign: Literal[0, 1],
    integer: int,
    fractional: str,
    to_base: int,
    from_base: int,
    precision: int,
    decoding_ctx: Context,
    encoding_ctx: Context,
) -> tuple[str, bool | Literal[0, 1]]:
    if fractional.startswith(decoding_ctx.dec_signs):
        raise ValueError("invalid number: fractional part cannot contain signs")
    denominator: int = from_base ** len(fractional)
    _, fractional = decoding_ctx.parse_int(fractional, from_base)
    # fractional cannot be None because the function is not called if it is empty
    # and sign stripping is not applied
    fractional: int

    if precision <= 0:
        return "", _round_div(
            sign, integer, fractional, denominator, encoding_ctx.rounding
        )
    precision -= 1

    result: list[int] = []
    while fractional and precision:
        i, fractional = divmod(fractional * to_base, denominator)
        result.append(i)
        precision -= 1
    result.append(
        _round_div(
            sign,
            None,
            fractional * to_base,
            denominator,
            encoding_ctx.rounding,
        )
    )

    while result[-1] == to_base:
        result.pop()
        if not result:
            # rounded up
            return "", True
        result[-1] += 1

    # remove trailing zeros
    while not result[-1]:
        result.pop()
        if not result:
            return "", False

    return (
        "".join(encoding_ctx.alphabet[i] for i in result),
        False,
    )


def _round_div(
    sign: Literal[0, 1], integer: int | None, f: int, d: int, mode: str
) -> int:
    result, f = divmod(f, d)

    if not f or mode == ROUND_DOWN:
        return result
    elif mode == ROUND_UP:
        return result + 1
    elif mode == ROUND_FLOOR:
        return result + 1 if sign else result
    elif mode == ROUND_CEILING:
        return result + 1 if not sign else result

    f *= 2
    if f < d:
        return result
    elif f > d:
        return result + 1

    if mode == ROUND_HALF_DOWN:
        return result
    elif mode == ROUND_HALF_UP:
        return result + 1
    # ROUND_HALF_EVEN
    return result + (integer if integer is not None else result) % 2
