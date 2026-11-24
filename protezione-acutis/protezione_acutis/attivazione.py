"""Interruttore di attivazione.

Il sistema resta DISATTIVATO finché non esiste un file locale
``configurazione.locale.json`` con ``"attivo": true``. Il file
``configurazione.json`` del repository deve restare sempre a false. Da disattivato:
  * funziona solo in modalità prova, su file dentro una cartella temporanea;
  * si possono usare solo fattori biometrici simulati.
Da attivato:
  * i fattori biometrici simulati vengono rifiutati;
  * si usano i parametri Argon2 di produzione.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .biometria import FattoreBiometrico
from .cripto import MINIMI_PRODUZIONE, ParametriArgon2, cifra, decifra

_CARTELLA = Path(__file__).resolve().parent.parent
CONFIGURAZIONE_REPOSITORY = _CARTELLA / "configurazione.json"
# File solo locale (escluso da git): è qui che si accende il sistema, così il
# repository pubblico resta sempre spento.
CONFIGURAZIONE_LOCALE = _CARTELLA / "configurazione.locale.json"
CONFIGURAZIONE_PREDEFINITA = CONFIGURAZIONE_LOCALE
ESTENSIONE = ".acutis"


class SistemaDisattivato(RuntimeError):
    """Operazione non consentita finché il sistema non è attivato."""


def sistema_attivo(percorso_config: Path | None = None) -> bool:
    """Legge l'interruttore. Se il file manca, il sistema è spento."""
    if percorso_config is None:
        percorso_config = CONFIGURAZIONE_PREDEFINITA
    try:
        dati = json.loads(Path(percorso_config).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False
    # Solo il booleano true attiva: "true", 1, "si" ecc. NON attivano.
    return dati.get("attivo") is True


def _dentro_cartella_temporanea(percorso: Path) -> bool:
    radice = Path(tempfile.gettempdir()).resolve()
    try:
        Path(percorso).resolve().relative_to(radice)
        return True
    except ValueError:
        return False


class Cassaforte:
    """Cifra e decifra file su disco rispettando l'interruttore."""

    def __init__(
        self,
        biometria: FattoreBiometrico,
        percorso_config: Path | None = None,
        parametri: ParametriArgon2 | None = None,
    ):
        self.attivo = sistema_attivo(percorso_config)
        if self.attivo and biometria.simulato:
            raise SistemaDisattivato(
                "Sistema attivo: la biometria simulata non è ammessa. "
                "Configurare un fattore biometrico reale."
            )
        if not self.attivo and not biometria.simulato:
            raise SistemaDisattivato(
                "Sistema disattivato: la biometria reale si collega solo "
                "dopo l'attivazione (vedi GUIDA_ATTIVAZIONE.md)."
            )
        self.biometria = biometria
        if self.attivo:
            self.parametri = MINIMI_PRODUZIONE
        else:
            self.parametri = parametri or ParametriArgon2.per_test()

    def _controlla_percorso(self, percorso: Path) -> None:
        if not self.attivo and not _dentro_cartella_temporanea(percorso):
            raise SistemaDisattivato(
                f"Sistema disattivato: in modalità prova si lavora solo dentro "
                f"{tempfile.gettempdir()}. File rifiutato: {percorso}"
            )

    def cifra_file(self, origine: Path, frase: str, elimina_originale: bool = False) -> Path:
        origine = Path(origine)
        self._controlla_percorso(origine)
        destinazione = origine.with_name(origine.name + ESTENSIONE)
        self._controlla_percorso(destinazione)
        contenitore = cifra(origine.read_bytes(), frase, self.biometria, self.parametri)
        temporaneo = destinazione.with_name(destinazione.name + ".parziale")
        temporaneo.write_bytes(contenitore)
        os.replace(temporaneo, destinazione)
        if elimina_originale:
            origine.unlink()
        return destinazione

    def decifra_file(self, origine: Path, frase: str) -> bytes:
        origine = Path(origine)
        self._controlla_percorso(origine)
        minimi = MINIMI_PRODUZIONE if self.attivo else ParametriArgon2.per_test()
        return decifra(origine.read_bytes(), frase, self.biometria, minimi)
