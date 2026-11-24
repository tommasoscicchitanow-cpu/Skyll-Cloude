"""Elenco dei progetti, icona, collegamenti e comandi lavora-*. Solo dati inventati."""

import struct

import pytest

from protezione_acutis import BiometriaSimulata, ParametriArgon2
from protezione_acutis.archivio import Archivio
from protezione_acutis.collegamenti import script_vbs
from protezione_acutis.icona import ico, png
from protezione_acutis.progetti import ErroreProgetto, Registro

FRASE = "frase inventata per provare i progetti"
P = ParametriArgon2.per_test()
OPZ = {"parametri": P, "attivo": False}


def test_nuovo_progetto_e_ricarica(tmp_path):
    reg = Registro.carica(tmp_path / "cassaforte")
    assert reg.progetti == []
    p = reg.nuovo("Idea uno", FRASE, BiometriaSimulata(), **OPZ)
    assert p.stato() == "chiuso"
    assert p.cartella_archivio == tmp_path / "cassaforte" / "Idea uno" / "archivio"
    di_nuovo = Registro.carica(tmp_path / "cassaforte")
    assert [x.nome for x in di_nuovo.progetti] == ["Idea uno"]
    assert di_nuovo.trova("idea UNO").fattore == "hello"


def test_nomi_non_validi_o_doppi(tmp_path):
    reg = Registro.carica(tmp_path)
    for cattivo in ("", "..", "a/b", "a\\b", "x" * 61, "c:"):
        with pytest.raises(ErroreProgetto):
            reg.nuovo(cattivo, FRASE, BiometriaSimulata(), **OPZ)
    reg.nuovo("Uno", FRASE, BiometriaSimulata(), **OPZ)
    with pytest.raises(ErroreProgetto):
        reg.nuovo("uno", FRASE, BiometriaSimulata(), **OPZ)


def test_collega_archivio_esistente_senza_toccarlo(tmp_path):
    vecchio = tmp_path / "archivio-vecchio"
    with Archivio.crea(vecchio, FRASE, BiometriaSimulata(), P, attivo=False) as a:
        a.aggiungi_dati("x.txt", b"finto")
    prima = sorted((f.name, f.stat().st_mtime_ns) for f in vecchio.rglob("*"))
    reg = Registro.carica(tmp_path / "cassaforte")
    p = reg.collega("Vecchio", vecchio)
    assert p.cartella_lavoro == tmp_path / "lavoro-aperto"
    assert sorted((f.name, f.stat().st_mtime_ns) for f in vecchio.rglob("*")) == prima
    with pytest.raises(ErroreProgetto):
        reg.collega("Altro", tmp_path / "non-esiste")


def test_stato_assente_se_disco_scollegato(tmp_path):
    reg = Registro.carica(tmp_path)
    p = reg.nuovo("Uno", FRASE, BiometriaSimulata(), **OPZ)
    p.archivio = str(tmp_path / "scollegato")
    assert p.stato() == "assente"


def test_icona_valida():
    dati = ico((16, 32))
    riservato, tipo, quante = struct.unpack("<HHH", dati[:6])
    assert (riservato, tipo, quante) == (0, 1, 2)
    assert png(16).startswith(b"\x89PNG")


def test_script_collegamenti():
    testo = script_vbs("C:\\Py\\pythonw.exe", "C:\\Cartella \"x\"", "C:\\c.ico")
    assert '"C:\\Py\\pythonw.exe"' in testo
    assert '"C:\\Cartella ""x"""' in testo
    assert "-m protezione_acutis app" in testo
    assert 'SpecialFolders("Desktop")' in testo and 'SpecialFolders("Programs")' in testo


def test_riga_di_comando_lavora(monkeypatch, tmp_path, capsys):
    import builtins
    import getpass

    from protezione_acutis import __main__ as cli
    import protezione_acutis.archivio as modulo

    bio = BiometriaSimulata()
    monkeypatch.setattr(cli, "_fattore", lambda *a: (bio, "simulata"))
    monkeypatch.setattr(getpass, "getpass", lambda *a: FRASE)
    monkeypatch.setattr(modulo.Archivio.apri.__func__, "__defaults__", (P, None))
    cartella = tmp_path / "ar"
    with Archivio.crea(cartella, FRASE, bio, P, attivo=False) as a:
        a.aggiungi_dati("segreto-nome.txt", b"finto")
        a.aggiungi_dati("da-togliere.txt", b"finto")
    lavoro = tmp_path / "lavoro-aperto"
    assert cli.main(["lavora-apri", str(cartella)]) == 0
    assert cli.main(["lavora-apri", str(cartella)]) == 4  # secondo apri bloccato
    (lavoro / "nuovo-nome.txt").write_bytes(b"nuovo")
    (lavoro / "da-togliere.txt").unlink()
    monkeypatch.setattr(builtins, "input", lambda *a: "s")
    assert cli.main(["lavora-chiudi", str(cartella)]) == 0
    assert not lavoro.exists()
    assert cli.main(["lavora-chiudi", str(cartella)]) == 4
    uscita = capsys.readouterr()
    for nome in ("segreto-nome", "nuovo-nome", "da-togliere"):
        assert nome not in uscita.out + uscita.err
    with Archivio.apri(cartella, FRASE, bio, P, attivo=False) as a:
        assert sorted(v["nome"] for v in a.elenca()) == ["nuovo-nome.txt", "segreto-nome.txt"]


def test_riga_di_comando_progetti(tmp_path, capsys):
    from protezione_acutis import __main__ as cli

    vecchio = tmp_path / "archivio-x"
    Archivio.crea(vecchio, FRASE, BiometriaSimulata(), P, attivo=False).chiudi()
    radice = str(tmp_path / "cassaforte")
    assert cli.main(["progetto-collega", "--radice", radice, "X", str(vecchio)]) == 0
    assert cli.main(["progetti", "--radice", radice]) == 0
    assert "X" in capsys.readouterr().out
    assert cli.main(["progetto-collega", "--radice", radice, "X", str(vecchio)]) == 4
