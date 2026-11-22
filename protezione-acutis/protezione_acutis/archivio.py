"""Archivio cifrato interno: sostituisce VeraCrypt, senza programmi di terzi.

Un archivio è una cartella (per esempio sulla partizione del disco E:) che
dall'esterno contiene solo file con nomi casuali e contenuto illeggibile:

    archivio.json        intestazione pubblica: parametri, sale, chiave avvolta
    indice.bin           elenco dei file (nomi, dimensioni, date), cifrato
    dati/<casuale>.bin   contenuto di ogni file, cifrato a blocchi

Chiavi:
  * frase segreta + segreto dell'impronta -> chiave di avvolgimento (Argon2id
    + HKDF, la stessa derivazione di cripto.py);
  * la chiave di avvolgimento cifra una "chiave principale" casuale di 32 byte.
    Così si può cambiare la frase o l'impronta senza ricifrare tutto;
  * la chiave principale cifra indice e contenuti con AES-256-GCM.

Algoritmi: soltanto standard pubblici e verificati da anni (AES-256-GCM,
Argon2id, HKDF-SHA256). Il codice dell'archivio è nostro; la matematica no,
volutamente: un algoritmo "inventato" non è mai stato attaccato da esperti e
sarebbe molto più debole.

Ogni blocco da 1 MiB ha un nonce casuale e come dato autenticato l'id del
file, il numero del blocco e se è l'ultimo: blocchi scambiati, tolti o
aggiunti vengono rilevati.
"""

from __future__ import annotations

import base64
import json
import os
import secrets
import struct
import tempfile
import time
from dataclasses import asdict
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .attivazione import SistemaDisattivato, sistema_attivo
from .biometria import FattoreBiometrico
from .cripto import (
    LUNGHEZZA_MINIMA_FRASE,
    MINIMI_PRODUZIONE,
    ErroreDecifratura,
    ErroreFormato,
    FraseDebole,
    ParametriArgon2,
    _deriva_chiave,
)

VERSIONE = 1
BLOCCO = 1024 * 1024
MAGIA_DATI = b"PAARC1"
NOME_INTESTAZIONE = "archivio.json"
NOME_INDICE = "indice.bin"
CARTELLA_DATI = "dati"


def _b64(dati: bytes) -> str:
    return base64.b64encode(dati).decode("ascii")


def _da_b64(testo: str) -> bytes:
    return base64.b64decode(testo, validate=True)


def _scrivi_atomico(percorso: Path, dati: bytes) -> None:
    temporaneo = percorso.with_name(percorso.name + ".parziale")
    with open(temporaneo, "wb") as f:
        f.write(dati)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporaneo, percorso)


def _controlla_cartella(cartella: Path, attivo: bool) -> None:
    if attivo:
        return
    radice = Path(tempfile.gettempdir()).resolve()
    try:
        Path(cartella).resolve().relative_to(radice)
    except ValueError:
        raise SistemaDisattivato(
            f"Sistema disattivato: in modalità prova l'archivio può stare solo "
            f"dentro {radice}. Cartella rifiutata: {cartella}"
        ) from None


def _aad_intestazione(intestazione: dict) -> bytes:
    pubblica = {k: v for k, v in intestazione.items() if k != "chiave_avvolta"}
    return json.dumps(pubblica, sort_keys=True, separators=(",", ":")).encode()


class Archivio:
    """Archivio aperto. Si ottiene con ``Archivio.crea`` o ``Archivio.apri``."""

    def __init__(self, cartella: Path, intestazione: dict, chiave: bytes, indice: dict):
        self.cartella = Path(cartella)
        self._intestazione = intestazione
        self._chiave: bytes | None = chiave
        self._indice = indice

    # -- creazione e apertura -------------------------------------------
    @classmethod
    def crea(
        cls,
        cartella: Path,
        frase: str,
        biometria: FattoreBiometrico,
        parametri: ParametriArgon2 = MINIMI_PRODUZIONE,
        attivo: bool | None = None,
    ) -> "Archivio":
        attivo = sistema_attivo() if attivo is None else attivo
        cartella = Path(cartella)
        _controlla_cartella(cartella, attivo)
        if attivo and biometria.simulato:
            raise SistemaDisattivato("Sistema attivo: biometria simulata non ammessa.")
        if len(frase) < LUNGHEZZA_MINIMA_FRASE:
            raise FraseDebole(
                f"La frase segreta deve avere almeno {LUNGHEZZA_MINIMA_FRASE} caratteri."
            )
        if (cartella / NOME_INTESTAZIONE).exists():
            raise FileExistsError(f"In {cartella} esiste già un archivio.")
        (cartella / CARTELLA_DATI).mkdir(parents=True, exist_ok=True)

        identificativo = biometria.registra()
        chiave_bio = biometria.sblocca(identificativo)
        sale = os.urandom(16)
        chiave_principale = os.urandom(32)
        intestazione = {
            "versione": VERSIONE,
            "argon2": asdict(parametri),
            "sale": _b64(sale),
            "biometria": identificativo,
        }
        avvolgente = _deriva_chiave(frase, sale, parametri, chiave_bio)
        nonce = os.urandom(12)
        avvolta = AESGCM(avvolgente).encrypt(nonce, chiave_principale, _aad_intestazione(intestazione))
        intestazione["chiave_avvolta"] = _b64(nonce + avvolta)
        _scrivi_atomico(
            cartella / NOME_INTESTAZIONE,
            json.dumps(intestazione, indent=2, sort_keys=True).encode(),
        )
        archivio = cls(cartella, intestazione, chiave_principale, {"file": {}})
        archivio._salva_indice()
        return archivio

    @classmethod
    def apri(
        cls,
        cartella: Path,
        frase: str,
        biometria: FattoreBiometrico,
        parametri_minimi: ParametriArgon2 = MINIMI_PRODUZIONE,
        attivo: bool | None = None,
    ) -> "Archivio":
        attivo = sistema_attivo() if attivo is None else attivo
        cartella = Path(cartella)
        _controlla_cartella(cartella, attivo)
        try:
            intestazione = json.loads((cartella / NOME_INTESTAZIONE).read_text("utf-8"))
            parametri = ParametriArgon2(**intestazione["argon2"])
            sale = _da_b64(intestazione["sale"])
            grezza = _da_b64(intestazione["chiave_avvolta"])
            identificativo = str(intestazione["biometria"])
        except FileNotFoundError:
            raise ErroreFormato(f"In {cartella} non c'è un archivio.") from None
        except (KeyError, TypeError, ValueError):
            raise ErroreFormato("Intestazione dell'archivio non valida.") from None
        if intestazione.get("versione") != VERSIONE:
            raise ErroreFormato("Versione dell'archivio non supportata.")
        if (
            parametri.tempo < parametri_minimi.tempo
            or parametri.memoria_kib < parametri_minimi.memoria_kib
        ):
            raise ErroreFormato("Parametri di derivazione troppo deboli.")

        chiave_bio = biometria.sblocca(identificativo)
        avvolgente = _deriva_chiave(frase, sale, parametri, chiave_bio)
        try:
            chiave = AESGCM(avvolgente).decrypt(grezza[:12], grezza[12:], _aad_intestazione(intestazione))
        except InvalidTag:
            raise ErroreDecifratura(
                "Archivio non aperto: frase o impronta errata, oppure intestazione alterata."
            ) from None
        archivio = cls(cartella, intestazione, chiave, {})
        archivio._indice = archivio._leggi_indice()
        return archivio

    # -- uso -------------------------------------------------------------
    def _aes(self) -> AESGCM:
        if self._chiave is None:
            raise RuntimeError("Archivio chiuso.")
        return AESGCM(self._chiave)

    def _salva_indice(self) -> None:
        nonce = os.urandom(12)
        chiaro = json.dumps(self._indice, sort_keys=True).encode()
        cifrato = self._aes().encrypt(nonce, chiaro, b"indice")
        _scrivi_atomico(self.cartella / NOME_INDICE, nonce + cifrato)

    def _leggi_indice(self) -> dict:
        grezzo = (self.cartella / NOME_INDICE).read_bytes()
        try:
            return json.loads(self._aes().decrypt(grezzo[:12], grezzo[12:], b"indice"))
        except InvalidTag:
            raise ErroreDecifratura("Indice dell'archivio alterato.") from None

    def elenca(self) -> list[dict]:
        self._aes()
        return [
            {"nome": nome, "dimensione": voce["dimensione"], "aggiunto": voce["aggiunto"]}
            for nome, voce in sorted(self._indice["file"].items())
        ]

    def aggiungi_dati(self, nome: str, dati: bytes) -> None:
        aes = self._aes()
        if not nome or "\x00" in nome:
            raise ValueError("Nome non valido.")
        vecchio = self._indice["file"].get(nome)
        id_file = secrets.token_hex(16)
        pezzi = [dati[i : i + BLOCCO] for i in range(0, len(dati), BLOCCO)] or [b""]
        uscita = bytearray(MAGIA_DATI)
        for numero, pezzo in enumerate(pezzi):
            ultimo = numero == len(pezzi) - 1
            aad = id_file.encode() + struct.pack(">IB", numero, ultimo)
            nonce = os.urandom(12)
            cifrato = aes.encrypt(nonce, pezzo, aad)
            uscita += struct.pack(">I", len(cifrato)) + nonce + cifrato
        _scrivi_atomico(self.cartella / CARTELLA_DATI / f"{id_file}.bin", bytes(uscita))
        self._indice["file"][nome] = {
            "id": id_file,
            "dimensione": len(dati),
            "aggiunto": int(time.time()),
        }
        self._salva_indice()
        if vecchio:
            (self.cartella / CARTELLA_DATI / f"{vecchio['id']}.bin").unlink(missing_ok=True)

    def aggiungi_file(self, origine: Path, nome: str | None = None) -> str:
        origine = Path(origine)
        nome = nome or origine.name
        self.aggiungi_dati(nome, origine.read_bytes())
        return nome

    def leggi(self, nome: str) -> bytes:
        aes = self._aes()
        try:
            voce = self._indice["file"][nome]
        except KeyError:
            raise FileNotFoundError(f"Nell'archivio non c'è '{nome}'.") from None
        grezzo = (self.cartella / CARTELLA_DATI / f"{voce['id']}.bin").read_bytes()
        if not grezzo.startswith(MAGIA_DATI):
            raise ErroreFormato("Blocco dati non valido.")
        posizione, numero, risultato, finito = len(MAGIA_DATI), 0, bytearray(), False
        while posizione < len(grezzo):
            if finito:
                raise ErroreDecifratura("Dati aggiunti in coda al file: alterazione.")
            (lunghezza,) = struct.unpack(">I", grezzo[posizione : posizione + 4])
            nonce = grezzo[posizione + 4 : posizione + 16]
            cifrato = grezzo[posizione + 16 : posizione + 16 + lunghezza]
            posizione += 16 + lunghezza
            ultimo = posizione >= len(grezzo)
            aad = voce["id"].encode() + struct.pack(">IB", numero, ultimo)
            try:
                risultato += aes.decrypt(nonce, cifrato, aad)
            except InvalidTag:
                raise ErroreDecifratura(f"'{nome}' è stato alterato o troncato.") from None
            finito = ultimo
            numero += 1
        if not finito or len(risultato) != voce["dimensione"]:
            raise ErroreDecifratura(f"'{nome}' è incompleto.")
        return bytes(risultato)

    def estrai(self, nome: str, destinazione: Path) -> Path:
        destinazione = Path(destinazione)
        if destinazione.is_dir():
            destinazione = destinazione / Path(nome).name
        _scrivi_atomico(destinazione, self.leggi(nome))
        return destinazione

    def rimuovi(self, nome: str) -> None:
        self._aes()
        voce = self._indice["file"].pop(nome)
        self._salva_indice()
        (self.cartella / CARTELLA_DATI / f"{voce['id']}.bin").unlink(missing_ok=True)

    def cambia_frase(self, nuova_frase: str, biometria: FattoreBiometrico) -> None:
        """Riavvolge la chiave principale con una nuova frase (e la stessa
        impronta). I contenuti non vengono ricifrati."""
        if len(nuova_frase) < LUNGHEZZA_MINIMA_FRASE:
            raise FraseDebole("Frase troppo corta.")
        intestazione = dict(self._intestazione)
        intestazione.pop("chiave_avvolta")
        sale = os.urandom(16)
        intestazione["sale"] = _b64(sale)
        parametri = ParametriArgon2(**intestazione["argon2"])
        chiave_bio = biometria.sblocca(intestazione["biometria"])
        avvolgente = _deriva_chiave(nuova_frase, sale, parametri, chiave_bio)
        nonce = os.urandom(12)
        avvolta = AESGCM(avvolgente).encrypt(nonce, self._chiave, _aad_intestazione(intestazione))
        intestazione["chiave_avvolta"] = _b64(nonce + avvolta)
        _scrivi_atomico(
            self.cartella / NOME_INTESTAZIONE,
            json.dumps(intestazione, indent=2, sort_keys=True).encode(),
        )
        self._intestazione = intestazione

    def chiudi(self) -> None:
        self._chiave = None
        self._indice = {}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.chiudi()
