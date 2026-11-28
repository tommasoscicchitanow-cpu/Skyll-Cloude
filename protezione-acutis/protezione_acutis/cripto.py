"""Cifratura a due fattori.

Schema:
  1. frase segreta  -> Argon2id (sale casuale)        -> chiave_frase (32 byte)
  2. impronta       -> segreto custodito dal dispositivo -> chiave_bio (32 byte)
  3. HKDF-SHA256(chiave_frase || chiave_bio)          -> chiave_file (32 byte)
  4. AES-256-GCM con nonce casuale; l'intestazione è dato autenticato (AAD),
     quindi qualunque manomissione dell'intestazione fa fallire la decifratura.

Servono ENTRAMBI i fattori: senza impronta, o con una frase sbagliata, la
chiave risultante è diversa e AES-GCM rifiuta il file.
"""

from __future__ import annotations

import base64
import json
import os
import struct
import unicodedata
from dataclasses import asdict, dataclass

from argon2.low_level import Type, hash_secret_raw
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from .biometria import FattoreBiometrico

MAGIA = b"PACUTIS1"
VERSIONE = 1
INFO_HKDF = b"protezione-acutis/v1/chiave-file"
LUNGHEZZA_MINIMA_FRASE = 20


class ErroreDecifratura(Exception):
    """Decifratura fallita. Il messaggio non dice volutamente quale fattore
    era sbagliato, per non aiutare chi tenta di indovinare."""


class ErroreFormato(Exception):
    """Il file non è nel formato atteso o è stato troncato."""


class FraseDebole(ValueError):
    """La frase segreta è troppo corta."""


@dataclass(frozen=True)
class ParametriArgon2:
    """Costo di Argon2id. I valori predefiniti seguono le raccomandazioni
    OWASP/RFC 9106 per uso interattivo (3 passaggi, 64 MiB, 4 thread)."""

    tempo: int = 3
    memoria_kib: int = 64 * 1024
    parallelismo: int = 4

    @classmethod
    def per_test(cls) -> "ParametriArgon2":
        """Parametri leggeri, SOLO per velocizzare le prove automatiche."""
        return cls(tempo=1, memoria_kib=8 * 1024, parallelismo=1)


MINIMI_PRODUZIONE = ParametriArgon2()


def _normalizza_frase(frase: str) -> bytes:
    # NFC: la stessa frase digitata su tastiere diverse (es. "è" composta o
    # precomposta) produce gli stessi byte.
    return unicodedata.normalize("NFC", frase).encode("utf-8")


def _deriva_chiave(frase: str, sale: bytes, parametri: ParametriArgon2, chiave_bio: bytes) -> bytes:
    chiave_frase = hash_secret_raw(
        secret=_normalizza_frase(frase),
        salt=sale,
        time_cost=parametri.tempo,
        memory_cost=parametri.memoria_kib,
        parallelism=parametri.parallelismo,
        hash_len=32,
        type=Type.ID,
    )
    if len(chiave_bio) != 32:
        raise ErroreDecifratura("Segreto biometrico di lunghezza inattesa.")
    return HKDF(
        algorithm=hashes.SHA256(), length=32, salt=sale, info=INFO_HKDF
    ).derive(chiave_frase + chiave_bio)


def _b64(dati: bytes) -> str:
    return base64.b64encode(dati).decode("ascii")


def cifra(
    dati: bytes,
    frase: str,
    biometria: FattoreBiometrico,
    parametri: ParametriArgon2 = MINIMI_PRODUZIONE,
    identificativo_bio: str | None = None,
) -> bytes:
    """Cifra ``dati``. Chiede l'impronta tramite ``biometria``.

    Se ``identificativo_bio`` è None viene registrato un nuovo segreto
    biometrico; altrimenti si riusa quello indicato (stessa impronta per più
    file).
    """
    if len(frase) < LUNGHEZZA_MINIMA_FRASE:
        raise FraseDebole(
            f"La frase segreta deve avere almeno {LUNGHEZZA_MINIMA_FRASE} caratteri."
        )
    if identificativo_bio is None:
        identificativo_bio = biometria.registra()
    chiave_bio = biometria.sblocca(identificativo_bio)

    sale = os.urandom(16)
    nonce = os.urandom(12)
    intestazione = json.dumps(
        {
            "versione": VERSIONE,
            "argon2": asdict(parametri),
            "sale": _b64(sale),
            "nonce": _b64(nonce),
            "biometria": identificativo_bio,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    aad = MAGIA + struct.pack(">I", len(intestazione)) + intestazione

    chiave = _deriva_chiave(frase, sale, parametri, chiave_bio)
    cifrato = AESGCM(chiave).encrypt(nonce, dati, aad)
    return aad + cifrato


def leggi_intestazione(contenitore: bytes) -> tuple[dict, bytes, bytes]:
    """Restituisce (intestazione, aad, cifrato) senza decifrare nulla."""
    if not contenitore.startswith(MAGIA) or len(contenitore) < len(MAGIA) + 4:
        raise ErroreFormato("Non è un file cifrato da questo strumento.")
    (lunghezza,) = struct.unpack(">I", contenitore[len(MAGIA) : len(MAGIA) + 4])
    inizio = len(MAGIA) + 4
    if lunghezza > 64 * 1024 or len(contenitore) < inizio + lunghezza + 16:
        raise ErroreFormato("File troncato o intestazione non valida.")
    grezza = contenitore[inizio : inizio + lunghezza]
    try:
        intestazione = json.loads(grezza)
    except ValueError:
        raise ErroreFormato("Intestazione illeggibile.") from None
    if intestazione.get("versione") != VERSIONE:
        raise ErroreFormato("Versione del formato non supportata.")
    return intestazione, contenitore[: inizio + lunghezza], contenitore[inizio + lunghezza :]


def decifra(
    contenitore: bytes,
    frase: str,
    biometria: FattoreBiometrico,
    parametri_minimi: ParametriArgon2 = MINIMI_PRODUZIONE,
) -> bytes:
    """Decifra. Solleva BiometriaNegata se l'impronta non viene accettata,
    ErroreDecifratura se la frase è sbagliata o il file è stato alterato."""
    intestazione, aad, cifrato = leggi_intestazione(contenitore)
    try:
        parametri = ParametriArgon2(**intestazione["argon2"])
        sale = base64.b64decode(intestazione["sale"], validate=True)
        nonce = base64.b64decode(intestazione["nonce"], validate=True)
        identificativo_bio = str(intestazione["biometria"])
    except (KeyError, TypeError, ValueError):
        raise ErroreFormato("Intestazione incompleta.") from None

    # Impedisce che un file "costruito apposta" con parametri deboli renda
    # facile indovinare la frase.
    if (
        parametri.tempo < parametri_minimi.tempo
        or parametri.memoria_kib < parametri_minimi.memoria_kib
        or parametri.parallelismo < 1
    ):
        raise ErroreFormato("Parametri di derivazione troppo deboli.")

    chiave_bio = biometria.sblocca(identificativo_bio)
    chiave = _deriva_chiave(frase, sale, parametri, chiave_bio)
    try:
        return AESGCM(chiave).decrypt(nonce, cifrato, aad)
    except InvalidTag:
        raise ErroreDecifratura(
            "Decifratura non riuscita: frase o impronta errata, oppure file alterato."
        ) from None
