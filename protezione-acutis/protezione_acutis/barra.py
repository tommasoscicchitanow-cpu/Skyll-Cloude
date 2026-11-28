"""Segnali sul pulsante della barra delle applicazioni di Windows.

Quando l'app è fissata alla barra, Windows mostra sempre l'icona del
collegamento e ignora quella della finestra: per questo lo stato si segnala
con le funzioni apposite della barra (ITaskbarList3), che funzionano anche
sui pulsanti fissati:

* un piccolo lucchetto sovrapposto all'angolo dell'icona (verde chiuso o
  rosso aperto);
* da aperta, il pulsante lampeggia di rosso finché tutto non è chiuso.

Su sistemi diversi da Windows tutto diventa un'operazione nulla.
"""

from __future__ import annotations

import ctypes
import os
import uuid
from pathlib import Path

CLSID_TASKBARLIST = "56FDF344-FD6D-11D0-958A-006097C9A090"
IID_ITASKBARLIST3 = "EA1AFB91-9E28-4B86-90E9-9E9F8A5EEFAF"
TBPF_NOPROGRESS, TBPF_ERROR = 0, 4
# posizioni dei metodi nella tabella virtuale di ITaskbarList3
_HRINIT, _SETPROGRESSVALUE, _SETPROGRESSSTATE, _SETOVERLAYICON = 3, 9, 10, 18


class _GUID(ctypes.Structure):
    _fields_ = [("a", ctypes.c_ubyte * 16)]

    @classmethod
    def da(cls, testo: str) -> "_GUID":
        return cls.from_buffer_copy(uuid.UUID(testo).bytes_le)


class BarraWindows:
    """Pulsante della finestra ``hwnd`` sulla barra delle applicazioni."""

    def __init__(self, hwnd: int, icone: dict[str, Path]):
        from ctypes import wintypes

        self._wt = wintypes
        self.hwnd = wintypes.HWND(hwnd)
        ole32 = ctypes.OleDLL("ole32")
        try:
            ole32.CoInitialize(None)
        except OSError:
            pass  # COM già inizializzato in altro modo: va bene lo stesso
        self._p = ctypes.c_void_p()
        clsid, iid = _GUID.da(CLSID_TASKBARLIST), _GUID.da(IID_ITASKBARLIST3)
        ole32.CoCreateInstance(ctypes.byref(clsid), None, 1, ctypes.byref(iid), ctypes.byref(self._p))
        self._metodo(_HRINIT)()
        user32 = ctypes.windll.user32
        user32.LoadImageW.restype = wintypes.HANDLE
        user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, ctypes.c_uint,
                                      ctypes.c_int, ctypes.c_int, ctypes.c_uint]
        lato = user32.GetSystemMetrics(49) or 16  # SM_CXSMICON
        self._hicon = {nome: user32.LoadImageW(None, str(percorso), 1, lato, lato, 0x10)
                       for nome, percorso in icone.items()}

    def _metodo(self, indice: int, *tipi):
        tabella = ctypes.cast(self._p, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        prototipo = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, *tipi)
        funzione = prototipo(tabella[indice])
        return lambda *argomenti: funzione(self._p, *argomenti)

    def sovrapponi(self, nome: str | None, descrizione: str = "") -> None:
        wt = self._wt
        self._metodo(_SETOVERLAYICON, wt.HWND, wt.HICON, wt.LPCWSTR)(
            self.hwnd, self._hicon.get(nome) if nome else None, descrizione)

    def rosso(self, acceso: bool) -> None:
        wt = self._wt
        if acceso:
            self._metodo(_SETPROGRESSVALUE, wt.HWND, ctypes.c_ulonglong, ctypes.c_ulonglong)(
                self.hwnd, 100, 100)
        self._metodo(_SETPROGRESSSTATE, wt.HWND, ctypes.c_int)(
            self.hwnd, TBPF_ERROR if acceso else TBPF_NOPROGRESS)


class BarraNulla:
    def sovrapponi(self, nome, descrizione=""):
        pass

    def rosso(self, acceso):
        pass


def crea_barra(finestra, cartella_icone: Path):
    """Restituisce l'oggetto per la barra, o uno nullo se non si può."""
    if os.name != "nt":
        return BarraNulla()
    try:
        from .icona import ico

        cartella_icone.mkdir(parents=True, exist_ok=True)
        icone = {}
        for nome in ("aperta", "verde"):
            percorso = cartella_icone / f"cassaforte-{nome}.ico"
            dati = ico((16, 20, 24, 32), variante=nome)
            if not percorso.exists() or percorso.read_bytes() != dati:
                percorso.write_bytes(dati)
            icone[nome] = percorso
        hwnd = int(finestra.wm_frame(), 16)
        return BarraWindows(hwnd, icone)
    except Exception:  # noqa: BLE001 la barra è un di più: mai bloccare l'app
        return BarraNulla()
