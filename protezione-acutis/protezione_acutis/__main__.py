"""Riga di comando.

  python -m protezione_acutis stato   mostra se il sistema è attivo
  python -m protezione_acutis prova   dimostrazione completa su dati inventati
  python -m protezione_acutis prova-hello
                                      prova con l'impronta vera (Windows Hello),
                                      solo in memoria e su dati inventati
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="protezione_acutis")
    sotto = parser.add_subparsers(dest="comando", required=True)
    sotto.add_parser("stato")
    sotto.add_parser("prova")
    sotto.add_parser("prova-hello")
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
