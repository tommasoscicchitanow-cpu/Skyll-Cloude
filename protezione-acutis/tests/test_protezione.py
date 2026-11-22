"""Prove automatiche. Usano solo frasi e documenti inventati."""

import json
import tempfile
from pathlib import Path

import pytest

from protezione_acutis import (
    BiometriaNegata,
    BiometriaSimulata,
    Cassaforte,
    ErroreDecifratura,
    ErroreFormato,
    FattoreBiometrico,
    ParametriArgon2,
    SistemaDisattivato,
    cifra,
    decifra,
)
from protezione_acutis.__main__ import main
from protezione_acutis.attivazione import CONFIGURAZIONE_REPOSITORY, sistema_attivo
from protezione_acutis.cripto import FraseDebole

FRASE = "il gatto viola canta sotto la luna di prova"
TESTO = "Appunti inventati per la prova: nessun nome reale, è tutto finto.".encode()
P = ParametriArgon2.per_test()


@pytest.fixture
def bio():
    return BiometriaSimulata()


def _cifra(bio, dati=TESTO, frase=FRASE):
    return cifra(dati, frase, bio, P)


# 1. Cifratura e decifratura -------------------------------------------------

def test_andata_e_ritorno(bio):
    assert decifra(_cifra(bio), FRASE, bio, P) == TESTO


def test_testo_in_chiaro_non_compare(bio):
    contenitore = _cifra(bio)
    assert TESTO not in contenitore
    assert b"Appunti" not in contenitore


def test_due_cifrature_sono_diverse(bio):
    assert _cifra(bio) != _cifra(bio)


def test_file_vuoto_e_file_grande(bio):
    assert decifra(_cifra(bio, b""), FRASE, bio, P) == b""
    grande = bytes(range(256)) * 20_000  # circa 5 MB
    assert decifra(_cifra(bio, grande), FRASE, bio, P) == grande


def test_frase_con_accenti_normalizzata(bio):
    composta = "perché la frase di prova è lunga"
    scomposta = "perché la frase di prova è lunga"
    contenitore = _cifra(bio, frase=composta)
    assert decifra(contenitore, scomposta, bio, P) == TESTO


def test_parametri_di_produzione_funzionano(bio):
    contenitore = cifra(TESTO, FRASE, bio)  # 64 MiB, 3 passaggi
    assert decifra(contenitore, FRASE, bio) == TESTO


# 2. Rifiuto con frase errata ------------------------------------------------

@pytest.mark.parametrize(
    "sbagliata",
    [FRASE + " ", FRASE.upper(), FRASE[:-1], "una frase completamente diversa", ""],
)
def test_frase_errata_rifiutata(bio, sbagliata):
    with pytest.raises(ErroreDecifratura):
        decifra(_cifra(bio), sbagliata, bio, P)


def test_frase_troppo_corta_rifiutata_in_cifratura(bio):
    with pytest.raises(FraseDebole):
        cifra(TESTO, "corta", bio, P)


# 3. Rifiuto senza biometria -------------------------------------------------

def test_impronta_non_riconosciuta(bio):
    contenitore = _cifra(bio)
    bio.impronta_valida = False
    with pytest.raises(BiometriaNegata):
        decifra(contenitore, FRASE, bio, P)


def test_sensore_non_disponibile(bio):
    contenitore = _cifra(bio)
    bio.disponibile = False
    with pytest.raises(BiometriaNegata):
        decifra(contenitore, FRASE, bio, P)


def test_altro_dispositivo_con_frase_giusta(bio):
    """Chi conosce la frase ma non ha il dispositivo con l'impronta registrata
    non apre il file."""
    contenitore = _cifra(bio)
    with pytest.raises(BiometriaNegata):
        decifra(contenitore, FRASE, BiometriaSimulata(), P)


class BiometriaFalsa(FattoreBiometrico):
    """Un attaccante che risponde con un segreto inventato."""

    simulato = True

    def registra(self):
        return "falso"

    def sblocca(self, identificativo):
        return b"\x00" * 32


def test_segreto_biometrico_falso_con_frase_giusta(bio):
    with pytest.raises(ErroreDecifratura):
        decifra(_cifra(bio), FRASE, BiometriaFalsa(), P)


def test_impronta_chiesta_a_ogni_apertura(bio):
    contenitore = _cifra(bio)
    prima = bio.richieste
    for _ in range(3):
        decifra(contenitore, FRASE, bio, P)
    assert bio.richieste == prima + 3


# 4. Integrità e formato -----------------------------------------------------

def test_byte_alterato_rifiutato(bio):
    contenitore = bytearray(_cifra(bio))
    contenitore[-5] ^= 0x01
    with pytest.raises(ErroreDecifratura):
        decifra(bytes(contenitore), FRASE, bio, P)


def test_intestazione_alterata_rifiutata(bio):
    contenitore = _cifra(bio)
    # sposta un carattere del sale: l'intestazione è autenticata
    indice = contenitore.index(b'"sale":"') + 8
    alterato = bytearray(contenitore)
    alterato[indice] = ord("A") if alterato[indice] != ord("A") else ord("B")
    with pytest.raises((ErroreDecifratura, ErroreFormato)):
        decifra(bytes(alterato), FRASE, bio, P)


def test_file_troncato_e_file_estraneo(bio):
    contenitore = _cifra(bio)
    with pytest.raises((ErroreFormato, ErroreDecifratura)):
        decifra(contenitore[:-20], FRASE, bio, P)
    with pytest.raises(ErroreFormato):
        decifra(b"non sono un file cifrato", FRASE, bio, P)


def test_parametri_deboli_rifiutati_in_produzione(bio):
    contenitore = _cifra(bio)  # cifrato con parametri leggeri
    with pytest.raises(ErroreFormato):
        decifra(contenitore, FRASE, bio)  # minimi di produzione


# 5. Interruttore di attivazione ---------------------------------------------

def test_configurazione_del_repository_e_disattivata():
    """Il repository deve restare disattivato fino alla pubblicazione."""
    assert json.loads(CONFIGURAZIONE_REPOSITORY.read_text())["attivo"] is False
    assert sistema_attivo(CONFIGURAZIONE_REPOSITORY) is False


def test_senza_file_locale_il_sistema_e_spento(tmp_path):
    assert sistema_attivo(tmp_path / "inesistente.json") is False


@pytest.mark.parametrize("valore", ["true", 1, "si", None])
def test_solo_il_vero_booleano_attiva(tmp_path, valore):
    config = tmp_path / "c.json"
    config.write_text(json.dumps({"attivo": valore}))
    assert sistema_attivo(config) is False


def test_disattivato_rifiuta_file_fuori_dalla_cartella_temporanea(bio):
    cassaforte = Cassaforte(bio)
    with pytest.raises(SistemaDisattivato):
        cassaforte.cifra_file(Path.home() / "documento.txt", FRASE)


class BiometriaReale(BiometriaFalsa):
    simulato = False


def test_disattivato_rifiuta_biometria_reale():
    with pytest.raises(SistemaDisattivato):
        Cassaforte(BiometriaReale())


def test_attivato_rifiuta_biometria_simulata(tmp_path, bio):
    config = tmp_path / "c.json"
    config.write_text('{"attivo": true}')
    with pytest.raises(SistemaDisattivato):
        Cassaforte(bio, percorso_config=config)


def test_cassaforte_su_file_temporanei(bio):
    cassaforte = Cassaforte(bio)
    with tempfile.TemporaryDirectory() as cartella:
        originale = Path(cartella) / "finto.txt"
        originale.write_bytes(TESTO)
        cifrato = cassaforte.cifra_file(originale, FRASE, elimina_originale=True)
        assert not originale.exists()
        assert cifrato.suffix == ".acutis"
        assert cassaforte.decifra_file(cifrato, FRASE) == TESTO


@pytest.mark.skipif(sistema_attivo(), reason="sistema attivato su questo computer")
def test_riga_di_comando(capsys):
    assert main(["stato"]) == 0
    assert "DISATTIVATO" in capsys.readouterr().out
    assert main(["prova"]) == 0
    assert main(["cifra", "qualunque.txt"]) == 2
