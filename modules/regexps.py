from re import compile

ARG = compile(r"(?<!\\|\w)\$(\w+)\b")
WORD_PATTERN = r"(?<!\S)\S+(?!\S)"
QUOTED_PATTERN = r'(?<!\\)".*?(?<!\\)"'
ARGUMENT_TEMPLATE = rf"(?P<%s>{WORD_PATTERN}|{QUOTED_PATTERN})"
SIDE_QUOTES = compile('^"|"$')
VAR_ARG = compile(r"(?<!\\)\$\*")
_ID = r"\d{15,20}"
ID = compile(_ID)
PING = compile(f"<@!?(?P<id>{_ID})>")
