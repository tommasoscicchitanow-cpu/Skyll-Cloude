"""Lavoro quotidiano sull'archivio: apri per lavorare, poi chiudi e proteggi.

``apri_lavoro`` estrae tutto l'archivio in una cartella di lavoro unica.
``chiudi_lavoro`` riporta nell'archivio i file nuovi e modificati, verifica
ogni file con SHA-256 decifrando davvero la copia archiviata, e solo se tutto
torna sovrascrive e cancella la cartella di lavoro.

Dove sta la cartella di lavoro: accanto all'archivio, sullo stesso disco
esterno (``P:\\lavoro-aperto``), e non su C:. Motivi:
  * la copia in chiaro non tocca mai il disco interno del PC, dove la
    sincronizzazione (OneDrive), i backup di Windows e altri programmi
    potrebbero copiarla altrove;
  * su un disco esterno meccanico la sovrascrittura prima della
    cancellazione è efficace; su un SSD interno no;
  * scollegando il disco, non resta nulla sul PC.

Tutte le funzioni restituiscono solo conteggi, mai nomi di file.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import shutil
import stat
from pathlib import Path

from .archivio import BLOCCO, Archivio

NOME_CARTELLA_LAVORO = "lavoro-aperto"
MARCATORE = ".acutis-lavoro.json"

# File temporanei creati dai programmi (Word, Esplora file): non vanno
# nell'archivio.
_IGNORATI_NOMI = {"thumbs.db", "desktop.ini", ".ds_store"}


class LavoroGiaAperto(RuntimeError):
    pass


class NessunLavoroAperto(RuntimeError):
    pass


def cartella_lavoro_predefinita(cartella_archivio: Path) -> Path:
    return Path(cartella_archivio).resolve().parent / NOME_CARTELLA_LAVORO


def _ignorato(percorso: Path) -> bool:
    nome = percorso.name.lower()
    return nome in _IGNORATI_NOMI or nome.startswith("~$") or nome.endswith((".tmp", ".~tmp"))


def _sha256_file(percorso: Path) -> str:
    h = hashlib.sha256()
    with open(percorso, "rb") as f:
        for pezzo in iter(lambda: f.read(BLOCCO), b""):
            h.update(pezzo)
    return h.hexdigest()


def _sha256_archiviato(archivio: Archivio, nome: str) -> str:
    h = hashlib.sha256()
    for pezzo in archivio.leggi_flusso(nome):
        h.update(pezzo)
    return h.hexdigest()


def _file_di_lavoro(cartella: Path) -> tuple[dict[str, Path], int]:
    file, ignorati = {}, 0
    for p in sorted(cartella.rglob("*")):
        if not p.is_file() or p.is_symlink() or p == cartella / MARCATORE:
            continue
        if _ignorato(p):
            ignorati += 1
            continue
        file[p.relative_to(cartella).as_posix()] = p
    return file, ignorati


def apri_lavoro(archivio: Archivio, cartella_lavoro: Path, avanzamento=None) -> dict:
    cartella_lavoro = Path(cartella_lavoro)
    if cartella_lavoro.exists():
        raise LavoroGiaAperto(
            "C'è già una cartella di lavoro aperta. Chiudila prima con "
            "'Acutis - Chiudi e proteggi'."
        )
    cartella_lavoro.mkdir(parents=True)
    radice = cartella_lavoro.resolve()
    (cartella_lavoro / MARCATORE).write_text(
        json.dumps({"archivio": str(archivio.cartella.resolve())}), encoding="utf-8"
    )
    voci = archivio.elenca()
    try:
        for numero, voce in enumerate(voci, 1):
            bersaglio = cartella_lavoro.joinpath(*voce["nome"].split("/"))
            if radice not in bersaglio.resolve().parents:
                raise ValueError("Percorso non valido nell'archivio.")
            bersaglio.parent.mkdir(parents=True, exist_ok=True)
            archivio.estrai(voce["nome"], bersaglio)
            if avanzamento:
                avanzamento(numero, len(voci))
    except BaseException:
        # apertura interrotta: non lasciare copie in chiaro a metà
        _distruggi(cartella_lavoro)
        raise
    return {"estratti": len(voci)}


def _distruggi(cartella: Path) -> int:
    """Sovrascrive ogni file con dati casuali e cancella la cartella.
    Restituisce quanti file non è stato possibile cancellare (aperti in un
    programma)."""
    rimasti = 0
    marcatore = cartella / MARCATORE
    for p in sorted(cartella.rglob("*"), reverse=True):
        if p == marcatore:
            continue
        try:
            if p.is_file() and not p.is_symlink():
                os.chmod(p, stat.S_IWRITE | stat.S_IREAD)
                dimensione = p.stat().st_size
                with open(p, "r+b") as f:
                    restano = dimensione
                    while restano > 0:
                        n = min(restano, BLOCCO)
                        f.write(os.urandom(n))
                        restano -= n
                    f.flush()
                    os.fsync(f.fileno())
                p.unlink()
            elif p.is_dir():
                p.rmdir()
            else:
                p.unlink()
        except OSError:
            if p.is_file():
                rimasti += 1
    if rimasti == 0:
        # il marcatore si toglie per ultimo: se qualcosa è rimasto, la
        # cartella resta riconoscibile e "chiudi" si può rilanciare
        marcatore.unlink(missing_ok=True)
        try:
            cartella.rmdir()
        except OSError:
            rimasti += sum(1 for x in cartella.rglob("*") if x.is_file())
    return rimasti


def lavoro_aperto(cartella_lavoro: Path) -> bool:
    return (Path(cartella_lavoro) / MARCATORE).exists()


def _leggi_marcatore(cartella_lavoro: Path) -> dict:
    try:
        return json.loads((Path(cartella_lavoro) / MARCATORE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _distruzione_iniziata(cartella_lavoro: Path) -> bool:
    return _leggi_marcatore(cartella_lavoro).get("distruzione") is True


def conta_cancellati(archivio: Archivio, cartella_lavoro: Path) -> int:
    """Quanti file dell'archivio non ci sono più nella cartella di lavoro."""
    if _distruzione_iniziata(cartella_lavoro):
        return 0
    lavoro, _ = _file_di_lavoro(Path(cartella_lavoro))
    return sum(1 for v in archivio.elenca() if v["nome"] not in lavoro)


def chiudi_lavoro(
    archivio: Archivio,
    cartella_lavoro: Path,
    rimuovi_cancellati: bool = False,
    avanzamento=None,
) -> dict:
    """Riporta il lavoro nell'archivio, verifica e distrugge la copia in
    chiaro. Se ``rimuovi_cancellati`` è False, i file cancellati nella
    cartella di lavoro restano nell'archivio (scelta prudente)."""
    cartella_lavoro = Path(cartella_lavoro)
    if not (cartella_lavoro / MARCATORE).exists():
        raise NessunLavoroAperto("Non c'è una cartella di lavoro aperta da chiudere.")

    archivio.elenca()  # solleva un errore se l'archivio è chiuso
    esito = {"invariati": 0, "nuovi": 0, "modificati": 0, "cancellati": 0,
             "cancellati_rimossi": 0, "ignorati": 0, "errori": 0,
             "verificati": 0, "verifica_fallita": 0, "non_cancellabili": 0,
             "cartella_distrutta": False, "ripresa": False}

    if _distruzione_iniziata(cartella_lavoro):
        # Una chiusura precedente aveva già archiviato e verificato tutto, ma
        # qualche file era bloccato da un programma. I file rimasti possono
        # essere già sovrascritti con dati casuali: NON vanno reimportati,
        # si finisce solo di distruggerli.
        esito["ripresa"] = True
        esito["non_cancellabili"] = _distruggi(cartella_lavoro)
        esito["cartella_distrutta"] = not cartella_lavoro.exists()
        return esito

    lavoro, ignorati = _file_di_lavoro(cartella_lavoro)
    esito["ignorati"] = ignorati
    nell_archivio = dict(archivio._indice["file"])

    for numero, (nome, percorso) in enumerate(lavoro.items(), 1):
        try:
            impronta = _sha256_file(percorso)
            voce = nell_archivio.get(nome)
            if voce and voce.get("sha256") and hmac.compare_digest(voce["sha256"], impronta):
                esito["invariati"] += 1
            else:
                with open(percorso, "rb") as f:
                    archivio._scrivi_flusso(nome, f, salva_indice=False)
                esito["modificati" if voce else "nuovi"] += 1
        except OSError:
            esito["errori"] += 1
        if avanzamento:
            avanzamento(numero, len(lavoro))
    archivio._salva_indice()

    cancellati = [n for n in nell_archivio if n not in lavoro]
    esito["cancellati"] = len(cancellati)
    if rimuovi_cancellati:
        for nome in cancellati:
            archivio.rimuovi(nome)
            esito["cancellati_rimossi"] += 1

    # verifica: ogni file della cartella di lavoro deve essere identico alla
    # copia archiviata, decifrata davvero
    for nome, percorso in lavoro.items():
        try:
            if hmac.compare_digest(_sha256_file(percorso), _sha256_archiviato(archivio, nome)):
                esito["verificati"] += 1
            else:
                esito["verifica_fallita"] += 1
        except Exception:
            esito["verifica_fallita"] += 1

    if esito["errori"] == 0 and esito["verifica_fallita"] == 0:
        dati = _leggi_marcatore(cartella_lavoro)
        dati["distruzione"] = True
        (cartella_lavoro / MARCATORE).write_text(json.dumps(dati), encoding="utf-8")
        esito["non_cancellabili"] = _distruggi(cartella_lavoro)
        esito["cartella_distrutta"] = not cartella_lavoro.exists()
    return esito
