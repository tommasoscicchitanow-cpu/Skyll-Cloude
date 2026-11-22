"""Fattore biometrico tramite passkey: lo smartphone come lettore d'impronte.

I file restano sul PC. Quando vanno aperti, Windows mostra la finestra delle
passkey; si sceglie "iPhone, iPad o dispositivo Android", si inquadra il
codice QR la prima volta, e da lì in poi il telefono, collegato via
Bluetooth, chiede l'impronta. Lo stesso codice funziona anche con una chiave
di sicurezza FIDO2 con lettore d'impronte o con Windows Hello del PC.

Il segreto si ottiene con l'estensione standard PRF (hmac-secret): il
telefono calcola, dentro il suo chip di sicurezza e solo dopo l'impronta, un
valore che dipende da una "sale" casuale salvata nell'intestazione del file.
Senza quel telefono (e quel dito) il valore non si può ottenere.

Verifica obbligatoria dell'utente: ``user_verification="required"``, quindi
il telefono deve chiedere impronta (o il suo sblocco) a ogni apertura.

Requisiti reali: Windows 11 aggiornato, Bluetooth attivo sul PC, telefono
Android 9+ con Google Password Manager o iPhone con iOS 18+, pacchetto
``fido2`` (vedi requirements-windows.txt). Il supporto PRF via telefono
dipende dalla versione di Windows e del telefono: va verificato con
``python -m protezione_acutis prova-passkey``.
"""

from __future__ import annotations

import base64
import hashlib
import os

from .biometria import BiometriaNegata, FattoreBiometrico

PREFISSO = "passkey"
RP_ID = "protezione-acutis.local"
ORIGINE = "https://" + RP_ID


def _b64(dati: bytes) -> str:
    return base64.urlsafe_b64encode(dati).rstrip(b"=").decode("ascii")


def _da_b64(testo: str) -> bytes:
    return base64.urlsafe_b64decode(testo + "=" * (-len(testo) % 4))


def _primo_prf(risposta) -> bytes | None:
    """Estrae prf.results.first da una risposta fido2 (attributi o dizionario)."""
    estensioni = getattr(risposta, "client_extension_results", None) or {}
    prf = getattr(estensioni, "prf", None)
    if prf is not None and getattr(prf, "results", None) is not None:
        return prf.results.first
    try:
        primo = estensioni["prf"]["results"]["first"]
    except (KeyError, TypeError):
        return None
    return _da_b64(primo) if isinstance(primo, str) else primo


def client_windows():
    """Client WebAuthn di Windows (finestra passkey di sistema)."""
    try:
        from fido2.client import DefaultClientDataCollector
        from fido2.client.windows import WindowsClient
    except Exception as errore:  # ImportError, o API Windows assenti
        raise BiometriaNegata(
            "Passkey disponibili solo su Windows con il pacchetto fido2."
        ) from errore
    if not WindowsClient.is_available():
        raise BiometriaNegata("Le API WebAuthn di Windows non sono disponibili.")
    return WindowsClient(DefaultClientDataCollector(ORIGINE))


class BiometriaPasskey(FattoreBiometrico):
    simulato = False

    def __init__(self, client=None):
        self._client = client

    @property
    def client(self):
        if self._client is None:
            self._client = client_windows()
        return self._client

    def registra(self) -> str:
        from fido2.webauthn import (
            AuthenticatorSelectionCriteria,
            PublicKeyCredentialCreationOptions,
            PublicKeyCredentialParameters,
            PublicKeyCredentialRpEntity,
            PublicKeyCredentialType,
            PublicKeyCredentialUserEntity,
            ResidentKeyRequirement,
            UserVerificationRequirement,
        )

        opzioni = PublicKeyCredentialCreationOptions(
            rp=PublicKeyCredentialRpEntity(id=RP_ID, name="Protezione progetto Acutis"),
            user=PublicKeyCredentialUserEntity(
                id=os.urandom(16), name="custode", display_name="Custode dei file"
            ),
            challenge=os.urandom(32),
            pub_key_cred_params=[
                PublicKeyCredentialParameters(type=PublicKeyCredentialType.PUBLIC_KEY, alg=-7),
                PublicKeyCredentialParameters(type=PublicKeyCredentialType.PUBLIC_KEY, alg=-257),
            ],
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement.PREFERRED,
                user_verification=UserVerificationRequirement.REQUIRED,
            ),
            extensions={"prf": {}},
        )
        try:
            risposta = self.client.make_credential(opzioni)
        except BiometriaNegata:
            raise
        except Exception as errore:
            raise BiometriaNegata(f"Registrazione passkey non riuscita: {errore}") from None

        estensioni = getattr(risposta, "client_extension_results", None) or {}
        prf = getattr(estensioni, "prf", None)
        abilitato = getattr(prf, "enabled", None)
        if abilitato is None:
            try:
                abilitato = estensioni["prf"]["enabled"]
            except (KeyError, TypeError):
                abilitato = False
        if not abilitato:
            raise BiometriaNegata(
                "Questo telefono o questa versione di Windows non supporta PRF: "
                "la passkey non può proteggere i file."
            )
        sale = os.urandom(32)
        return f"{PREFISSO}:{_b64(risposta.raw_id)}:{_b64(sale)}"

    def sblocca(self, identificativo: str) -> bytes:
        from fido2.webauthn import (
            PublicKeyCredentialDescriptor,
            PublicKeyCredentialRequestOptions,
            PublicKeyCredentialType,
            UserVerificationRequirement,
        )

        try:
            prefisso, id_b64, sale_b64 = identificativo.split(":")
            id_credenziale, sale = _da_b64(id_b64), _da_b64(sale_b64)
        except ValueError:
            raise BiometriaNegata("Identificativo passkey non valido.") from None
        if prefisso != PREFISSO:
            raise BiometriaNegata("Questo file non è stato protetto con una passkey.")

        opzioni = PublicKeyCredentialRequestOptions(
            challenge=os.urandom(32),
            rp_id=RP_ID,
            allow_credentials=[
                PublicKeyCredentialDescriptor(type=PublicKeyCredentialType.PUBLIC_KEY, id=id_credenziale)
            ],
            user_verification=UserVerificationRequirement.REQUIRED,
            extensions={"prf": {"eval": {"first": sale}}},
        )
        try:
            selezione = self.client.get_assertion(opzioni)
            risposta = selezione.get_response(0)
        except BiometriaNegata:
            raise
        except Exception:
            raise BiometriaNegata("Impronta non confermata sul telefono o richiesta annullata.") from None
        primo = _primo_prf(risposta)
        if not primo:
            raise BiometriaNegata("Il telefono non ha restituito il segreto PRF.")
        return hashlib.sha256(b"protezione-acutis/passkey/v1" + primo).digest()
