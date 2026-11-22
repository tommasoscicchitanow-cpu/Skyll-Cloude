"""Prove del fattore passkey (smartphone) con un telefono simulato.

Il telefono simulato si comporta come un vero autenticatore PRF: tiene una
chiave interna e restituisce HMAC(chiave, sale) solo se l'impronta è valida.
"""

import hashlib
import hmac
import os
from types import SimpleNamespace

import pytest

pytest.importorskip("fido2")

from fido2.webauthn import UserVerificationRequirement

from protezione_acutis import BiometriaNegata, ErroreDecifratura, ParametriArgon2, cifra, decifra
from protezione_acutis.passkey import BiometriaPasskey

FRASE = "frase inventata per provare il telefono"
TESTO = b"Testo inventato per la prova con lo smartphone."
P = ParametriArgon2.per_test()


class TelefonoSimulato:
    def __init__(self, supporta_prf=True):
        self.chiavi = {}
        self.impronta_valida = True
        self.supporta_prf = supporta_prf
        self.richieste_impronta = 0

    def make_credential(self, opzioni):
        assert opzioni.authenticator_selection.user_verification == UserVerificationRequirement.REQUIRED
        id_cred = os.urandom(16)
        self.chiavi[id_cred] = os.urandom(32)
        return SimpleNamespace(
            raw_id=id_cred,
            client_extension_results={"prf": {"enabled": self.supporta_prf}},
        )

    def get_assertion(self, opzioni):
        assert opzioni.user_verification == UserVerificationRequirement.REQUIRED
        self.richieste_impronta += 1
        if not self.impronta_valida:
            raise RuntimeError("NotAllowedError")
        id_cred = opzioni.allow_credentials[0].id
        if id_cred not in self.chiavi:
            raise RuntimeError("credenziale sconosciuta")
        sale = opzioni.extensions["prf"]["eval"]["first"]
        primo = hmac.new(self.chiavi[id_cred], sale, hashlib.sha256).digest()
        risposta = SimpleNamespace(client_extension_results={"prf": {"results": {"first": primo}}})
        return SimpleNamespace(get_response=lambda i: risposta)


@pytest.fixture
def telefono():
    return TelefonoSimulato()


def test_andata_e_ritorno_con_telefono(telefono):
    bio = BiometriaPasskey(client=telefono)
    contenitore = cifra(TESTO, FRASE, bio, P)
    assert decifra(contenitore, FRASE, bio, P) == TESTO
    assert telefono.richieste_impronta == 2  # una per cifrare, una per aprire


def test_frase_errata_con_telefono(telefono):
    bio = BiometriaPasskey(client=telefono)
    contenitore = cifra(TESTO, FRASE, bio, P)
    with pytest.raises(ErroreDecifratura):
        decifra(contenitore, FRASE + "x", bio, P)


def test_impronta_rifiutata_sul_telefono(telefono):
    bio = BiometriaPasskey(client=telefono)
    contenitore = cifra(TESTO, FRASE, bio, P)
    telefono.impronta_valida = False
    with pytest.raises(BiometriaNegata):
        decifra(contenitore, FRASE, bio, P)


def test_altro_telefono_non_apre(telefono):
    contenitore = cifra(TESTO, FRASE, BiometriaPasskey(client=telefono), P)
    with pytest.raises(BiometriaNegata):
        decifra(contenitore, FRASE, BiometriaPasskey(client=TelefonoSimulato()), P)


def test_telefono_senza_prf_rifiutato():
    with pytest.raises(BiometriaNegata):
        BiometriaPasskey(client=TelefonoSimulato(supporta_prf=False)).registra()


def test_file_diversi_hanno_segreti_diversi(telefono):
    bio = BiometriaPasskey(client=telefono)
    a, b = bio.registra(), bio.registra()
    assert bio.sblocca(a) != bio.sblocca(b)
    assert bio.sblocca(a) == bio.sblocca(a)


def test_identificativo_estraneo_rifiutato(telefono):
    bio = BiometriaPasskey(client=telefono)
    for sbagliato in ("sim-123", "hello:x:00", "passkey:solo-due"):
        with pytest.raises(BiometriaNegata):
            bio.sblocca(sbagliato)
