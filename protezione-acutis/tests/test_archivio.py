"""Prove dell'archivio cifrato interno. Solo dati inventati."""

import json
import os
from pathlib import Path

import pytest

from protezione_acutis import BiometriaNegata, BiometriaSimulata, ErroreDecifratura, ParametriArgon2, SistemaDisattivato
from protezione_acutis.archivio import BLOCCO, Archivio
from protezione_acutis.cripto import ErroreFormato, FraseDebole

FRASE = "frase inventata per provare l'archivio interno"
P = ParametriArgon2.per_test()


@pytest.fixture
def bio():
    return BiometriaSimulata()


@pytest.fixture
def cartella(tmp_path):
    return tmp_path / "archivio"


def _crea(cartella, bio):
    return Archivio.crea(cartella, FRASE, bio, P, attivo=False)


def _apri(cartella, bio, frase=FRASE):
    return Archivio.apri(cartella, frase, bio, P, attivo=False)


def test_aggiungi_chiudi_riapri_leggi(cartella, bio):
    with _crea(cartella, bio) as a:
        a.aggiungi_dati("appunti/intervista-finta.txt", "Testo inventato, è tutto finto.".encode())
    with _apri(cartella, bio) as a:
        assert a.leggi("appunti/intervista-finta.txt") == "Testo inventato, è tutto finto.".encode()
        assert [v["nome"] for v in a.elenca()] == ["appunti/intervista-finta.txt"]


def test_nomi_e_contenuti_non_visibili_su_disco(cartella, bio):
    with _crea(cartella, bio) as a:
        a.aggiungi_dati("fonte-segreta-inventata.txt", b"CONTENUTO-RICONOSCIBILE-123")
    tutto = b"".join(p.read_bytes() for p in cartella.rglob("*") if p.is_file())
    nomi = " ".join(p.name for p in cartella.rglob("*"))
    assert b"CONTENUTO-RICONOSCIBILE" not in tutto
    assert b"fonte-segreta" not in tutto and "fonte-segreta" not in nomi


def test_file_grande_a_piu_blocchi(cartella, bio):
    dati = os.urandom(BLOCCO * 2 + 12345)
    with _crea(cartella, bio) as a:
        a.aggiungi_dati("grande.bin", dati)
    with _apri(cartella, bio) as a:
        assert a.leggi("grande.bin") == dati


def test_file_vuoto(cartella, bio):
    with _crea(cartella, bio) as a:
        a.aggiungi_dati("vuoto.txt", b"")
        assert a.leggi("vuoto.txt") == b""


def test_frase_errata(cartella, bio):
    _crea(cartella, bio).chiudi()
    with pytest.raises(ErroreDecifratura):
        _apri(cartella, bio, FRASE + "x")


def test_senza_impronta(cartella, bio):
    _crea(cartella, bio).chiudi()
    bio.impronta_valida = False
    with pytest.raises(BiometriaNegata):
        _apri(cartella, bio)


def test_altro_dispositivo(cartella, bio):
    _crea(cartella, bio).chiudi()
    with pytest.raises(BiometriaNegata):
        _apri(cartella, BiometriaSimulata())


def test_blocco_alterato(cartella, bio):
    with _crea(cartella, bio) as a:
        a.aggiungi_dati("x.txt", b"dati inventati" * 100)
    blocco = next((cartella / "dati").iterdir())
    grezzo = bytearray(blocco.read_bytes())
    grezzo[-3] ^= 1
    blocco.write_bytes(bytes(grezzo))
    with _apri(cartella, bio) as a, pytest.raises(ErroreDecifratura):
        a.leggi("x.txt")


def test_blocchi_tolti_o_scambiati(cartella, bio):
    dati = os.urandom(BLOCCO * 2 + 10)
    with _crea(cartella, bio) as a:
        a.aggiungi_dati("g.bin", dati)
    blocco = next((cartella / "dati").iterdir())
    grezzo = blocco.read_bytes()
    taglio = 6 + 4 + 12 + BLOCCO + 16  # magia + un blocco intero
    blocco.write_bytes(grezzo[:taglio])  # troncato all'inizio del secondo blocco
    with _apri(cartella, bio) as a, pytest.raises(ErroreDecifratura):
        a.leggi("g.bin")


def test_file_di_dati_scambiati_tra_loro(cartella, bio):
    with _crea(cartella, bio) as a:
        a.aggiungi_dati("a.txt", b"primo")
        a.aggiungi_dati("b.txt", b"secondo")
        ida, idb = (a._indice["file"][n]["id"] for n in ("a.txt", "b.txt"))
    d = cartella / "dati"
    pa, pb = d / f"{ida}.bin", d / f"{idb}.bin"
    ca, cb = pa.read_bytes(), pb.read_bytes()
    pa.write_bytes(cb)
    pb.write_bytes(ca)
    with _apri(cartella, bio) as a, pytest.raises(ErroreDecifratura):
        a.leggi("a.txt")


def test_intestazione_alterata(cartella, bio):
    _crea(cartella, bio).chiudi()
    file = cartella / "archivio.json"
    intestazione = json.loads(file.read_text())
    intestazione["argon2"]["tempo"] += 1
    file.write_text(json.dumps(intestazione))
    with pytest.raises(ErroreDecifratura):
        _apri(cartella, bio)


def test_sostituisci_e_rimuovi(cartella, bio):
    with _crea(cartella, bio) as a:
        a.aggiungi_dati("n.txt", b"vecchio")
        a.aggiungi_dati("n.txt", b"nuovo")
        assert a.leggi("n.txt") == b"nuovo"
        assert len(list((cartella / "dati").iterdir())) == 1
        a.rimuovi("n.txt")
        assert a.elenca() == [] and not list((cartella / "dati").iterdir())


def test_cambia_frase(cartella, bio):
    with _crea(cartella, bio) as a:
        a.aggiungi_dati("f.txt", b"inventato")
        a.cambia_frase("una nuova frase inventata abbastanza lunga", bio)
    with pytest.raises(ErroreDecifratura):
        _apri(cartella, bio)
    with Archivio.apri(cartella, "una nuova frase inventata abbastanza lunga", bio, P, attivo=False) as a:
        assert a.leggi("f.txt") == b"inventato"


def test_estrai_e_aggiungi_file(cartella, bio, tmp_path):
    origine = tmp_path / "finto.txt"
    origine.write_bytes(b"documento finto")
    with _crea(cartella, bio) as a:
        assert a.aggiungi_file(origine) == "finto.txt"
        uscita = a.estrai("finto.txt", tmp_path / "estratto")
    assert uscita.read_bytes() == b"documento finto"


def test_archivio_chiuso_non_utilizzabile(cartella, bio):
    a = _crea(cartella, bio)
    a.aggiungi_dati("x", b"1")
    a.chiudi()
    with pytest.raises(RuntimeError):
        a.aggiungi_dati("y", b"2")


def test_frase_corta_e_doppia_creazione(cartella, bio):
    with pytest.raises(FraseDebole):
        Archivio.crea(cartella, "corta", bio, P, attivo=False)
    _crea(cartella, bio).chiudi()
    with pytest.raises(FileExistsError):
        _crea(cartella, bio)


def test_parametri_deboli_rifiutati_in_produzione(cartella, bio):
    _crea(cartella, bio).chiudi()
    with pytest.raises(ErroreFormato):
        Archivio.apri(cartella, FRASE, bio, attivo=False)


def test_disattivato_rifiuta_cartella_fuori_da_temp(bio):
    with pytest.raises(SistemaDisattivato):
        Archivio.crea(Path.home() / "archivio-vero", FRASE, bio, P, attivo=False)


def test_attivo_rifiuta_biometria_simulata(cartella, bio):
    with pytest.raises(SistemaDisattivato):
        Archivio.crea(cartella, FRASE, bio, P, attivo=True)


def test_riga_di_comando_archivio(monkeypatch, tmp_path, capsys):
    """Il flusso completo da riga di comando, con impronta simulata."""
    import getpass

    from protezione_acutis import __main__ as cli

    bio = BiometriaSimulata()
    monkeypatch.setattr(cli, "_fattore", lambda *a: (bio, "simulata"))
    monkeypatch.setattr(getpass, "getpass", lambda *a: FRASE)
    import protezione_acutis.archivio as modulo

    # parametri Argon2 leggeri solo per la velocità della prova
    monkeypatch.setattr(modulo.Archivio.crea.__func__, "__defaults__", (P, None))
    monkeypatch.setattr(modulo.Archivio.apri.__func__, "__defaults__", (P, None))
    cartella = str(tmp_path / "ar")
    finto = tmp_path / "finto.txt"
    finto.write_bytes(b"inventato")
    assert cli.main(["archivio-crea", cartella]) == 0
    assert cli.main(["archivio-aggiungi", cartella, str(finto)]) == 0
    assert cli.main(["archivio-elenca", cartella]) == 0
    assert "finto.txt" in capsys.readouterr().out
    assert cli.main(["archivio-estrai", cartella, "finto.txt", str(tmp_path / "fuori.txt")]) == 0
    assert (tmp_path / "fuori.txt").read_bytes() == b"inventato"
    monkeypatch.setattr(getpass, "getpass", lambda *a: FRASE + "x")
    assert cli.main(["archivio-elenca", cartella]) == 4


# -- import di cartelle, verifica, recupero --------------------------------

from protezione_acutis.archivio import formatta_chiave_recupero, leggi_chiave_recupero


def _albero_finto(radice: Path) -> Path:
    (radice / "capitolo-1" / "note").mkdir(parents=True)
    (radice / "capitolo-1" / "bozza-inventata.txt").write_bytes(b"bozza finta")
    (radice / "capitolo-1" / "note" / "appunto.txt").write_bytes(b"appunto finto")
    (radice / "foto-finta.bin").write_bytes(os.urandom(BLOCCO + 7))
    (radice / "vuoto.txt").write_bytes(b"")
    return radice


def test_importa_cartella_con_percorsi_relativi(cartella, bio, tmp_path):
    sorgente = _albero_finto(tmp_path / "sorgente")
    with _crea(cartella, bio) as a:
        esito = a.importa_cartella(sorgente)
        assert esito["totale"] == 4 and esito["importati"] == 4 and esito["errori"] == 0
        nomi = {v["nome"] for v in a.elenca()}
    assert nomi == {"capitolo-1/bozza-inventata.txt", "capitolo-1/note/appunto.txt",
                    "foto-finta.bin", "vuoto.txt"}
    with _apri(cartella, bio) as a:
        assert a.leggi("capitolo-1/note/appunto.txt") == b"appunto finto"
    # gli originali non vengono toccati
    assert (sorgente / "capitolo-1" / "bozza-inventata.txt").read_bytes() == b"bozza finta"


def test_importa_riprende_senza_ricopiare(cartella, bio, tmp_path):
    sorgente = _albero_finto(tmp_path / "sorgente")
    with _crea(cartella, bio) as a:
        a.importa_cartella(sorgente)
        esito = a.importa_cartella(sorgente)
    assert esito["gia_presenti"] == 4 and esito["importati"] == 0
    assert len(list((cartella / "dati").iterdir())) == 4


def test_verifica_cartella_solo_conteggi(cartella, bio, tmp_path):
    sorgente = _albero_finto(tmp_path / "sorgente")
    with _crea(cartella, bio) as a:
        a.importa_cartella(sorgente)
        esito = a.verifica_cartella(sorgente)
        assert esito == {"controllati": 4, "identici": 4, "diversi": 0, "mancanti": 0,
                         "illeggibili": 0, "solo_in_archivio": 0}
        assert all(isinstance(v, int) for v in esito.values())
        (sorgente / "vuoto.txt").write_bytes(b"cambiato")
        (sorgente / "nuovo.txt").write_bytes(b"nuovo")
        a.aggiungi_dati("solo-qui.txt", b"x")
        esito = a.verifica_cartella(sorgente)
    assert esito["diversi"] == 1 and esito["mancanti"] == 1 and esito["solo_in_archivio"] == 1


def test_verifica_integrita_rileva_danni(cartella, bio, tmp_path):
    sorgente = _albero_finto(tmp_path / "sorgente")
    with _crea(cartella, bio) as a:
        a.importa_cartella(sorgente)
        assert a.verifica_integrita() == {"controllati": 4, "integri": 4, "danneggiati": 0}
    blocco = max((cartella / "dati").iterdir(), key=lambda p: p.stat().st_size)
    grezzo = bytearray(blocco.read_bytes())
    grezzo[100] ^= 1
    blocco.write_bytes(bytes(grezzo))
    with _apri(cartella, bio) as a:
        assert a.verifica_integrita()["danneggiati"] == 1


def test_formato_chiave_recupero():
    grezza = os.urandom(32)
    testo = formatta_chiave_recupero(grezza)
    assert len(testo.replace("-", "")) == 56
    assert leggi_chiave_recupero(testo.lower().replace("-", " ")) == grezza
    sbagliato = ("A" if testo[0] != "A" else "B") + testo[1:]
    with pytest.raises(ErroreDecifratura):
        leggi_chiave_recupero(sbagliato)
    with pytest.raises(ErroreDecifratura):
        leggi_chiave_recupero(testo[:-5])


def test_recupero_dopo_perdita_impronta(cartella, bio):
    with _crea(cartella, bio) as a:
        a.aggiungi_dati("x.txt", b"inventato")
        chiave = a.crea_chiave_recupero(FRASE)
    assert chiave.replace("-", "") not in (cartella / "archivio.json").read_text()
    # il PC si rompe: l'impronta registrata non esiste più
    bio_perso = bio
    bio_perso.impronta_valida = False
    with pytest.raises(BiometriaNegata):
        _apri(cartella, bio_perso)
    nuovo = BiometriaSimulata()
    with Archivio.apri_con_recupero(cartella, FRASE, chiave, P, attivo=False) as a:
        assert a.leggi("x.txt") == b"inventato"
        a.riassocia_impronta(FRASE, nuovo)
    with _apri(cartella, nuovo) as a:
        assert a.leggi("x.txt") == b"inventato"
    # la chiave di recupero funziona ancora
    Archivio.apri_con_recupero(cartella, FRASE, chiave, P, attivo=False).chiudi()


def test_recupero_richiede_anche_la_frase(cartella, bio):
    with _crea(cartella, bio) as a:
        chiave = a.crea_chiave_recupero(FRASE)
    with pytest.raises(ErroreDecifratura):
        Archivio.apri_con_recupero(cartella, FRASE + "x", chiave, P, attivo=False)
    altra = formatta_chiave_recupero(os.urandom(32))
    with pytest.raises(ErroreDecifratura):
        Archivio.apri_con_recupero(cartella, FRASE, altra, P, attivo=False)


def test_cambio_frase_invalida_vecchio_recupero(cartella, bio):
    with _crea(cartella, bio) as a:
        chiave = a.crea_chiave_recupero(FRASE)
        a.cambia_frase("una nuova frase inventata abbastanza lunga", bio)
    with pytest.raises(ErroreFormato):
        Archivio.apri_con_recupero(cartella, FRASE, chiave, P, attivo=False)


def test_senza_chiave_di_recupero(cartella, bio):
    _crea(cartella, bio).chiudi()
    with pytest.raises(ErroreFormato):
        Archivio.apri_con_recupero(cartella, FRASE, formatta_chiave_recupero(os.urandom(32)), P, attivo=False)


def test_riga_di_comando_import_verifica_senza_nomi(monkeypatch, tmp_path, capsys):
    """L'output di importa, verifica e integrità non contiene mai nomi di file."""
    import getpass

    from protezione_acutis import __main__ as cli
    import protezione_acutis.archivio as modulo

    bio = BiometriaSimulata()
    monkeypatch.setattr(cli, "_fattore", lambda *a: (bio, "simulata"))
    monkeypatch.setattr(getpass, "getpass", lambda *a: FRASE)
    monkeypatch.setattr(modulo.Archivio.crea.__func__, "__defaults__", (P, None))
    monkeypatch.setattr(modulo.Archivio.apri.__func__, "__defaults__", (P, None))
    sorgente = _albero_finto(tmp_path / "sorgente")
    cartella = str(tmp_path / "ar")
    assert cli.main(["archivio-crea", cartella]) == 0
    capsys.readouterr()
    assert cli.main(["archivio-importa", cartella, str(sorgente)]) == 0
    assert cli.main(["archivio-verifica", cartella, str(sorgente)]) == 0
    assert cli.main(["archivio-integrita", cartella]) == 0
    uscita = capsys.readouterr()
    testo = uscita.out + uscita.err
    assert "ESITO: OK" in testo
    for parola in ("capitolo", "bozza", "appunto", "foto-finta", "vuoto"):
        assert parola not in testo
    (sorgente / "vuoto.txt").write_bytes(b"cambiato")
    assert cli.main(["archivio-verifica", cartella, str(sorgente)]) == 5
    assert cli.main(["archivio-estrai-tutto", cartella, str(tmp_path / "fuori")]) == 0
    assert (tmp_path / "fuori" / "capitolo-1" / "note" / "appunto.txt").read_bytes() == b"appunto finto"
