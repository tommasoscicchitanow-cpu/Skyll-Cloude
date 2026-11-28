"""Fattore biometrico reale per Windows: Windows Hello.

Come funziona:
  * alla registrazione Windows crea una chiave RSA dentro il chip TPM del PC,
    protetta da Windows Hello. La chiave privata non esce mai dal chip;
  * per sbloccare, Windows mostra la richiesta di impronta, poi la chiave
    firma una "sfida" casuale salvata (in chiaro, non è segreta)
    nell'intestazione del file. La firma RSA PKCS#1 v1.5 è deterministica:
    stessa chiave e stessa sfida danno sempre la stessa firma, da cui si
    ricava il segreto di 32 byte;
  * su un altro PC, o se la chiave viene cancellata, la firma non si può
    produrre e i file non si aprono.

Limite da conoscere: Windows Hello accetta, oltre all'impronta, anche il PIN
di Windows Hello come alternativa. Il programma non può impedirlo; si può solo
scegliere un PIN lungo o disattivarlo dalle impostazioni di accesso, se il PC
lo consente.

Richiede: Windows 10/11, Windows Hello configurato, pacchetti
``winrt-runtime``, ``winrt-Windows.Security.Credentials`` e
``winrt-Windows.Security.Cryptography`` (vedi requirements-windows.txt).
"""

from __future__ import annotations

import asyncio
import hashlib
import secrets
import sys

from .biometria import BiometriaNegata, FattoreBiometrico

PREFISSO = "hello"
NOME_CHIAVE = "protezione-acutis"


def _moduli():
    if sys.platform != "win32":
        raise BiometriaNegata("Windows Hello è disponibile solo su Windows.")
    try:
        from winrt.windows.security.credentials import (
            KeyCredentialCreationOption,
            KeyCredentialManager,
            KeyCredentialStatus,
        )
        from winrt.windows.security.cryptography import CryptographicBuffer
    except ImportError as errore:
        raise BiometriaNegata(
            "Mancano i pacchetti winrt: pip install -r requirements-windows.txt"
        ) from errore
    return KeyCredentialManager, KeyCredentialCreationOption, KeyCredentialStatus, CryptographicBuffer


class BiometriaWindowsHello(FattoreBiometrico):
    simulato = False

    def __init__(self, nome_chiave: str = NOME_CHIAVE):
        self.nome_chiave = nome_chiave

    # -- registrazione ---------------------------------------------------
    async def _registra(self) -> None:
        manager, opzione, stato, _ = _moduli()
        if not await manager.is_supported_async():
            raise BiometriaNegata("Windows Hello non è configurato su questo PC.")
        esito = await manager.request_create_async(self.nome_chiave, opzione.FAIL_IF_EXISTS)
        if esito.status == stato.CREDENTIAL_ALREADY_EXISTS:
            return  # stessa chiave per tutti i file: si usa una sfida diversa
        if esito.status != stato.SUCCESS:
            raise BiometriaNegata(f"Registrazione Windows Hello non riuscita ({esito.status}).")

    def registra(self) -> str:
        asyncio.run(self._registra())
        sfida = secrets.token_hex(32)
        return f"{PREFISSO}:{self.nome_chiave}:{sfida}"

    # -- sblocco ---------------------------------------------------------
    async def _firma(self, nome: str, sfida_hex: str) -> bytes:
        manager, _, stato, buffer = _moduli()
        aperta = await manager.open_async(nome)
        if aperta.status != stato.SUCCESS:
            raise BiometriaNegata("Chiave Windows Hello non trovata su questo PC.")
        firma = await aperta.credential.request_sign_async(buffer.decode_from_hex_string(sfida_hex))
        if firma.status != stato.SUCCESS:
            raise BiometriaNegata("Impronta non riconosciuta o richiesta annullata.")
        return bytes.fromhex(buffer.encode_to_hex_string(firma.result))

    def sblocca(self, identificativo: str) -> bytes:
        try:
            prefisso, nome, sfida = identificativo.split(":")
        except ValueError:
            raise BiometriaNegata("Identificativo biometrico non valido.") from None
        if prefisso != PREFISSO:
            raise BiometriaNegata("Questo file non è stato protetto con Windows Hello.")
        firma = asyncio.run(self._firma(nome, sfida))
        return hashlib.sha256(b"protezione-acutis/windows-hello/v1" + firma).digest()

    # -- rimozione (per le prove) ------------------------------------------
    def elimina_chiave(self) -> None:
        manager, *_ = _moduli()
        asyncio.run(manager.delete_async(self.nome_chiave))
