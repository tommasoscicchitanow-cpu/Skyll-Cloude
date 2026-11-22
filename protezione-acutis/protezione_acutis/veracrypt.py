"""Collegamento a VeraCrypt: partizione o contenitore con doppia chiave.

Il volume VeraCrypt viene creato con DUE elementi obbligatori:
  * la password = la frase segreta di Tommaso, digitata direttamente nella
    finestra di VeraCrypt (mai passata da riga di comando, dove altri
    programmi potrebbero leggerla);
  * un file chiave (keyfile) di 64 byte che NON è salvato da nessuna parte:
    viene ricalcolato ogni volta dal segreto che il telefono (o Windows Hello)
    rilascia solo dopo l'impronta.

Il file chiave esiste su disco solo per i pochi secondi del montaggio, in un
file temporaneo leggibile solo dall'utente, e poi viene sovrascritto e
cancellato.

Sul disco resta soltanto ``chiave-veracrypt.json``, che contiene
l'identificativo pubblico della passkey: senza telefono e impronta non serve a
nulla.
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterator

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from .attivazione import SistemaDisattivato, sistema_attivo
from .biometria import FattoreBiometrico

INFO_KEYFILE = b"protezione-acutis/v1/keyfile-veracrypt"
LUNGHEZZA_KEYFILE = 64
ESEGUIBILE_WINDOWS = Path(r"C:\Program Files\VeraCrypt\VeraCrypt.exe")


def prepara(biometria: FattoreBiometrico, file_identificativo: Path) -> None:
    """Registra la passkey (chiede l'impronta) e salva l'identificativo
    pubblico. Da fare una volta sola, prima di creare il volume."""
    file_identificativo = Path(file_identificativo)
    if file_identificativo.exists():
        raise FileExistsError(
            f"{file_identificativo} esiste già: sovrascriverlo renderebbe "
            "inapribile il volume creato con il vecchio file chiave."
        )
    identificativo = biometria.registra()
    file_identificativo.write_text(
        json.dumps({"versione": 1, "biometria": identificativo}, indent=2),
        encoding="utf-8",
    )


def calcola_keyfile(biometria: FattoreBiometrico, file_identificativo: Path) -> bytes:
    """Chiede l'impronta e ricalcola il contenuto del file chiave."""
    dati = json.loads(Path(file_identificativo).read_text(encoding="utf-8"))
    segreto = biometria.sblocca(dati["biometria"])
    return HKDF(
        algorithm=hashes.SHA256(), length=LUNGHEZZA_KEYFILE, salt=None, info=INFO_KEYFILE
    ).derive(segreto)


@contextlib.contextmanager
def keyfile_temporaneo(contenuto: bytes) -> Iterator[Path]:
    """Scrive il file chiave in un file temporaneo privato e lo distrugge
    all'uscita, anche in caso di errore."""
    descrittore, nome = tempfile.mkstemp(prefix="pa-", suffix=".key")
    percorso = Path(nome)
    try:
        with os.fdopen(descrittore, "wb") as f:
            f.write(contenuto)
        if sys.platform != "win32":
            os.chmod(percorso, 0o600)
        yield percorso
    finally:
        try:
            with open(percorso, "r+b") as f:
                f.write(os.urandom(len(contenuto)))
                f.flush()
                os.fsync(f.fileno())
        except FileNotFoundError:
            pass
        with contextlib.suppress(FileNotFoundError):
            percorso.unlink()


def comando_monta(volume: str, lettera: str, keyfile: Path, eseguibile: Path = ESEGUIBILE_WINDOWS) -> list[str]:
    """Riga di comando di VeraCrypt per Windows. Nessuna password: VeraCrypt
    la chiede nella sua finestra."""
    lettera = lettera.rstrip(":").upper()
    if len(lettera) != 1 or not lettera.isalpha():
        raise ValueError("Lettera di unità non valida.")
    return [str(eseguibile), "/volume", volume, "/letter", lettera, "/keyfile", str(keyfile), "/quit"]


def comando_smonta(lettera: str, eseguibile: Path = ESEGUIBILE_WINDOWS) -> list[str]:
    lettera = lettera.rstrip(":").upper()
    return [str(eseguibile), "/dismount", lettera, "/quit", "/silent"]


def _controlla_volume(volume: str, attivo: bool) -> None:
    if attivo:
        return
    radice = Path(tempfile.gettempdir()).resolve()
    try:
        Path(volume).resolve().relative_to(radice)
    except (ValueError, OSError):
        raise SistemaDisattivato(
            "Sistema disattivato: in modalità prova si monta solo un contenitore "
            f"di prova dentro {radice}, mai una partizione o un disco reale."
        ) from None


def monta(
    biometria: FattoreBiometrico,
    file_identificativo: Path,
    volume: str,
    lettera: str,
    esegui=subprocess.run,
    attivo: bool | None = None,
) -> int:
    """Chiede l'impronta, prepara il file chiave per un istante e lancia
    VeraCrypt, che chiederà la frase."""
    attivo = sistema_attivo() if attivo is None else attivo
    _controlla_volume(volume, attivo)
    if esegui is subprocess.run and not (ESEGUIBILE_WINDOWS.exists() or shutil.which("veracrypt")):
        raise FileNotFoundError("VeraCrypt non è installato.")
    contenuto = calcola_keyfile(biometria, file_identificativo)
    with keyfile_temporaneo(contenuto) as keyfile:
        esito = esegui(comando_monta(volume, lettera, keyfile))
    return getattr(esito, "returncode", 0)
