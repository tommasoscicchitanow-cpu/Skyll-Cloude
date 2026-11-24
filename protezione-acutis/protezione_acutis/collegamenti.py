"""Collegamenti con icona per l'app Cassaforte, sul Desktop e nel menu Start.

Windows non permette di fissare un programma alla barra delle applicazioni
da uno script in modo affidabile: lo fa Tommaso con un clic destro (vedi la
guida)."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from .icona import scrivi_icona

NOME = "Cassaforte"
CARTELLA_PROGETTO = Path(__file__).resolve().parent.parent
ICONA = CARTELLA_PROGETTO / "cassaforte.ico"


def _vbs_stringa(testo: str) -> str:
    return '"' + str(testo).replace('"', '""') + '"'


def script_vbs(pythonw: Path, cartella: Path, icona: Path) -> str:
    return "\r\n".join([
        'Set sh = CreateObject("WScript.Shell")',
        'For Each dove In Array(sh.SpecialFolders("Desktop"), sh.SpecialFolders("Programs"))',
        f'  Set l = sh.CreateShortcut(dove & "\\{NOME}.lnk")',
        f"  l.TargetPath = {_vbs_stringa(pythonw)}",
        '  l.Arguments = "-m protezione_acutis app"',
        f"  l.WorkingDirectory = {_vbs_stringa(cartella)}",
        f"  l.IconLocation = {_vbs_stringa(str(icona) + ',0')}",
        '  l.Description = "Cassaforte: progetti protetti da frase e impronta"',
        "  l.Save",
        '  WScript.Echo "Creato: " & dove & "\\' + NOME + '.lnk"',
        "Next",
        "",
    ])


def crea_collegamenti() -> str:
    if os.name != "nt":
        raise RuntimeError("I collegamenti si creano solo su Windows.")
    scrivi_icona(ICONA)
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    if not pythonw.exists():
        pythonw = Path(sys.executable)
    fd, percorso = tempfile.mkstemp(suffix=".vbs")
    with os.fdopen(fd, "wb") as f:
        f.write(b"\xff\xfe" + script_vbs(pythonw, CARTELLA_PROGETTO, ICONA).encode("utf-16-le"))
    try:
        esito = subprocess.run(["cscript", "//nologo", "//U", percorso], capture_output=True,
                               check=True)
        return esito.stdout.decode("utf-16-le", errors="replace")
    finally:
        os.unlink(percorso)
