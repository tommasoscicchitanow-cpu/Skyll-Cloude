"""Lettura della frase segreta dal terminale.

Su Windows mostra un asterisco per ogni carattere digitato, così si vede che
la tastiera sta scrivendo, ma il testo non compare mai a schermo. Altrove, o se
non c'è una console vera, si usa getpass (nessun eco).
"""

from __future__ import annotations

import getpass
import sys


def _leggi_con_asterischi(richiesta: str, getwch, scrivi) -> str:
    scrivi(richiesta)
    caratteri: list[str] = []
    while True:
        c = getwch()
        if c in ("\r", "\n"):
            scrivi("\r\n")
            return "".join(caratteri)
        if c == "\x03":  # Ctrl+C
            scrivi("\r\n")
            raise KeyboardInterrupt
        if c in ("\x00", "\xe0"):  # tasti speciali (frecce, F1...): ignorati
            getwch()
            continue
        if c == "\b":
            if caratteri:
                caratteri.pop()
                scrivi("\b \b")
            continue
        if c == "\x16":  # Ctrl+V non è gestito: si digita a mano
            continue
        if c.isprintable() or c == " ":
            caratteri.append(c)
            scrivi("*")


def leggi_frase(richiesta: str) -> str:
    if sys.platform == "win32" and sys.stdin is not None and sys.stdin.isatty():
        try:
            import msvcrt
        except ImportError:
            return getpass.getpass(richiesta)

        def scrivi(testo: str) -> None:
            for c in testo:
                msvcrt.putwch(c)

        return _leggi_con_asterischi(richiesta, msvcrt.getwch, scrivi)
    return getpass.getpass(richiesta)
