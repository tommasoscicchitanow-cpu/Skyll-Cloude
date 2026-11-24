"""Prove di 'Apri per lavorare' / 'Chiudi e proteggi'. Solo dati inventati."""

import os
from pathlib import Path

import pytest

from protezione_acutis import BiometriaSimulata, ParametriArgon2
from protezione_acutis.archivio import BLOCCO, Archivio
from protezione_acutis.lavoro import (
    MARCATORE,
    LavoroGiaAperto,
    NessunLavoroAperto,
    _sha256_archiviato,
    apri_lavoro,
    cartella_lavoro_predefinita,
    chiudi_lavoro,
    conta_cancellati,
)

FRASE = "frase inventata per provare il lavoro quotidiano"
P = ParametriArgon2.per_test()


@pytest.fixture
def ambiente(tmp_path):
    bio = BiometriaSimulata()
    cartella = tmp_path / "archivio"
    with Archivio.crea(cartella, FRASE, bio, P, attivo=False) as a:
        a.aggiungi_dati("cap1/bozza.txt", b"bozza finta")
        a.aggiungi_dati("cap1/note/nota.txt", b"nota finta")
        a.aggiungi_dati("grande.bin", os.urandom(BLOCCO + 3))
    return bio, cartella, cartella_lavoro_predefinita(cartella)


def _apri(bio, cartella):
    return Archivio.apri(cartella, FRASE, bio, P, attivo=False)


def test_cartella_di_lavoro_accanto_all_archivio(ambiente):
    _, cartella, lavoro = ambiente
    assert lavoro.parent == cartella.resolve().parent and lavoro.name == "lavoro-aperto"


def test_apri_estrae_tutto_con_le_cartelle(ambiente):
    bio, cartella, lavoro = ambiente
    with _apri(bio, cartella) as a:
        assert apri_lavoro(a, lavoro) == {"estratti": 3}
    assert (lavoro / "cap1" / "note" / "nota.txt").read_bytes() == b"nota finta"
    assert (lavoro / MARCATORE).exists()


def test_secondo_apri_bloccato(ambiente):
    bio, cartella, lavoro = ambiente
    with _apri(bio, cartella) as a:
        apri_lavoro(a, lavoro)
        with pytest.raises(LavoroGiaAperto):
            apri_lavoro(a, lavoro)


def test_chiudi_senza_modifiche_distrugge_la_cartella(ambiente):
    bio, cartella, lavoro = ambiente
    with _apri(bio, cartella) as a:
        apri_lavoro(a, lavoro)
        esito = chiudi_lavoro(a, lavoro)
    assert esito["invariati"] == 3 and esito["verificati"] == 3
    assert esito["cartella_distrutta"] and not lavoro.exists()


def test_chiudi_riporta_nuovi_e_modificati(ambiente):
    bio, cartella, lavoro = ambiente
    with _apri(bio, cartella) as a:
        apri_lavoro(a, lavoro)
    (lavoro / "cap1" / "bozza.txt").write_bytes(b"bozza riscritta")
    (lavoro / "cap2").mkdir()
    (lavoro / "cap2" / "nuovo.txt").write_bytes(b"capitolo nuovo")
    (lavoro / "~$bozza.txt").write_bytes(b"blocco di Word")
    (lavoro / "Thumbs.db").write_bytes(b"x")
    with _apri(bio, cartella) as a:
        esito = chiudi_lavoro(a, lavoro)
        assert esito["nuovi"] == 1 and esito["modificati"] == 1 and esito["invariati"] == 2
        assert esito["ignorati"] == 2 and esito["verificati"] == 4
    assert not lavoro.exists()
    with _apri(bio, cartella) as a:
        assert a.leggi("cap1/bozza.txt") == b"bozza riscritta"
        assert a.leggi("cap2/nuovo.txt") == b"capitolo nuovo"
        assert "~$bozza.txt" not in {v["nome"] for v in a.elenca()}


def test_cancellati_restano_nell_archivio_salvo_conferma(ambiente):
    bio, cartella, lavoro = ambiente
    with _apri(bio, cartella) as a:
        apri_lavoro(a, lavoro)
        (lavoro / "cap1" / "bozza.txt").unlink()
        esito = chiudi_lavoro(a, lavoro)
        assert esito["cancellati"] == 1 and esito["cancellati_rimossi"] == 0
        assert a.leggi("cap1/bozza.txt") == b"bozza finta"
        apri_lavoro(a, lavoro)
        (lavoro / "cap1" / "bozza.txt").unlink()
        esito = chiudi_lavoro(a, lavoro, rimuovi_cancellati=True)
        assert esito["cancellati_rimossi"] == 1
        assert "cap1/bozza.txt" not in {v["nome"] for v in a.elenca()}


def test_chiudi_senza_lavoro_aperto(ambiente):
    bio, cartella, lavoro = ambiente
    with _apri(bio, cartella) as a, pytest.raises(NessunLavoroAperto):
        chiudi_lavoro(a, lavoro)


def test_file_bloccato_cartella_non_distrutta_e_si_puo_richiudere(ambiente, monkeypatch):
    bio, cartella, lavoro = ambiente
    with _apri(bio, cartella) as a:
        contenuto_grande = _sha256_archiviato(a, "grande.bin")
        apri_lavoro(a, lavoro)
        bloccato = lavoro / "grande.bin"
        originale_unlink = Path.unlink

        def unlink_finto(self, *args, **kw):
            if self == bloccato:
                raise PermissionError("aperto in un altro programma")
            return originale_unlink(self, *args, **kw)

        monkeypatch.setattr(Path, "unlink", unlink_finto)
        esito = chiudi_lavoro(a, lavoro)
        assert esito["non_cancellabili"] == 1 and not esito["cartella_distrutta"]
        assert (lavoro / MARCATORE).exists()
        monkeypatch.setattr(Path, "unlink", originale_unlink)
        # il file rimasto è già sovrascritto: non va né reimportato né
        # contato come "cancellato" dagli altri
        assert conta_cancellati(a, lavoro) == 0
        esito = chiudi_lavoro(a, lavoro, rimuovi_cancellati=True)
        assert esito["ripresa"] and esito["cartella_distrutta"]
        assert esito["modificati"] == 0 and esito["cancellati_rimossi"] == 0
        assert a.leggi("cap1/bozza.txt") == b"bozza finta"
        assert len(a.leggi("grande.bin")) == BLOCCO + 3
        assert _sha256_archiviato(a, "grande.bin") == contenuto_grande


def test_verifica_fallita_non_distrugge(ambiente, monkeypatch):
    bio, cartella, lavoro = ambiente
    import protezione_acutis.lavoro as modulo

    with _apri(bio, cartella) as a:
        apri_lavoro(a, lavoro)
        monkeypatch.setattr(modulo, "_sha256_archiviato", lambda *x: "0" * 64)
        esito = chiudi_lavoro(a, lavoro)
    assert esito["verifica_fallita"] == 3 and not esito["cartella_distrutta"]
    assert lavoro.exists()


def test_conta_cancellati(ambiente):
    bio, cartella, lavoro = ambiente
    with _apri(bio, cartella) as a:
        apri_lavoro(a, lavoro)
        (lavoro / "grande.bin").unlink()
        assert conta_cancellati(a, lavoro) == 1


def test_apertura_interrotta_non_lascia_file_in_chiaro(ambiente, monkeypatch):
    bio, cartella, lavoro = ambiente
    with _apri(bio, cartella) as a:
        def guasto(*x, **k):
            raise OSError("disco pieno")

        monkeypatch.setattr(a, "estrai", guasto)
        with pytest.raises(OSError):
            apri_lavoro(a, lavoro)
    assert not lavoro.exists()
