__all__ = ("AVAILABLE_LANGUAGES", "init", "t")

import os
import logging as log

import i18n
from i18n import t


LOCALES_PATH = "./locales"
AVAILABLE_LANGUAGES = [i.rpartition(".")[0] for i in os.listdir(LOCALES_PATH)]


def init():
    i18n.load_path.append(LOCALES_PATH)
    i18n.set("filename_format", "{locale}.{format}")
    i18n.set("skip_locale_root_data", True)
    i18n.set("on_missing_translation", handle_missing_translation)
    i18n.set("enable_memoization", True)

    i18n.add_function("p", plural_uk, "uk")
    i18n.add_function("p", plural_en, "en")


def handle_missing_translation(key, locale, **_):
    log.error(f"No translation for {key!r} ({locale})")
    return key


def plural_uk(*args: str, count: int, **kwargs) -> str:
    count = abs(count)
    rem = count % 10
    if rem >= 5 or rem == 0 or 11 <= count % 100 <= 19:
        return args[2]
    elif rem == 1:
        return args[0]
    return args[1]


def plural_en(*args: str, count: int, **kwargs) -> str:
    return args[abs(count) != 1]
