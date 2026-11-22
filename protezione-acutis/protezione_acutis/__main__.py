"""Riga di comando.

  python -m protezione_acutis stato   mostra se il sistema è attivo
  python -m protezione_acutis prova   dimostrazione completa su dati inventati
  python -m protezione_acutis prova-hello
                                      prova con l'impronta vera (Windows Hello),
                                      solo in memoria e su dati inventati
  python -m protezione_acutis prova-passkey
                                      come sopra, ma con lo smartphone come
                                      lettore d'impronte (passkey)
  python -m protezione_acutis veracrypt-prepara
  python -m protezione_acutis veracrypt-keyfile
  python -m protezione_acutis veracrypt-monta VOLUME LETTERA
                                      volume VeraCrypt con frase + file chiave
                                      rilasciato dall'impronta sul telefono
  python -m protezione_acutis cifra FILE / decifra FILE
                                      disponibili solo dopo l'attivazione
"""

from __future__ import annotations

import argparse
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


IDENTIFICATIVO_VC = Path.home() / ".protezione-acutis" / "chiave-veracrypt.json"


def _veracrypt(argomenti) -> int:
    from . import veracrypt as vc
    from .passkey import BiometriaPasskey

    telefono = BiometriaPasskey()
    if argomenti.comando == "veracrypt-prepara":
        IDENTIFICATIVO_VC.parent.mkdir(exist_ok=True)
        print("Conferma con l'impronta sul telefono per registrare la passkey.")
        vc.prepara(telefono, IDENTIFICATIVO_VC)
        print(f"Fatto. Identificativo pubblico salvato in {IDENTIFICATIVO_VC}")
        return 0
    if argomenti.comando == "veracrypt-keyfile":
        contenuto = vc.calcola_keyfile(telefono, IDENTIFICATIVO_VC)
        with vc.keyfile_temporaneo(contenuto) as keyfile:
            print(f"File chiave temporaneo: {keyfile}")
            print("Selezionalo in VeraCrypt (Usa file chiave), completa, poi premi Invio qui.")
            input()
        print("File chiave distrutto.")
        return 0
    return vc.monta(telefono, IDENTIFICATIVO_VC, argomenti.volume, argomenti.lettera)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="protezione_acutis")
    sotto = parser.add_subparsers(dest="comando", required=True)
    sotto.add_parser("stato")
    sotto.add_parser("prova")
    sotto.add_parser("prova-hello")
    sotto.add_parser("prova-passkey")
    sotto.add_parser("veracrypt-prepara")
    sotto.add_parser("veracrypt-keyfile")
    monta = sotto.add_parser("veracrypt-monta")
    monta.add_argument("volume")
    monta.add_argument("lettera")
    for nome in ("cifra", "decifra"):
        sotto.add_parser(nome).add_argument("file", type=Path)
    argomenti = parser.parse_args(argv)

    if argomenti.comando == "stato":
        print("ATTIVO" if sistema_attivo() else "DISATTIVATO (solo prove)")
        return 0
    if argomenti.comando == "prova":
        return _prova()
    if argomenti.comando == "prova-hello":
        return _prova_hello()
    if argomenti.comando == "prova-passkey":
        return _prova_passkey()
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
