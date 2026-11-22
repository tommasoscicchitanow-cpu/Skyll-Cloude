"""Prove del collegamento a VeraCrypt (senza VeraCrypt: il comando è simulato)."""

import tempfile
from pathlib import Path

import pytest

from protezione_acutis import BiometriaNegata, BiometriaSimulata, SistemaDisattivato
from protezione_acutis import veracrypt as vc


@pytest.fixture
def preparato(tmp_path):
    bio = BiometriaSimulata()
    ident = tmp_path / "chiave-veracrypt.json"
    vc.prepara(bio, ident)
    return bio, ident


def test_keyfile_stabile_e_lungo_64_byte(preparato):
    bio, ident = preparato
    a = vc.calcola_keyfile(bio, ident)
    assert len(a) == 64 and a == vc.calcola_keyfile(bio, ident)


def test_keyfile_non_salvato_su_disco(preparato):
    bio, ident = preparato
    contenuto = vc.calcola_keyfile(bio, ident)
    assert contenuto not in ident.read_bytes()
    assert contenuto.hex() not in ident.read_text()


def test_senza_impronta_niente_keyfile(preparato):
    bio, ident = preparato
    bio.impronta_valida = False
    with pytest.raises(BiometriaNegata):
        vc.calcola_keyfile(bio, ident)


def test_altro_telefono_niente_keyfile(preparato):
    _, ident = preparato
    with pytest.raises(BiometriaNegata):
        vc.calcola_keyfile(BiometriaSimulata(), ident)


def test_prepara_non_sovrascrive(preparato):
    bio, ident = preparato
    with pytest.raises(FileExistsError):
        vc.prepara(bio, ident)


def test_keyfile_temporaneo_distrutto_anche_con_errore():
    with pytest.raises(RuntimeError):
        with vc.keyfile_temporaneo(b"x" * 64) as percorso:
            assert percorso.read_bytes() == b"x" * 64
            raise RuntimeError("errore durante il montaggio")
    assert not percorso.exists()


def test_comando_senza_password():
    comando = vc.comando_monta(r"\Device\Harddisk1\Partition2", "x:", Path("k.key"))
    assert "/password" not in comando and "/p" not in comando
    assert comando[comando.index("/letter") + 1] == "X"
    with pytest.raises(ValueError):
        vc.comando_monta("v", "XY", Path("k.key"))


def test_monta_contenitore_di_prova(preparato):
    bio, ident = preparato
    chiamate = []

    def finto_veracrypt(comando):
        keyfile = Path(comando[comando.index("/keyfile") + 1])
        chiamate.append(keyfile.read_bytes())
        class Esito: returncode = 0
        return Esito()

    volume = str(Path(tempfile.gettempdir()) / "prova.hc")
    assert vc.monta(bio, ident, volume, "X", esegui=finto_veracrypt, attivo=False) == 0
    assert chiamate == [vc.calcola_keyfile(bio, ident)]


def test_disattivato_rifiuta_partizione_reale(preparato):
    bio, ident = preparato
    with pytest.raises(SistemaDisattivato):
        vc.monta(bio, ident, r"\Device\Harddisk0\Partition3", "X", esegui=lambda c: None, attivo=False)
