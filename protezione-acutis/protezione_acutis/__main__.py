"""Riga di comando.

  python -m protezione_acutis stato   mostra se il sistema è attivo
  python -m protezione_acutis prova   dimostrazione completa su dati inventati
  python -m protezione_acutis prova-hello
                                      prova con l'impronta vera (Windows Hello),
                                      solo in memoria e su dati inventati
  python -m protezione_acutis prova-passkey
                                      come sopra, ma con lo smartphone come
                                      lettore d'impronte (passkey)
  python -m protezione_acutis veracrypt-prepara [--fattore hello] [--prova]
  python -m protezione_acutis veracrypt-keyfile [--fattore hello] [--prova]
  python -m protezione_acutis veracrypt-monta [--fattore hello] [--prova] VOLUME LETTERA
                                      volume VeraCrypt con frase + file chiave
                                      rilasciato dall'impronta sul telefono
  python -m protezione_acutis archivio-crea|archivio-elenca CARTELLA
  python -m protezione_acutis archivio-aggiungi CARTELLA FILE...
  python -m protezione_acutis archivio-estrai CARTELLA NOME DESTINAZIONE
  python -m protezione_acutis archivio-rimuovi CARTELLA NOME
                                      archivio cifrato interno (al posto di
                                      VeraCrypt); opzioni --fattore, --prova
  python -m protezione_acutis lavora-apri|lavora-chiudi [--fattore hello] ARCHIVIO
                                      apre tutto in una cartella di lavoro e
                                      poi lo riporta nell'archivio, verifica e
                                      distrugge la copia in chiaro
  python -m protezione_acutis app     finestra "Cassaforte" per tutti i progetti
  python -m protezione_acutis progetti | progetto-collega NOME ARCHIVIO
  python -m protezione_acutis crea-collegamenti
                                      icona sul Desktop e nel menu Start
  python -m protezione_acutis cifra FILE / decifra FILE
                                      disponibili solo dopo l'attivazione
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

from .attivazione import Cassaforte, SistemaDisattivato, sistema_attivo
from .biometria import BiometriaNegata, BiometriaSimulata
from .cripto import ErroreDecifratura


def _prova() -> int:
    frase = "frase di prova inventata per la dimostrazione"
    testo = b"Documento di prova: contenuto inventato, nessuna fonte reale."
    biometria = BiometriaSimulata()
    cassaforte = Cassaforte(biometria)
    with tempfile.TemporaryDirectory() as cartella:
        originale = Path(cartella) / "documento-finto.txt"
        originale.write_bytes(testo)
        cifrato = cassaforte.cifra_file(originale, frase)
        print(f"1. Cifrato:                        {cifrato.name}")
        assert testo not in cifrato.read_bytes()
        print("2. Il testo in chiaro non compare nel file cifrato: OK")
        assert cassaforte.decifra_file(cifrato, frase) == testo
        print("3. Frase giusta + impronta giusta:  decifrato, OK")
        try:
            cassaforte.decifra_file(cifrato, frase + "x")
            print("4. ERRORE: frase sbagliata accettata")
            return 1
        except ErroreDecifratura:
            print("4. Frase sbagliata:                 rifiutato, OK")
        biometria.impronta_valida = False
        try:
            cassaforte.decifra_file(cifrato, frase)
            print("5. ERRORE: impronta mancante accettata")
            return 1
        except BiometriaNegata:
            print("5. Impronta non riconosciuta:       rifiutato, OK")
    print("\nProva completata. Il sistema resta DISATTIVATO.")
    return 0


def _prova_hello() -> int:
    """Usa il sensore vero ma solo su un testo inventato tenuto in memoria:
    nessun file viene letto o scritto. La chiave di prova viene poi cancellata."""
    from .cripto import ParametriArgon2, cifra, decifra
    from .windows_hello import BiometriaWindowsHello

    frase = "frase di prova inventata per windows hello"
    testo = b"Testo inventato per provare il sensore."
    p = ParametriArgon2.per_test()
    hello = BiometriaWindowsHello(nome_chiave="protezione-acutis-prova")
    try:
        print("Appoggia il dito ogni volta che Windows lo chiede (la prima volta anche due richieste di seguito).")
        contenitore = cifra(testo, frase, hello, p)
        print("Ora per decifrare.")
        assert decifra(contenitore, frase, hello, p) == testo
        print("1. Impronta + frase giusta: decifrato, OK")
        print("Ora con una frase sbagliata.")
        try:
            decifra(contenitore, frase + "x", hello, p)
            print("2. ERRORE: frase sbagliata accettata")
            return 1
        except ErroreDecifratura:
            print("2. Impronta giusta + frase sbagliata: rifiutato, OK")
        print("Ora, se vuoi, alla prossima richiesta premi Annulla.")
        try:
            decifra(contenitore, frase, hello, p)
            print("3. Hai confermato l'impronta: decifrato (prova di annullamento saltata)")
        except BiometriaNegata:
            print("3. Impronta annullata: rifiutato, OK")
    except BiometriaNegata as errore:
        print(f"Windows Hello non disponibile: {errore}", file=sys.stderr)
        return 4
    finally:
        try:
            hello.elimina_chiave()
        except Exception:
            pass
    print("\nProva con il sensore completata. La chiave di prova è stata cancellata.")
    return 0


def _prova_passkey() -> int:
    """Smartphone come lettore d'impronte, su un testo inventato in memoria."""
    from .cripto import ParametriArgon2, cifra, decifra
    from .passkey import BiometriaPasskey

    frase = "frase di prova inventata per lo smartphone"
    testo = b"Testo inventato per provare il telefono."
    p = ParametriArgon2.per_test()
    telefono = BiometriaPasskey()
    try:
        print("Nella finestra di Windows scegli 'iPhone, iPad o dispositivo Android',")
        print("inquadra il QR con il telefono e conferma con l'impronta.")
        contenitore = cifra(testo, frase, telefono, p)
        print("Ora conferma di nuovo sul telefono, per decifrare.")
        assert decifra(contenitore, frase, telefono, p) == testo
        print("1. Impronta sul telefono + frase giusta: decifrato, OK")
        print("Ancora una volta, con una frase sbagliata.")
        try:
            decifra(contenitore, frase + "x", telefono, p)
            print("2. ERRORE: frase sbagliata accettata")
            return 1
        except ErroreDecifratura:
            print("2. Impronta giusta + frase sbagliata: rifiutato, OK")
        print("Ora, alla prossima richiesta, annulla sul telefono.")
        try:
            decifra(contenitore, frase, telefono, p)
            print("3. Hai confermato: decifrato (prova di annullamento saltata)")
        except BiometriaNegata:
            print("3. Impronta annullata: rifiutato, OK")
    except BiometriaNegata as errore:
        print(f"Passkey non disponibile: {errore}", file=sys.stderr)
        return 4
    print("\nProva con lo smartphone completata. Puoi cancellare la passkey di")
    print("prova 'protezione-acutis.local' dal gestore password del telefono.")
    return 0


CARTELLA_VC = Path.home() / ".protezione-acutis"


def _veracrypt(argomenti) -> int:
    """Comandi VeraCrypt.

    --fattore sceglie chi rilascia l'impronta: "passkey" (smartphone o chiave
    FIDO2) oppure "hello" (Windows Hello del PC).
    --prova usa un identificativo e una chiave separati, solo per la prova:
    possono essere buttati via senza toccare la configurazione definitiva.
    Con --prova il montaggio è consentito anche a sistema spento, ma SOLO per
    il volume creato in prova.
    """
    from . import veracrypt as vc

    suffisso = "-prova" if argomenti.prova else ""
    identificativo = CARTELLA_VC / f"chiave-veracrypt{suffisso}.json"
    if argomenti.fattore == "hello":
        from .windows_hello import BiometriaWindowsHello

        fattore = BiometriaWindowsHello(nome_chiave=f"protezione-acutis-vc{suffisso}")
        dove = "con Windows Hello (impronta o PIN del PC)"
    else:
        from .passkey import BiometriaPasskey

        fattore = BiometriaPasskey()
        dove = "con l'impronta sul telefono"

    if argomenti.comando == "veracrypt-prepara":
        CARTELLA_VC.mkdir(exist_ok=True)
        print(f"Conferma {dove} per registrare la chiave.")
        vc.prepara(fattore, identificativo)
        print(f"Fatto. Identificativo pubblico salvato in {identificativo}")
        return 0
    if argomenti.comando == "veracrypt-keyfile":
        print(f"Conferma {dove} per sbloccare il file chiave.")
        contenuto = vc.calcola_keyfile(fattore, identificativo)
        with vc.keyfile_temporaneo(contenuto) as keyfile:
            print(f"\nFile chiave temporaneo: {keyfile}")
            print("In VeraCrypt spunta 'Usa file chiave', premi 'File chiave...',")
            print("'Aggiungi file' e scegli il file qui sopra. Finita l'operazione")
            print("in VeraCrypt, torna qui e premi Invio: il file verrà distrutto.")
            input()
        print("File chiave distrutto.")
        return 0
    print(f"Conferma {dove}; poi VeraCrypt ti chiederà la frase.")
    attivo = True if argomenti.prova else None
    return vc.monta(fattore, identificativo, argomenti.volume, argomenti.lettera, attivo=attivo)


def _fattore(nome: str, prova: bool, chiave_hello: str):
    if nome == "hello":
        from .windows_hello import BiometriaWindowsHello

        suffisso = "-prova" if prova else ""
        return BiometriaWindowsHello(nome_chiave=f"{chiave_hello}{suffisso}"), "con Windows Hello"
    from .passkey import BiometriaPasskey

    return BiometriaPasskey(), "con l'impronta sul telefono"


def _archivio(argomenti) -> int:
    """Archivio cifrato interno. La frase si digita qui, sul PC, e non viene
    mostrata né salvata. Con --prova l'archivio può stare anche fuori dalla
    cartella temporanea a sistema spento: usarlo SOLO con file inventati."""
    from .frase import leggi_frase

    from .archivio import Archivio

    fattore, dove = _fattore(argomenti.fattore, argomenti.prova, "protezione-acutis-archivio")
    attivo = True if argomenti.prova else None
    cartella = Path(argomenti.cartella)

    if argomenti.comando == "archivio-crea":
        frase = leggi_frase("Nuova frase segreta: ")
        if leggi_frase("Ripeti la frase: ") != frase:
            print("Le due frasi non coincidono.", file=sys.stderr)
            return 2
        print(f"Conferma {dove}.")
        Archivio.crea(cartella, frase, fattore, attivo=attivo).chiudi()
        print(f"Archivio creato in {cartella}")
        return 0

    if argomenti.comando == "archivio-recupera":
        frase = leggi_frase("Frase segreta: ")
        chiave = leggi_frase("Chiave di recupero (anche con spazi o trattini): ")
        with Archivio.apri_con_recupero(cartella, frase, chiave, attivo=attivo) as archivio:
            print(f"Chiave di recupero accettata. Ora conferma {dove} per collegare la nuova impronta.")
            archivio.riassocia_impronta(frase, fattore)
        print("Fatto: l'archivio ora si apre con la frase e la nuova impronta.")
        print("La chiave di recupero su carta resta valida.")
        return 0

    frase = leggi_frase("Frase segreta: ")
    print(f"Conferma {dove}.")
    with Archivio.apri(cartella, frase, fattore, attivo=attivo) as archivio:
        if argomenti.comando == "archivio-chiave-recupero":
            chiave = archivio.crea_chiave_recupero(frase)
            print()
            print("  CHIAVE DI RECUPERO: scrivila a mano su carta, NON fotografarla,")
            print("  non copiarla nel PC, nel telefono o in chat.")
            print()
            print("   ", chiave)
            print()
            print("  Con questa chiave + la tua frase si riapre l'archivio anche se")
            print("  Windows Hello o il PC si rompono. Ogni nuova chiave annulla la precedente.")
            input("  Quando l'hai trascritta e ricontrollata, premi Invio per cancellare lo schermo.")
            os.system("cls" if os.name == "nt" else "clear")
            return 0
        del frase
        if argomenti.comando == "archivio-elenca":
            voci = archivio.elenca()
            for voce in voci:
                print(f"{voce['dimensione']:>12}  {voce['nome']}")
            print(f"{len(voci)} file.")
        elif argomenti.comando == "archivio-aggiungi":
            for origine in argomenti.file:
                print("Aggiunto:", archivio.aggiungi_file(Path(origine)))
            print("Gli originali NON sono stati cancellati: fallo tu dopo aver verificato.")
        elif argomenti.comando == "archivio-importa":
            esito = archivio.importa_cartella(Path(argomenti.sorgente), avanzamento=_avanzamento)
            print(f"\nFile trovati: {esito['totale']}  copiati ora: {esito['importati']}  "
                  f"già presenti: {esito['gia_presenti']}  errori di lettura: {esito['errori']}  "
                  f"dati copiati: {esito['byte'] / 1e9:.2f} GB")
            print("La cartella originale NON è stata toccata.")
            if esito["errori"]:
                print("Ci sono errori: rilancia lo stesso comando, riprende da dove si era fermato.")
        elif argomenti.comando == "archivio-verifica":
            esito = archivio.verifica_cartella(Path(argomenti.sorgente), avanzamento=_avanzamento)
            print(f"\nControllati: {esito['controllati']}  identici: {esito['identici']}  "
                  f"diversi: {esito['diversi']}  mancanti nell'archivio: {esito['mancanti']}  "
                  f"illeggibili: {esito['illeggibili']}  solo nell'archivio: {esito['solo_in_archivio']}")
            ok = esito["identici"] == esito["controllati"]
            print("ESITO: OK, l'archivio contiene tutto." if ok else "ESITO: DIFFERENZE, non cancellare l'originale.")
            return 0 if ok else 5
        elif argomenti.comando == "archivio-integrita":
            esito = archivio.verifica_integrita(avanzamento=_avanzamento)
            print(f"\nControllati: {esito['controllati']}  integri: {esito['integri']}  "
                  f"danneggiati: {esito['danneggiati']}")
            return 0 if esito["danneggiati"] == 0 else 5
        elif argomenti.comando == "archivio-estrai":
            print("Estratto in:", archivio.estrai(argomenti.nome, Path(argomenti.destinazione)))
        elif argomenti.comando == "archivio-estrai-tutto":
            destinazione = Path(argomenti.destinazione)
            voci = archivio.elenca()
            for numero, voce in enumerate(voci, 1):
                bersaglio = destinazione.joinpath(*voce["nome"].split("/"))
                if destinazione.resolve() not in bersaglio.resolve().parents:
                    raise ValueError("Percorso non valido nell'archivio.")
                bersaglio.parent.mkdir(parents=True, exist_ok=True)
                archivio.estrai(voce["nome"], bersaglio)
                _avanzamento(numero, len(voci))
            print(f"\n{len(voci)} file estratti. Sono IN CHIARO: cancellali appena finito.")
        elif argomenti.comando == "archivio-rimuovi":
            archivio.rimuovi(argomenti.nome)
            print("Rimosso:", argomenti.nome)
    return 0


def _lavoro(argomenti) -> int:
    """Apri per lavorare / chiudi e proteggi. Stampa solo conteggi."""
    from .archivio import Archivio
    from .frase import leggi_frase
    from .lavoro import (apri_lavoro, cartella_lavoro_predefinita, chiudi_lavoro,
                         conta_cancellati, lavoro_aperto)

    fattore, dove = _fattore(argomenti.fattore, argomenti.prova, "protezione-acutis-archivio")
    attivo = True if argomenti.prova else None
    cartella = Path(argomenti.cartella)
    lavoro = Path(argomenti.lavoro) if argomenti.lavoro else cartella_lavoro_predefinita(cartella)
    apri = argomenti.comando == "lavora-apri"
    if apri and lavoro.exists():
        print("C'è già una cartella di lavoro aperta: chiudila prima con 'lavora-chiudi'.",
              file=sys.stderr)
        return 4
    if not apri and not lavoro_aperto(lavoro):
        print("Non c'è una cartella di lavoro aperta da chiudere.", file=sys.stderr)
        return 4
    frase = leggi_frase("Frase segreta: ")
    print(f"Conferma {dove}.")
    with Archivio.apri(cartella, frase, fattore, attivo=attivo) as archivio:
        del frase
        if apri:
            esito = apri_lavoro(archivio, lavoro, avanzamento=_avanzamento)
            print(f"\n{esito['estratti']} file aperti in: {lavoro}")
            print("Sono IN CHIARO: quando hai finito usa 'Chiudi e proteggi'.")
            if os.name == "nt":
                os.startfile(str(lavoro))  # noqa: S606
            return 0
        rimuovi = False
        cancellati = conta_cancellati(archivio, lavoro)
        if cancellati:
            risposta = input(f"{cancellati} file dell'archivio non ci sono più nella cartella "
                             "di lavoro. Toglierli anche dall'archivio? [s/N] ")
            rimuovi = risposta.strip().lower() in ("s", "si", "sì")
        e = chiudi_lavoro(archivio, lavoro, rimuovi_cancellati=rimuovi, avanzamento=_avanzamento)
    print(f"\nNuovi: {e['nuovi']}  modificati: {e['modificati']}  invariati: {e['invariati']}  "
          f"cancellati: {e['cancellati']} (tolti dall'archivio: {e['cancellati_rimossi']})  "
          f"ignorati (file temporanei): {e['ignorati']}")
    print(f"Verificati con SHA-256: {e['verificati']}  verifica fallita: {e['verifica_fallita']}  "
          f"errori di lettura: {e['errori']}")
    if e["errori"] or e["verifica_fallita"]:
        print("ATTENZIONE: la cartella di lavoro NON è stata cancellata. Riprova.")
        return 5
    if e["non_cancellabili"]:
        print(f"Il lavoro è salvato, ma {e['non_cancellabili']} file sono aperti in un altro "
              "programma: chiudilo e rilancia 'Chiudi e proteggi'.")
        return 5
    print("Cartella di lavoro sovrascritta e cancellata. Tutto protetto.")
    return 0


def _progetti(argomenti) -> int:
    from .progetti import Registro

    registro = Registro.carica(argomenti.radice)
    if argomenti.comando == "progetto-collega":
        p = registro.collega(argomenti.nome, Path(argomenti.archivio),
                             Path(argomenti.lavoro) if argomenti.lavoro else None,
                             fattore=argomenti.fattore)
        print(f"Collegato: {p.nome}  (cartella di lavoro: {p.lavoro})")
        return 0
    for p in registro.progetti:
        print(f"{p.nome:<30} {p.stato()}")
    print(f"{len(registro.progetti)} progetti in {registro.percorso}")
    return 0


def _avanzamento(fatti: int, totale: int) -> None:
    print(f"\r  {fatti}/{totale}", end="", file=sys.stderr, flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="protezione_acutis")
    sotto = parser.add_subparsers(dest="comando", required=True)
    sotto.add_parser("stato")
    sotto.add_parser("prova")
    sotto.add_parser("prova-hello")
    sotto.add_parser("prova-passkey")
    for nome, extra in (
        ("archivio-crea", []),
        ("archivio-elenca", []),
        ("archivio-aggiungi", [("file", {"nargs": "+"})]),
        ("archivio-estrai", [("nome", {}), ("destinazione", {})]),
        ("archivio-rimuovi", [("nome", {})]),
        ("archivio-importa", [("sorgente", {})]),
        ("archivio-verifica", [("sorgente", {})]),
        ("archivio-integrita", []),
        ("archivio-estrai-tutto", [("destinazione", {})]),
        ("archivio-chiave-recupero", []),
        ("archivio-recupera", []),
    ):
        comando_ar = sotto.add_parser(nome)
        comando_ar.add_argument("--fattore", choices=["passkey", "hello"], default="passkey")
        comando_ar.add_argument("--prova", action="store_true")
        comando_ar.add_argument("cartella")
        for argomento, opzioni in extra:
            comando_ar.add_argument(argomento, **opzioni)
    for nome in ("veracrypt-prepara", "veracrypt-keyfile", "veracrypt-monta"):
        comando_vc = sotto.add_parser(nome)
        comando_vc.add_argument("--fattore", choices=["passkey", "hello"], default="passkey")
        comando_vc.add_argument("--prova", action="store_true")
        if nome == "veracrypt-monta":
            comando_vc.add_argument("volume")
            comando_vc.add_argument("lettera")
    for nome in ("lavora-apri", "lavora-chiudi"):
        comando_lv = sotto.add_parser(nome)
        comando_lv.add_argument("--fattore", choices=["passkey", "hello"], default="passkey")
        comando_lv.add_argument("--prova", action="store_true")
        comando_lv.add_argument("--lavoro", help="cartella di lavoro (predefinita: accanto all'archivio)")
        comando_lv.add_argument("cartella")
    sotto.add_parser("app").add_argument("--radice")
    sotto.add_parser("progetti").add_argument("--radice")
    collega = sotto.add_parser("progetto-collega")
    collega.add_argument("--radice")
    collega.add_argument("--lavoro")
    collega.add_argument("--fattore", choices=["passkey", "hello"], default="hello")
    collega.add_argument("nome")
    collega.add_argument("archivio")
    sotto.add_parser("crea-collegamenti")
    for nome in ("cifra", "decifra"):
        sotto.add_parser(nome).add_argument("file", type=Path)
    argomenti = parser.parse_args(argv)

    if argomenti.comando == "app":
        from .app import avvia

        return avvia(Path(argomenti.radice) if argomenti.radice else None)
    if argomenti.comando == "crea-collegamenti":
        from .collegamenti import crea_collegamenti

        print(crea_collegamenti())
        return 0
    if argomenti.comando in ("progetti", "progetto-collega"):
        from .progetti import ErroreProgetto

        try:
            return _progetti(argomenti)
        except ErroreProgetto as errore:
            print(errore, file=sys.stderr)
            return 4
    if argomenti.comando.startswith("lavora-"):
        from .cripto import ErroreFormato, FraseDebole
        from .lavoro import LavoroGiaAperto, NessunLavoroAperto

        try:
            return _lavoro(argomenti)
        except (BiometriaNegata, ErroreDecifratura, ErroreFormato, FraseDebole,
                SistemaDisattivato, LavoroGiaAperto, NessunLavoroAperto) as errore:
            print(errore, file=sys.stderr)
            return 4

    if argomenti.comando == "stato":
        print("ATTIVO" if sistema_attivo() else "DISATTIVATO (solo prove)")
        return 0
    if argomenti.comando == "prova":
        return _prova()
    if argomenti.comando == "prova-hello":
        return _prova_hello()
    if argomenti.comando == "prova-passkey":
        return _prova_passkey()
    if argomenti.comando.startswith("archivio-"):
        from .cripto import ErroreFormato, FraseDebole

        try:
            return _archivio(argomenti)
        except (BiometriaNegata, ErroreDecifratura, ErroreFormato, FraseDebole,
                FileNotFoundError, FileExistsError, SistemaDisattivato) as errore:
            print(errore, file=sys.stderr)
            return 4
    if argomenti.comando.startswith("veracrypt-"):
        try:
            return _veracrypt(argomenti)
        except (BiometriaNegata, FileNotFoundError, FileExistsError) as errore:
            print(errore, file=sys.stderr)
            return 4

    if not sistema_attivo():
        print(
            "Sistema DISATTIVATO: cifra e decifra su file reali non sono "
            "disponibili fino alla pubblicazione. Usa il comando 'prova'.",
            file=sys.stderr,
        )
        return 2
    # Dopo l'attivazione qui si collegherà il fattore biometrico reale scelto
    # per il dispositivo di Tommaso (vedi GUIDA_ATTIVAZIONE.md, passo 3).
    print(
        "Nessun fattore biometrico reale configurato: completare il passo 3 "
        "della guida.",
        file=sys.stderr,
    )
    return 3


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SistemaDisattivato as errore:
        print(errore, file=sys.stderr)
        sys.exit(2)
