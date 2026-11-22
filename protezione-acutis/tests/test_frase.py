"""Prove dell'inserimento della frase con asterischi (tastiera simulata)."""

import pytest

from protezione_acutis.frase import _leggi_con_asterischi


def _digita(tasti):
    uscita = []
    sequenza = iter(tasti)
    frase = _leggi_con_asterischi("Frase: ", lambda: next(sequenza), uscita.append)
    return frase, "".join(uscita)


def test_mostra_solo_asterischi():
    frase, schermo = _digita(list("gatto viola è") + ["\r"])
    assert frase == "gatto viola è"
    assert schermo == "Frase: " + "*" * len("gatto viola è") + "\r\n"
    assert "gatto" not in schermo


def test_backspace_cancella_un_carattere():
    frase, schermo = _digita(["a", "b", "\b", "c", "\r"])
    assert frase == "ac"
    assert schermo.count("\b \b") == 1


def test_backspace_a_vuoto_non_fa_nulla():
    frase, _ = _digita(["\b", "x", "\r"])
    assert frase == "x"


def test_tasti_speciali_ignorati():
    frase, schermo = _digita(["a", "\xe0", "K", "b", "\x00", ";", "\r"])
    assert frase == "ab" and schermo.count("*") == 2


def test_ctrl_c_interrompe():
    with pytest.raises(KeyboardInterrupt):
        _digita(["a", "\x03"])
