"""Fattore biometrico (impronta digitale).

Il fattore biometrico non "contiene" l'impronta: l'impronta non lascia mai il
dispositivo. Funziona così: al momento della registrazione il dispositivo genera
un segreto casuale di 32 byte e lo custodisce in un'area protetta (Secure
Enclave su Mac, TPM con Windows Hello, keystore hardware su Android, oppure una
passkey/chiave FIDO2 con estensione PRF/hmac-secret). Il segreto viene
rilasciato solo dopo che il sensore ha riconosciuto l'impronta.

Questo modulo definisce l'interfaccia comune, indipendente dalla piattaforma,
e una implementazione simulata da usare SOLO nelle prove automatiche.
L'implementazione reale verrà scelta quando sapremo su quale dispositivo
lavorerà Tommaso (vedi GUIDA_ATTIVAZIONE.md).
"""

from __future__ import annotations

import abc
import os
import secrets


class BiometriaNegata(Exception):
    """L'impronta non è stata riconosciuta, l'utente ha annullato o il
    dispositivo biometrico non è disponibile."""


class FattoreBiometrico(abc.ABC):
    """Interfaccia comune a tutti i fattori biometrici."""

    #: True solo per l'implementazione di prova. Un sistema attivato rifiuta
    #: qualunque fattore con questo attributo a True.
    simulato: bool = False

    @abc.abstractmethod
    def registra(self) -> str:
        """Crea un nuovo segreto protetto da impronta e ne restituisce un
        identificativo pubblico (non segreto), da salvare nell'intestazione
        dei file cifrati."""

    @abc.abstractmethod
    def sblocca(self, identificativo: str) -> bytes:
        """Chiede l'impronta e, se riconosciuta, restituisce il segreto di 32
        byte associato all'identificativo. Altrimenti solleva BiometriaNegata."""


class BiometriaSimulata(FattoreBiometrico):
    """Simulazione per i test: NON offre alcuna protezione reale.

    ``impronta_valida`` simula l'esito del sensore. ``disponibile=False``
    simula un dispositivo senza sensore o con biometria disattivata.
    """

    simulato = True

    def __init__(self, impronta_valida: bool = True, disponibile: bool = True):
        self.impronta_valida = impronta_valida
        self.disponibile = disponibile
        self._segreti: dict[str, bytes] = {}
        self.richieste = 0

    def registra(self) -> str:
        if not self.disponibile:
            raise BiometriaNegata("Sensore biometrico non disponibile.")
        identificativo = "sim-" + secrets.token_hex(8)
        self._segreti[identificativo] = os.urandom(32)
        return identificativo

    def sblocca(self, identificativo: str) -> bytes:
        self.richieste += 1
        if not self.disponibile:
            raise BiometriaNegata("Sensore biometrico non disponibile.")
        if not self.impronta_valida:
            raise BiometriaNegata("Impronta non riconosciuta.")
        try:
            return self._segreti[identificativo]
        except KeyError:
            raise BiometriaNegata("Nessun segreto registrato per questo file.") from None
