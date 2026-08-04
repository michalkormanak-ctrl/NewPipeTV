"""Ochrana pred prompt injection v načítaných dokumentoch (sekcia 16.2).

Text z dokumentov je vždy DATA, nie systémové pokyny. Táto funkcia
neodstraňuje obsah (dokument sa nesmie okliesniť ako právny prameň), iba
escapuje sekvencie, ktoré by mohli byť interpretované ako ohraničenie
kontextového bloku, a odstraňuje kontrolné/neviditeľné znaky bežne
zneužívané na injekciu."""
from __future__ import annotations

import re
import unicodedata

# Neviditeľné/riadiace znaky bežne zneužívané na skrytie injektovaného textu.
# Zostavené z celočíselných kódových bodov (chr(...)), aby zoznam bol
# jednoznačný v code review bez závislosti na tom, ako editor zobrazuje
# neviditeľné glyfy priamo v zdrojovom súbore.
_INVISIBLE_CODEPOINTS = (
    list(range(0x200B, 0x200F + 1))  # zero-width space/ZWNJ/ZWJ, LRM, RLM
    + list(range(0x202A, 0x202E + 1))  # smerové ovládanie (embedding/override)
    + [0x2060]  # word joiner
    + [0xFEFF]  # byte order mark
    + list(range(0x00, 0x09))  # C0 riadiace znaky pred \t
    + [0x0B, 0x0C]  # vertical tab, form feed
    + list(range(0x0E, 0x20))  # C0 riadiace znaky za \r, pred medzerou
    + [0x7F]  # DEL
)

_INVISIBLE_CHARS_RE = re.compile(
    "[" + "".join(re.escape(chr(cp)) for cp in _INVISIBLE_CODEPOINTS) + "]"
)


def sanitize_document_text(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text)
    without_control_chars = _INVISIBLE_CHARS_RE.sub("", normalized)
    # Zabráni predčasnému ukončeniu <document> bloku vloženým textom.
    escaped = without_control_chars.replace("</document>", "&lt;/document&gt;").replace(
        "<document", "&lt;document"
    )
    return escaped
