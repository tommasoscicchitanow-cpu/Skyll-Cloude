"""Elenco dei progetti protetti, per l'app "Cassaforte".

Ogni progetto è un archivio cifrato interno (vedi ``archivio.py``) con la
sua cartella di lavoro. L'elenco sta in ``<radice>/progetti.json``, sul disco
esterno: contiene solo nomi dei progetti e percorsi delle cartelle, mai nomi
di file o contenuti. Scegli nomi di progetto che non rivelino nulla.

Struttura per un progetto nuovo::

    P:\\cassaforte\\<Nome>\\archivio\\        archivio cifrato
    P:\\cassaforte\\<Nome>\\lavoro-aperto\\   esiste solo mentre lavori

Un archivio già esistente (per esempio ``P:\\archivio-acutis``) si collega
all'elenco senza spostarlo né toccarlo.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from .archivio import Archivio
from .lavoro import NOME_CARTELLA_LAVORO, cartella_lavoro_predefinita, lavoro_aperto

FILE_ELENCO = "progetti.json"
CHIAVE_HELLO = "protezione-acutis-archivio"
_NOME_VALIDO = re.compile(r"^[\w][\w .\-]{0,59}$", re.UNICODE)


def radice_predefinita() -> Path:
    """P:\\cassaforte su Windows; si cambia con "radice_cassaforte" nel file
    configurazione.locale.json o con la variabile CASSAFORTE_RADICE."""
    if os.environ.get("CASSAFORTE_RADICE"):
        return Path(os.environ["CASSAFORTE_RADICE"])
    from .attivazione import CONFIGURAZIONE_LOCALE

    try:
        dati = json.loads(CONFIGURAZIONE_LOCALE.read_text(encoding="utf-8"))
        if dati.get("radice_cassaforte"):
            return Path(dati["radice_cassaforte"])
    except (FileNotFoundError, ValueError):
        pass
    return Path("P:/cassaforte") if os.name == "nt" else Path.home() / "cassaforte"


class ErroreProgetto(ValueError):
    pass


@dataclass
class Progetto:
    nome: str
    archivio: str
    lavoro: str
    fattore: str = "hello"  # "hello" (Windows Hello) oppure "passkey" (telefono)
    chiave_hello: str = CHIAVE_HELLO

    @property
    def cartella_archivio(self) -> Path:
        return Path(self.archivio)

    @property
    def cartella_lavoro(self) -> Path:
        return Path(self.lavoro)

    def stato(self) -> str:
        """"aperto", "chiuso" o "assente" (disco non collegato)."""
        if not (self.cartella_archivio / "archivio.json").exists():
            return "assente"
        return "aperto" if lavoro_aperto(self.cartella_lavoro) else "chiuso"


def _controlla_nome(nome: str) -> str:
    nome = nome.strip()
    if not _NOME_VALIDO.match(nome) or nome in (".", ".."):
        raise ErroreProgetto(
            "Nome non valido: usa lettere, numeri, spazi, punto, trattino o "
            "trattino basso (massimo 60 caratteri)."
        )
    return nome


class Registro:
    def __init__(self, radice: Path, progetti: list[Progetto]):
        self.radice = Path(radice)
        self.progetti = progetti

    @property
    def percorso(self) -> Path:
        return self.radice / FILE_ELENCO

    @classmethod
    def carica(cls, radice: Path | None = None) -> "Registro":
        radice = Path(radice) if radice else radice_predefinita()
        try:
            dati = json.loads((radice / FILE_ELENCO).read_text(encoding="utf-8"))
        except FileNotFoundError:
            return cls(radice, [])
        campi = Progetto.__dataclass_fields__
        return cls(radice, [Progetto(**{k: v for k, v in p.items() if k in campi})
                            for p in dati.get("progetti", [])])

    def salva(self) -> None:
        self.radice.mkdir(parents=True, exist_ok=True)
        testo = json.dumps({"versione": 1, "progetti": [asdict(p) for p in self.progetti]},
                           indent=2, ensure_ascii=False)
        fd, provvisorio = tempfile.mkstemp(dir=self.radice, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(testo)
        os.replace(provvisorio, self.percorso)

    def trova(self, nome: str) -> Progetto:
        for p in self.progetti:
            if p.nome.lower() == nome.strip().lower():
                return p
        raise ErroreProgetto("Progetto non trovato.")

    def _aggiungi(self, progetto: Progetto) -> Progetto:
        if any(p.nome.lower() == progetto.nome.lower() for p in self.progetti):
            raise ErroreProgetto("Esiste già un progetto con questo nome.")
        self.progetti.append(progetto)
        self.salva()
        return progetto

    def collega(self, nome: str, cartella_archivio: Path, cartella_lavoro: Path | None = None,
                fattore: str = "hello", chiave_hello: str = CHIAVE_HELLO) -> Progetto:
        """Aggiunge all'elenco un archivio che esiste già, senza toccarlo."""
        nome = _controlla_nome(nome)
        cartella_archivio = Path(cartella_archivio)
        if not (cartella_archivio / "archivio.json").exists():
            raise ErroreProgetto("In quella cartella non c'è un archivio cifrato.")
        lavoro = Path(cartella_lavoro) if cartella_lavoro else cartella_lavoro_predefinita(cartella_archivio)
        return self._aggiungi(Progetto(nome, str(cartella_archivio), str(lavoro), fattore, chiave_hello))

    def nuovo(self, nome: str, frase: str, biometria, fattore: str = "hello",
              chiave_hello: str = CHIAVE_HELLO, **opzioni_archivio) -> Progetto:
        """Crea un archivio vuoto in <radice>/<nome>/archivio e lo registra."""
        nome = _controlla_nome(nome)
        if any(p.nome.lower() == nome.lower() for p in self.progetti):
            raise ErroreProgetto("Esiste già un progetto con questo nome.")
        base = self.radice / nome
        if base.exists():
            raise ErroreProgetto("Esiste già una cartella con questo nome.")
        Archivio.crea(base / "archivio", frase, biometria, **opzioni_archivio).chiudi()
        return self._aggiungi(Progetto(nome, str(base / "archivio"),
                                       str(base / NOME_CARTELLA_LAVORO), fattore, chiave_hello))

    def aperti(self) -> list[Progetto]:
        return [p for p in self.progetti if p.stato() == "aperto"]
