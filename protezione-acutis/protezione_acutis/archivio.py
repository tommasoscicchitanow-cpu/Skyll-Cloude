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
import hashlib
import hmac
import io
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
    pubblica = {k: v for k, v in intestazione.items() if k not in ("chiave_avvolta", "recupero")}
    return json.dumps(pubblica, sort_keys=True, separators=(",", ":")).encode()


_ALFABETO = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"


def formatta_chiave_recupero(recupero: bytes) -> str:
    """32 byte + 3 byte di controllo, in base32 a gruppi di 4 caratteri."""
    testo = base64.b32encode(recupero + hashlib.sha256(recupero).digest()[:3]).decode().rstrip("=")
    return "-".join(testo[i : i + 4] for i in range(0, len(testo), 4))


def leggi_chiave_recupero(testo: str) -> bytes:
    """Accetta spazi, trattini e minuscole; corregge 0/1/8 letti al posto di O/I/B."""
    pulito = "".join(c for c in testo.upper() if c.isalnum()).translate(str.maketrans("018", "OIB"))
    if any(c not in _ALFABETO for c in pulito) or len(pulito) != 56:
        raise ErroreDecifratura("Chiave di recupero non valida: controlla di averla copiata tutta.")
    grezza = base64.b32decode(pulito + "=" * (-len(pulito) % 8))
    recupero, controllo = grezza[:32], grezza[32:]
    if not hmac.compare_digest(hashlib.sha256(recupero).digest()[:3], controllo):
        raise ErroreDecifratura("Chiave di recupero non valida: c'è un errore di trascrizione.")
    return recupero


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

    # -- scrittura a flusso: anche file di molti GB senza riempire la RAM --
    def _scrivi_flusso(self, nome: str, sorgente, salva_indice: bool = True) -> str:
        """``sorgente`` è un file aperto in lettura binaria. Restituisce lo
        SHA-256 del contenuto in chiaro."""
        aes = self._aes()
        if not nome or "\x00" in nome:
            raise ValueError("Nome non valido.")
        vecchio = self._indice["file"].get(nome)
        id_file = secrets.token_hex(16)
        destinazione = self.cartella / CARTELLA_DATI / f"{id_file}.bin"
        temporaneo = destinazione.with_name(destinazione.name + ".parziale")
        impronta = hashlib.sha256()
        dimensione = 0
        try:
            with open(temporaneo, "wb") as uscita:
                uscita.write(MAGIA_DATI)
                pezzo = sorgente.read(BLOCCO)
                numero = 0
                while True:
                    successivo = sorgente.read(BLOCCO) if pezzo else b""
                    ultimo = not successivo
                    impronta.update(pezzo)
                    dimensione += len(pezzo)
                    aad = id_file.encode() + struct.pack(">IB", numero, ultimo)
                    nonce = os.urandom(12)
                    cifrato = aes.encrypt(nonce, pezzo, aad)
                    uscita.write(struct.pack(">I", len(cifrato)) + nonce + cifrato)
                    if ultimo:
                        break
                    pezzo, numero = successivo, numero + 1
                uscita.flush()
                os.fsync(uscita.fileno())
            os.replace(temporaneo, destinazione)
        except BaseException:
            temporaneo.unlink(missing_ok=True)
            raise
        self._indice["file"][nome] = {
            "id": id_file,
            "dimensione": dimensione,
            "aggiunto": int(time.time()),
            "sha256": impronta.hexdigest(),
        }
        if salva_indice:
            self._salva_indice()
        if vecchio:
            (self.cartella / CARTELLA_DATI / f"{vecchio['id']}.bin").unlink(missing_ok=True)
        return impronta.hexdigest()

    def aggiungi_dati(self, nome: str, dati: bytes) -> None:
        self._scrivi_flusso(nome, io.BytesIO(dati))

    def aggiungi_file(self, origine: Path, nome: str | None = None) -> str:
        origine = Path(origine)
        nome = nome or origine.name
        with open(origine, "rb") as f:
            self._scrivi_flusso(nome, f)
        return nome

    def importa_cartella(self, sorgente: Path, prefisso: str = "", avanzamento=None) -> dict:
        """Copia ricorsivamente tutti i file di ``sorgente`` nell'archivio,
        con i percorsi relativi (separatore "/"). Gli originali NON vengono
        toccati. Restituisce solo conteggi, mai nomi di file."""
        self._aes()
        sorgente = Path(sorgente)
        if not sorgente.is_dir():
            raise FileNotFoundError("La cartella da importare non esiste.")
        file = [p for p in sorted(sorgente.rglob("*")) if p.is_file() and not p.is_symlink()]
        esito = {"totale": len(file), "importati": 0, "gia_presenti": 0, "errori": 0, "byte": 0}
        for numero, percorso in enumerate(file, 1):
            nome = prefisso + percorso.relative_to(sorgente).as_posix()
            presente = self._indice["file"].get(nome)
            try:
                if presente and presente["dimensione"] == percorso.stat().st_size:
                    # ripresa dopo un'interruzione: già copiato
                    esito["gia_presenti"] += 1
                    if avanzamento:
                        avanzamento(numero, len(file))
                    continue
                with open(percorso, "rb") as f:
                    self._scrivi_flusso(nome, f, salva_indice=False)
                esito["importati"] += 1
                esito["byte"] += self._indice["file"][nome]["dimensione"]
            except OSError:
                esito["errori"] += 1
            if numero % 25 == 0:
                self._salva_indice()
            if avanzamento:
                avanzamento(numero, len(file))
        self._salva_indice()
        return esito

    def verifica_cartella(self, sorgente: Path, prefisso: str = "", avanzamento=None) -> dict:
        """Confronta i file di ``sorgente`` con l'archivio decifrandoli
        davvero (SHA-256 del contenuto). Restituisce solo conteggi."""
        self._aes()
        sorgente = Path(sorgente)
        file = [p for p in sorted(sorgente.rglob("*")) if p.is_file() and not p.is_symlink()]
        nomi_sorgente = set()
        esito = {"controllati": len(file), "identici": 0, "diversi": 0, "mancanti": 0,
                 "illeggibili": 0, "solo_in_archivio": 0}
        for numero, percorso in enumerate(file, 1):
            nome = prefisso + percorso.relative_to(sorgente).as_posix()
            nomi_sorgente.add(nome)
            if nome not in self._indice["file"]:
                esito["mancanti"] += 1
            else:
                try:
                    originale = hashlib.sha256()
                    with open(percorso, "rb") as f:
                        for pezzo in iter(lambda: f.read(BLOCCO), b""):
                            originale.update(pezzo)
                    archiviato = hashlib.sha256()
                    for pezzo in self.leggi_flusso(nome):
                        archiviato.update(pezzo)
                    uguale = hmac.compare_digest(originale.digest(), archiviato.digest())
                    esito["identici" if uguale else "diversi"] += 1
                except (OSError, ErroreDecifratura, ErroreFormato):
                    esito["illeggibili"] += 1
            if avanzamento:
                avanzamento(numero, len(file))
        esito["solo_in_archivio"] = sum(
            1 for n in self._indice["file"] if n.startswith(prefisso) and n not in nomi_sorgente
        )
        return esito

    def verifica_integrita(self, avanzamento=None) -> dict:
        """Decifra tutto l'archivio e controlla ogni file con lo SHA-256
        registrato all'importazione. Utile dopo aver scollegato l'originale."""
        self._aes()
        esito = {"controllati": 0, "integri": 0, "danneggiati": 0}
        voci = list(self._indice["file"].items())
        for numero, (nome, voce) in enumerate(voci, 1):
            esito["controllati"] += 1
            try:
                archiviato = hashlib.sha256()
                for pezzo in self.leggi_flusso(nome):
                    archiviato.update(pezzo)
                atteso = voce.get("sha256")
                ok = atteso is None or hmac.compare_digest(archiviato.hexdigest(), atteso)
                esito["integri" if ok else "danneggiati"] += 1
            except (OSError, ErroreDecifratura, ErroreFormato):
                esito["danneggiati"] += 1
            if avanzamento:
                avanzamento(numero, len(voci))
        return esito

    # -- lettura a flusso ------------------------------------------------
    def leggi_flusso(self, nome: str):
        aes = self._aes()
        try:
            voce = self._indice["file"][nome]
        except KeyError:
            raise FileNotFoundError(f"Nell'archivio non c'è '{nome}'.") from None
        with open(self.cartella / CARTELLA_DATI / f"{voce['id']}.bin", "rb") as f:
            if f.read(len(MAGIA_DATI)) != MAGIA_DATI:
                raise ErroreFormato("Blocco dati non valido.")
            numero, dimensione, finito = 0, 0, False
            intestazione = f.read(16)
            while intestazione:
                if finito:
                    raise ErroreDecifratura(f"'{nome}': dati aggiunti in coda, alterazione.")
                if len(intestazione) < 16:
                    raise ErroreDecifratura(f"'{nome}' è stato troncato.")
                (lunghezza,) = struct.unpack(">I", intestazione[:4])
                if lunghezza > BLOCCO + 16:
                    raise ErroreDecifratura(f"'{nome}' è stato alterato.")
                nonce = intestazione[4:16]
                cifrato = f.read(lunghezza)
                intestazione = f.read(16)
                ultimo = not intestazione
                aad = voce["id"].encode() + struct.pack(">IB", numero, ultimo)
                try:
                    chiaro = aes.decrypt(nonce, cifrato, aad)
                except InvalidTag:
                    raise ErroreDecifratura(f"'{nome}' è stato alterato o troncato.") from None
                dimensione += len(chiaro)
                yield chiaro
                finito = ultimo
                numero += 1
            if not finito or dimensione != voce["dimensione"]:
                raise ErroreDecifratura(f"'{nome}' è incompleto.")

    def leggi(self, nome: str) -> bytes:
        return b"".join(self.leggi_flusso(nome))

    def estrai(self, nome: str, destinazione: Path) -> Path:
        destinazione = Path(destinazione)
        if destinazione.is_dir():
            destinazione = destinazione / Path(nome).name
        temporaneo = destinazione.with_name(destinazione.name + ".parziale")
        try:
            with open(temporaneo, "wb") as f:
                for pezzo in self.leggi_flusso(nome):
                    f.write(pezzo)
            os.replace(temporaneo, destinazione)
        except BaseException:
            temporaneo.unlink(missing_ok=True)
            raise
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
        # la vecchia chiave di recupero era legata alla vecchia frase: si
        # elimina, e ne va creata una nuova
        intestazione.pop("recupero", None)
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

    # -- chiave di recupero ----------------------------------------------
    def crea_chiave_recupero(self, frase: str) -> str:
        """Crea una chiave di recupero da scrivere su carta. Insieme alla
        frase sostituisce l'impronta (PC rotto, Windows Hello reinstallato).
        La frase resta comunque obbligatoria. Sostituisce eventuali chiavi
        di recupero precedenti. Restituisce il testo da trascrivere: non
        viene salvato da nessuna parte."""
        aes = self._aes()
        del aes
        recupero = os.urandom(32)
        sale = os.urandom(16)
        parametri = ParametriArgon2(**self._intestazione["argon2"])
        avvolgente = _deriva_chiave(frase, sale, parametri, recupero)
        nonce = os.urandom(12)
        avvolta = AESGCM(avvolgente).encrypt(nonce, self._chiave, b"recupero" + sale)
        intestazione = dict(self._intestazione)
        intestazione["recupero"] = {"sale": _b64(sale), "avvolta": _b64(nonce + avvolta)}
        _scrivi_atomico(
            self.cartella / NOME_INTESTAZIONE,
            json.dumps(intestazione, indent=2, sort_keys=True).encode(),
        )
        self._intestazione = intestazione
        return formatta_chiave_recupero(recupero)

    @classmethod
    def apri_con_recupero(
        cls,
        cartella: Path,
        frase: str,
        chiave_recupero: str,
        parametri_minimi: ParametriArgon2 = MINIMI_PRODUZIONE,
        attivo: bool | None = None,
    ) -> "Archivio":
        attivo = sistema_attivo() if attivo is None else attivo
        cartella = Path(cartella)
        _controlla_cartella(cartella, attivo)
        recupero = leggi_chiave_recupero(chiave_recupero)
        try:
            intestazione = json.loads((cartella / NOME_INTESTAZIONE).read_text("utf-8"))
            parametri = ParametriArgon2(**intestazione["argon2"])
            sale = _da_b64(intestazione["recupero"]["sale"])
            grezza = _da_b64(intestazione["recupero"]["avvolta"])
        except FileNotFoundError:
            raise ErroreFormato(f"In {cartella} non c'è un archivio.") from None
        except (KeyError, TypeError, ValueError):
            raise ErroreFormato("Questo archivio non ha una chiave di recupero.") from None
        if parametri.tempo < parametri_minimi.tempo or parametri.memoria_kib < parametri_minimi.memoria_kib:
            raise ErroreFormato("Parametri di derivazione troppo deboli.")
        avvolgente = _deriva_chiave(frase, sale, parametri, recupero)
        try:
            chiave = AESGCM(avvolgente).decrypt(grezza[:12], grezza[12:], b"recupero" + sale)
        except InvalidTag:
            raise ErroreDecifratura("Frase o chiave di recupero errata.") from None
        archivio = cls(cartella, intestazione, chiave, {})
        archivio._indice = archivio._leggi_indice()
        return archivio

    def riassocia_impronta(self, frase: str, biometria: FattoreBiometrico) -> None:
        """Collega l'archivio a un nuovo fattore biometrico (nuovo PC, nuovo
        telefono, Windows Hello reinstallato). Va aperto prima, per esempio
        con la chiave di recupero. La chiave di recupero resta valida."""
        if len(frase) < LUNGHEZZA_MINIMA_FRASE:
            raise FraseDebole("Frase troppo corta.")
        self._aes()
        intestazione = {k: v for k, v in self._intestazione.items() if k != "chiave_avvolta"}
        intestazione["biometria"] = biometria.registra()
        chiave_bio = biometria.sblocca(intestazione["biometria"])
        sale = os.urandom(16)
        intestazione["sale"] = _b64(sale)
        parametri = ParametriArgon2(**intestazione["argon2"])
        avvolgente = _deriva_chiave(frase, sale, parametri, chiave_bio)
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
