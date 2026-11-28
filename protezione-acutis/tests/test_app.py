"""Prove della finestra Cassaforte con impronta simulata e dati inventati.
Servono tkinter e uno schermo (anche virtuale): altrimenti si saltano."""

import os
import time

import pytest

tk = pytest.importorskip("tkinter")

from protezione_acutis import BiometriaSimulata, ParametriArgon2  # noqa: E402
from protezione_acutis.archivio import Archivio  # noqa: E402

FRASE = "frase inventata per provare la finestra"
P = ParametriArgon2.per_test()


@pytest.fixture
def app(tmp_path):
    try:
        finestra = tk.Tk()
    except tk.TclError:
        pytest.skip("nessuno schermo disponibile")
    from protezione_acutis.app import AppCassaforte

    bio = BiometriaSimulata()
    a = AppCassaforte(tmp_path / "cassaforte", crea_fattore=lambda p: (bio, "Conferma (simulata)"),
                      opzioni_apri={"parametri_minimi": P, "attivo": False},
                      opzioni_crea={"parametri": P, "attivo": False}, finestra=finestra)
    a.avvisi, a.domande, a.cartelle_mostrate = [], [], []
    a.avvisa = lambda t, testo, tipo="info": a.avvisi.append((tipo, testo))
    a.risposte = []
    a.chiedi = lambda t, testo: (a.domande.append(testo), a.risposte.pop(0) if a.risposte else False)[1]
    a.mostra_cartella = lambda c: a.cartelle_mostrate.append(c)
    a.bio = bio
    yield a
    try:
        a.distruggi()
    except tk.TclError:
        pass
    # gli oggetti tkinter vanno raccolti nel thread principale, non in un
    # thread di lavoro della prova successiva
    del a, finestra
    import gc

    gc.collect()


def _attendi(app, limite=20):
    fine = time.time() + limite
    while time.time() < fine:
        app.finestra.update()
        if not app.occupato and app.coda.empty():
            app.finestra.update()
            return
        time.sleep(0.01)
    raise AssertionError("operazione non terminata")


def _testi_visibili(app):
    return " ".join([app.messaggio.cget("text"), app.spiegazione.cget("text")]
                    + [t for _, t in app.avvisi] + app.domande)


def test_ciclo_completo(app):
    app.crea_progetto("Idea", FRASE, "hello")
    _attendi(app)
    assert app.progetto_scelto().nome == "Idea"
    assert app.etichetta_stato.cget("text") == "Protetto"

    app.campo_frase.insert(0, FRASE)
    app.azione_apri()
    assert app.campo_frase.get() == ""  # la frase si cancella subito
    _attendi(app)
    p = app.progetto_scelto()
    assert p.stato() == "aperto" and app.cartelle_mostrate == [p.cartella_lavoro]
    assert app.etichetta_stato.cget("text") == "Aperto per lavorare"
    assert "disabled" in app.pulsante_apri.state()

    (p.cartella_lavoro / "nome-riservato.txt").write_bytes(b"contenuto inventato")
    app.campo_frase.insert(0, FRASE)
    app.azione_chiudi()
    _attendi(app)
    assert p.stato() == "chiuso" and not p.cartella_lavoro.exists()
    assert "Nuovi 1" in app.messaggio.cget("text")
    assert "nome-riservato" not in _testi_visibili(app)

    # riapro, cancello il file: la domanda arriva e rispondo "no"
    app.campo_frase.insert(0, FRASE)
    app.azione_apri()
    _attendi(app)
    (p.cartella_lavoro / "nome-riservato.txt").unlink()
    app.campo_frase.insert(0, FRASE)
    app.azione_chiudi()
    _attendi(app)
    assert len(app.domande) == 1 and "1 file" in app.domande[0]
    with Archivio.apri(p.cartella_archivio, FRASE, app.bio, P, attivo=False) as a:
        assert len(a.elenca()) == 1
    assert "nome-riservato" not in _testi_visibili(app)


def test_frase_sbagliata(app):
    app.crea_progetto("Idea", FRASE, "hello")
    _attendi(app)
    app.campo_frase.insert(0, FRASE + " sbagliata")
    app.azione_apri()
    _attendi(app)
    assert app.avvisi[-1][0] == "errore" and "non corrette" in app.avvisi[-1][1]
    assert app.progetto_scelto().stato() == "chiuso"


def test_frase_vuota(app):
    app.crea_progetto("Idea", FRASE, "hello")
    _attendi(app)
    app.azione_apri()
    assert app.avvisi and not app.occupato


def test_uscita_con_progetto_aperto(app):
    app.crea_progetto("Idea", FRASE, "hello")
    _attendi(app)
    app.campo_frase.insert(0, FRASE)
    app.azione_apri()
    _attendi(app)
    app.chiedi_tre = lambda t, testo: None  # Annulla
    app.chiudi_finestra()
    assert app.finestra.winfo_exists()
    app.chiedi_tre = lambda t, testo: True  # Sì: torna a chiuderlo
    app.chiudi_finestra()
    assert app.finestra.winfo_exists()


def test_chiave_di_recupero(app):
    app.crea_progetto("Idea", FRASE, "hello")
    _attendi(app)
    app.risposte = [True]
    app.campo_frase.insert(0, FRASE)
    app.azione_chiave_recupero()
    _attendi(app)
    testi = [w.cget("text") for w in app.finestra_chiave.winfo_children() if isinstance(w, tk.Label)]
    assert any(len(t.replace("-", "")) == 56 for t in testi)


def test_nessun_progetto(app):
    assert app.etichetta_nome.cget("text") == "Nessun progetto"
    assert "disabled" in app.pulsante_apri.state()


@pytest.mark.skipif(os.name == "nt", reason="solo dove non c'è Windows Hello")
def test_nome_non_valido(app):
    app.crea_progetto("a/b", FRASE, "hello")
    _attendi(app)
    assert app.avvisi[-1][0] == "errore"


def test_icona_e_titolo_segnalano_lo_stato(app):
    assert app.stato_generale() == "chiusa"
    app.crea_progetto("Idea", FRASE, "hello")
    _attendi(app)
    assert app.finestra.title() == "Cassaforte (tutto chiuso)"
    app.campo_frase.insert(0, FRASE)
    app.azione_apri()
    _attendi(app)
    assert app.stato_generale() == "aperta"
    assert app.finestra.title() == "Cassaforte (aperta: 1)"
    assert app._icona_attuale == "aperta"
    app.campo_frase.insert(0, FRASE)
    app.azione_chiudi()
    _attendi(app)
    assert app._icona_attuale == "chiusa" and app.finestra.title() == "Cassaforte (tutto chiuso)"
