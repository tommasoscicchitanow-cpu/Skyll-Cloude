"""Icona dell'app (lucchetto dorato su fondo blu notte), disegnata in Python
puro: nessun file binario nel repository e nessuna libreria in più."""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

FONDO = (24, 43, 72)
ORO = (232, 176, 75)
CAMPIONI = 4  # sovracampionamento per bordi morbidi


def _rettangolo_arrotondato(x, y, x0, y0, x1, y1, r):
    cx = min(max(x, x0 + r), x1 - r)
    cy = min(max(y, y0 + r), y1 - r)
    return x0 <= x <= x1 and y0 <= y <= y1 and (x - cx) ** 2 + (y - cy) ** 2 <= r * r


ROSSO = (211, 32, 39)
VERDE = (34, 139, 34)
BIANCO = (255, 250, 240)
# variante -> (fondo, metallo, arco aperto)
VARIANTI = {
    "chiusa": (FONDO, ORO, False),   # icona normale: tutto protetto
    "aperta": (ROSSO, BIANCO, True),  # almeno un progetto aperto
    "aperta2": ((120, 10, 14), (255, 120, 120), True),  # seconda fase del lampeggio
    "verde": (VERDE, BIANCO, False),  # piccolo segnale "tutto chiuso"
}


def _colore(x: float, y: float, aperta: bool = False, variante: str | None = None):
    """Coordinate 0..1. Restituisce (r, g, b) o None (trasparente).
    Chiusa: lucchetto dorato su blu notte. Aperta: lucchetto bianco con
    l'arco sollevato su fondo arancione, ben distinguibile anche in piccolo."""
    fondo, metallo, aperta = VARIANTI[variante or ("aperta" if aperta else "chiusa")]
    if not _rettangolo_arrotondato(x, y, 0.02, 0.02, 0.98, 0.98, 0.2):
        return None
    # buco della serratura
    if (x - 0.5) ** 2 + (y - 0.64) ** 2 <= 0.065 ** 2 or (0.475 <= x <= 0.525 and 0.64 <= y <= 0.78):
        return fondo
    # corpo
    if _rettangolo_arrotondato(x, y, 0.22, 0.46, 0.78, 0.88, 0.07):
        return metallo
    # arco: anello tra raggio 0.15 e 0.23; da aperta è sollevato e la gamba
    # destra non entra nel corpo
    centro = 0.27 if aperta else 0.40
    d = math.hypot(x - 0.5, y - centro)
    if 0.15 <= d <= 0.23 and y <= centro:
        return metallo
    if 0.15 <= abs(x - 0.5) <= 0.23 and centro < y <= 0.48:
        if not aperta or x < 0.5 or y <= 0.34:
            return metallo
    return fondo


def pixel(lato: int, aperta: bool = False, variante: str | None = None) -> bytes:
    righe = bytearray()
    for py in range(lato):
        righe.append(0)  # filtro PNG "nessuno"
        for px in range(lato):
            somma = [0, 0, 0, 0]
            for sy in range(CAMPIONI):
                for sx in range(CAMPIONI):
                    c = _colore((px + (sx + 0.5) / CAMPIONI) / lato,
                                (py + (sy + 0.5) / CAMPIONI) / lato, aperta, variante)
                    if c:
                        somma[0] += c[0]
                        somma[1] += c[1]
                        somma[2] += c[2]
                        somma[3] += 1
            n = CAMPIONI * CAMPIONI
            if somma[3]:
                righe += bytes((somma[0] // somma[3], somma[1] // somma[3],
                                somma[2] // somma[3], 255 * somma[3] // n))
            else:
                righe += b"\0\0\0\0"
    return bytes(righe)


def png(lato: int, aperta: bool = False, variante: str | None = None) -> bytes:
    def blocco(tipo: bytes, dati: bytes) -> bytes:
        return struct.pack(">I", len(dati)) + tipo + dati + struct.pack(">I", zlib.crc32(tipo + dati))

    return (b"\x89PNG\r\n\x1a\n"
            + blocco(b"IHDR", struct.pack(">IIBBBBB", lato, lato, 8, 6, 0, 0, 0))
            + blocco(b"IDAT", zlib.compress(pixel(lato, aperta, variante), 9))
            + blocco(b"IEND", b""))


def ico(lati=(16, 24, 32, 48, 64, 256), variante: str = "chiusa") -> bytes:
    immagini = [png(l, variante=variante) for l in lati]
    testa = struct.pack("<HHH", 0, 1, len(lati))
    posizione = 6 + 16 * len(lati)
    voci = b""
    for lato, dati in zip(lati, immagini):
        voci += struct.pack("<BBBBHHII", lato % 256, lato % 256, 0, 0, 1, 32, len(dati), posizione)
        posizione += len(dati)
    return testa + voci + b"".join(immagini)


def scrivi_icona(percorso: Path) -> Path:
    percorso = Path(percorso)
    percorso.parent.mkdir(parents=True, exist_ok=True)
    percorso.write_bytes(ico())
    return percorso
