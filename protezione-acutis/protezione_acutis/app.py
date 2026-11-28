"""App "Cassaforte": finestra per lavorare sui progetti protetti.

Avvio: ``pythonw -m protezione_acutis app`` (lo fa il collegamento con
l'icona sul Desktop e nel menu Start).

Per ogni progetto: "Apri per lavorare" (frase + impronta, estrae tutto nella
cartella di lavoro e la apre), "Chiudi e proteggi" (frase + impronta, riporta
nell'archivio nuovi e modificati, verifica SHA-256, poi sovrascrive e cancella
la cartella di lavoro). La finestra non mostra mai nomi di file, solo
conteggi, e non scrive log.
"""

from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from .archivio import Archivio
from .biometria import BiometriaNegata
from .cripto import ErroreDecifratura, ErroreFormato, FraseDebole, LUNGHEZZA_MINIMA_FRASE
from .lavoro import (
    LavoroGiaAperto,
    NessunLavoroAperto,
    apri_lavoro,
    chiudi_lavoro,
    conta_cancellati,
)
from .barra import BarraNulla, crea_barra
from .progetti import ErroreProgetto, Progetto, Registro

# Ogni quanto ricordare, con una finestrella in primo piano, che la cassaforte
# è ancora aperta (secondi).
PROMEMORIA_OGNI = 30 * 60
LAMPEGGIO_MS = 900
AVVISO_PERICOLO = ("\u26a0  CASSAFORTE APERTA: finché resta aperta c'è rischio di fuga di "
                   "notizie. Chiudi e proteggi appena hai finito.")

TITOLO = "Cassaforte"

# colori
BLU = "#182B48"
BLU_CHIARO = "#24406A"
ORO = "#E8B04B"
CARTA = "#F6F4EF"
TESTO = "#1D1D1F"
GRIGIO = "#6B6B70"
VERDE = "#2E7D4F"
ARANCIO = "#C25E00"

STATI = {
    "chiuso": ("Protetto", VERDE, "Archivio chiuso e cifrato. Nessuna copia in chiaro."),
    "aperto": ("Aperto per lavorare", ARANCIO,
               "I file sono IN CHIARO nella cartella di lavoro. "
               "Quando hai finito premi «Chiudi e proteggi»."),
    "assente": ("Disco non collegato", GRIGIO, "Collega il disco esterno per usare questo progetto."),
}


BREVI = {"chiuso": "Protetto", "aperto": "APERTO", "assente": "Scollegato"}


def fattore_reale(progetto: Progetto):
    """Restituisce (fattore, testo da mostrare) per il progetto."""
    if progetto.fattore == "passkey":
        from .passkey import BiometriaPasskey

        return BiometriaPasskey(), "Conferma con l'impronta sul telefono…"
    from .windows_hello import BiometriaWindowsHello

    return BiometriaWindowsHello(nome_chiave=progetto.chiave_hello), "Conferma con Windows Hello…"


def messaggio_errore(errore: BaseException) -> str:
    """Testo per l'utente. Mai il testo grezzo di un errore di sistema, che
    potrebbe contenere il nome di un file."""
    if isinstance(errore, ErroreDecifratura):
        return "Frase o impronta non corrette. Nessun file è stato toccato."
    if isinstance(errore, ErroreFormato):
        return "L'archivio non è riconosciuto o è danneggiato. Nessun file è stato toccato."
    if isinstance(errore, (BiometriaNegata, FraseDebole, ErroreProgetto,
                           LavoroGiaAperto, NessunLavoroAperto)):
        return str(errore)
    from .attivazione import SistemaDisattivato

    if isinstance(errore, SistemaDisattivato):
        return str(errore)
    if isinstance(errore, PermissionError):
        return ("Accesso negato a un file o a una cartella: forse è aperto in un altro "
                "programma. Chiudilo e riprova.")
    if isinstance(errore, OSError):
        return ("Errore di lettura o scrittura sul disco. Controlla che il disco esterno "
                f"sia collegato e riprova. (codice {errore.errno})")
    return f"Errore imprevisto ({type(errore).__name__}). Nessun file è stato cancellato."


class AppCassaforte:
    def __init__(self, radice: Path | None = None, crea_fattore=fattore_reale,
                 opzioni_apri: dict | None = None, opzioni_crea: dict | None = None,
                 finestra: tk.Tk | None = None):
        self.registro = Registro.carica(radice)
        self.crea_fattore = crea_fattore
        self.opzioni_apri = opzioni_apri or {}
        self.opzioni_crea = opzioni_crea or {}
        self.coda: queue.Queue = queue.Queue()
        self.occupato = False
        self._risposta: dict = {}

        self.finestra = finestra or tk.Tk()
        self._attese: dict = {}
        self.barra_win = BarraNulla()
        self._aperta_da: float | None = None
        self._fase = False
        self._costruisci()
        self.aggiorna_elenco()
        self._attese.update({"ascolta": self.finestra.after(100, self._ascolta),
                             "ricontrolla": self.finestra.after(3000, self._ricontrolla),
                             "barra": self.finestra.after(600, self._collega_barra)})

    # -- interfacce sostituibili nelle prove -------------------------------
    def avvisa(self, titolo: str, testo: str, tipo: str = "info") -> None:
        {"info": messagebox.showinfo, "attenzione": messagebox.showwarning,
         "errore": messagebox.showerror}[tipo](titolo, testo, parent=self.finestra)

    def chiedi(self, titolo: str, testo: str) -> bool:
        return messagebox.askyesno(titolo, testo, parent=self.finestra, default="no")

    def chiedi_tre(self, titolo: str, testo: str):
        return messagebox.askyesnocancel(titolo, testo, parent=self.finestra)

    def mostra_cartella(self, cartella: Path) -> None:
        if os.name == "nt":
            os.startfile(str(cartella))  # noqa: S606 (solo Windows)

    # -- costruzione ---------------------------------------------------------
    def _costruisci(self) -> None:
        f = self.finestra
        f.title(TITOLO)
        f.configure(bg=CARTA)
        f.minsize(780, 560)
        f.geometry("900x590")
        self._icone = self._prepara_icone()
        self._icona_attuale = None
        f.protocol("WM_DELETE_WINDOW", self.chiudi_finestra)

        famiglia = "Segoe UI" if os.name == "nt" else "DejaVu Sans"
        self.font = (famiglia, 10)
        stile = ttk.Style(f)
        stile.theme_use("clam")
        stile.configure(".", font=self.font, background=CARTA, foreground=TESTO)
        stile.configure("Treeview", rowheight=30, fieldbackground="white", background="white")
        stile.configure("Treeview.Heading", font=(famiglia, 10, "bold"))
        stile.map("Treeview", background=[("selected", BLU_CHIARO)], foreground=[("selected", "white")])
        stile.configure("Primario.TButton", font=(famiglia, 11, "bold"), padding=(14, 8),
                        background=BLU, foreground="white")
        stile.map("Primario.TButton", background=[("disabled", "#B8BCC6"), ("active", BLU_CHIARO)])
        stile.configure("TButton", padding=(10, 6))
        stile.configure("Horizontal.TProgressbar", background=ORO, troughcolor="#E4E1D8")

        testata = tk.Frame(f, bg=BLU, height=64)
        testata.pack(fill="x")
        # fascia di pericolo, visibile solo quando qualcosa è aperto
        self.fascia = tk.Label(f, text=AVVISO_PERICOLO, bg="#D32027", fg="white",
                               font=(famiglia, 11, "bold"), pady=6, wraplength=840)
        tk.Label(testata, text=TITOLO,
                 bg=BLU, fg=ORO, font=(famiglia, 18, "bold")).pack(side="left", padx=18, pady=12)
        tk.Label(testata, text="Progetti protetti da frase segreta e impronta", bg=BLU,
                 fg="#C9D3E3", font=(famiglia, 10)).pack(side="left", pady=(8, 0))

        corpo = tk.Frame(f, bg=CARTA)
        corpo.pack(fill="both", expand=True, padx=16, pady=12)

        sinistra = tk.Frame(corpo, bg=CARTA)
        sinistra.pack(side="left", fill="y")
        tk.Label(sinistra, text="Progetti", bg=CARTA, fg=GRIGIO,
                 font=(famiglia, 9, "bold")).pack(anchor="w")
        self.elenco = ttk.Treeview(sinistra, columns=("stato",), show="tree headings",
                                   selectmode="browse", height=10)
        self.elenco.heading("#0", text="Nome")
        self.elenco.heading("stato", text="Stato")
        self.elenco.column("#0", width=170)
        self.elenco.column("stato", width=100)
        self.elenco.tag_configure("aperto", foreground=ARANCIO)
        self.elenco.tag_configure("chiuso", foreground=VERDE)
        self.elenco.tag_configure("assente", foreground=GRIGIO)
        self.elenco.pack(fill="y", expand=True, pady=(4, 8))
        self.elenco.bind("<<TreeviewSelect>>", lambda e: self._mostra_dettaglio())
        riga = tk.Frame(sinistra, bg=CARTA)
        riga.pack(fill="x")
        self.pulsante_nuovo = ttk.Button(riga, text="Nuovo progetto…", command=self.finestra_nuovo)
        self.pulsante_nuovo.pack(side="left")
        self.pulsante_recupero = ttk.Button(riga, text="Chiave di recupero…",
                                            command=self.azione_chiave_recupero)
        self.pulsante_recupero.pack(side="left", padx=(6, 0))

        destra = tk.Frame(corpo, bg="white", highlightbackground="#E0DDD4", highlightthickness=1)
        destra.pack(side="left", fill="both", expand=True, padx=(16, 0))
        interno = tk.Frame(destra, bg="white")
        interno.pack(fill="both", expand=True, padx=22, pady=18)

        self.etichetta_nome = tk.Label(interno, text="", bg="white", fg=TESTO,
                                       font=(famiglia, 16, "bold"), anchor="w")
        self.etichetta_nome.pack(fill="x")
        self.etichetta_stato = tk.Label(interno, text="", bg=VERDE, fg="white",
                                        font=(famiglia, 10, "bold"), padx=10, pady=3)
        self.etichetta_stato.pack(anchor="w", pady=(6, 4))
        self.spiegazione = tk.Label(interno, text="", bg="white", fg=GRIGIO, justify="left",
                                    anchor="w", wraplength=440)
        self.spiegazione.pack(fill="x", pady=(0, 14))

        tk.Label(interno, text="Frase segreta", bg="white", fg=TESTO,
                 font=(famiglia, 10, "bold")).pack(anchor="w")
        self.campo_frase = ttk.Entry(interno, show="*", width=48, font=(famiglia, 12))
        self.campo_frase.pack(anchor="w", fill="x", pady=(4, 2), ipady=3)
        self.campo_frase.bind("<Return>", lambda e: self._invio())
        tk.Label(interno, text="Dopo la frase ti verrà chiesta l'impronta.", bg="white",
                 fg=GRIGIO, font=(famiglia, 9)).pack(anchor="w", pady=(0, 12))

        pulsanti = tk.Frame(interno, bg="white")
        pulsanti.pack(anchor="w")
        self.pulsante_apri = ttk.Button(pulsanti, text="Apri per lavorare", style="Primario.TButton",
                                        command=self.azione_apri)
        self.pulsante_apri.pack(side="left")
        self.pulsante_chiudi = ttk.Button(pulsanti, text="Chiudi e proteggi", style="Primario.TButton",
                                          command=self.azione_chiudi)
        self.pulsante_chiudi.pack(side="left", padx=(8, 0))
        self.pulsante_cartella = ttk.Button(interno, text="Mostra la cartella di lavoro",
                                            command=self.azione_mostra)
        self.pulsante_cartella.pack(anchor="w", pady=(8, 0))

        self.barra = ttk.Progressbar(interno, mode="determinate", length=440)
        self.barra.pack(anchor="w", fill="x", pady=(16, 4))
        self.messaggio = tk.Label(interno, text="", bg="white", fg=TESTO, anchor="w",
                                  justify="left", wraplength=440)
        self.messaggio.pack(fill="x")

    # -- elenco e stato --------------------------------------------------------
    def progetto_scelto(self) -> Progetto | None:
        scelta = self.elenco.selection()
        if not scelta:
            return None
        try:
            return self.registro.trova(scelta[0])
        except ErroreProgetto:
            return None

    def seleziona(self, nome: str) -> None:
        self.elenco.selection_set(nome)
        self.elenco.focus(nome)
        self._mostra_dettaglio()

    def _prepara_icone(self) -> dict:
        """Icone della barra delle applicazioni: lucchetto chiuso (tutto
        protetto) o aperto (almeno un progetto aperto). Si disegnano una
        volta sola all'avvio."""
        import base64

        from .icona import png

        icone = {}
        for aperta in (False, True):
            try:
                icone[aperta] = [tk.PhotoImage(master=self.finestra,
                                               data=base64.b64encode(png(lato, aperta)))
                                 for lato in (48, 32, 16)]
            except tk.TclError:
                return {}
        return icone

    def stato_generale(self) -> str:
        """"aperta" se almeno un progetto è aperto, altrimenti "chiusa"."""
        return "aperta" if any(p.stato() == "aperto" for p in self.registro.progetti) else "chiusa"

    def _collega_barra(self) -> None:
        self.barra_win = crea_barra(self.finestra, Path(__file__).resolve().parent.parent)
        self._icona_attuale = None
        self._aggiorna_icona()

    def _aggiorna_icona(self) -> None:
        """Segnala lo stato generale: icona della finestra, piccolo lucchetto
        sul pulsante della barra, fascia rossa e lampeggio finché è aperta."""
        stato = self.stato_generale()
        if stato == self._icona_attuale:
            return
        self._icona_attuale = stato
        if self._icone:
            self.finestra.iconphoto(True, *self._icone[stato == "aperta"])
        if stato == "aperta":
            import time

            self._aperta_da = time.monotonic()
            self._ultimo_promemoria = self._aperta_da
            self.barra_win.sovrapponi("aperta", "Cassaforte aperta: rischio fuga di notizie")
            self.fascia.pack(fill="x", after=self.fascia.master.winfo_children()[0])
            self._mostra_striscia()
            self._lampeggia()
        else:
            self._aperta_da = None
            attesa = self._attese.pop("lampeggio", None)
            if attesa:
                self.finestra.after_cancel(attesa)
            self.barra_win.rosso(False)
            self.barra_win.sovrapponi("verde", "Cassaforte: tutto chiuso e protetto")
            self.fascia.pack_forget()
            if getattr(self, "striscia", None) is not None:
                self.striscia.withdraw()
            self.finestra.title(f"{TITOLO} (tutto chiuso)")

    def _lampeggia(self) -> None:
        """Animazione di pericolo: costa una chiamata al secondo circa."""
        if self._aperta_da is None:
            return
        import time

        self._fase = not self._fase
        aperti = sum(1 for p in self.registro.progetti if p.stato() == "aperto") or 1
        self.barra_win.rosso(self._fase)
        colore = "#D32027" if self._fase else "#8E0F14"
        self.fascia.config(bg=colore)
        if getattr(self, "striscia", None) is not None:
            self.striscia.config(bg=colore)
            for figlio in self.striscia.winfo_children():
                figlio.config(bg=colore)
            self.striscia.lift()
        self.finestra.title(
            f"\u26a0 CASSAFORTE APERTA ({aperti})" if self._fase else "\u26a0 Rischio fuga di notizie")
        adesso = time.monotonic()
        if adesso - self._ultimo_promemoria >= PROMEMORIA_OGNI:
            self._ultimo_promemoria = adesso
            self._promemoria(int((adesso - self._aperta_da) // 60))
        self._attese["lampeggio"] = self.finestra.after(LAMPEGGIO_MS, self._lampeggia)

    def _area_di_lavoro(self) -> tuple[int, int, int, int]:
        """Schermo senza la barra delle applicazioni: (sinistra, alto, destra, basso)."""
        if os.name == "nt":
            try:
                import ctypes
                from ctypes import wintypes

                r = wintypes.RECT()
                if ctypes.windll.user32.SystemParametersInfoW(0x30, 0, ctypes.byref(r), 0):
                    return r.left, r.top, r.right, r.bottom
            except Exception:  # noqa: BLE001
                pass
        return 0, 0, self.finestra.winfo_screenwidth(), self.finestra.winfo_screenheight() - 48

    def _mostra_striscia(self) -> None:
        """Striscia rossa sempre in primo piano appoggiata sopra la barra delle
        applicazioni, in basso a destra: si vede anche con l'app ridotta a
        icona o sotto altre finestre. Un clic riporta alla Cassaforte."""
        if getattr(self, "striscia", None) is None:
            s = tk.Toplevel(self.finestra, bg="#D32027", cursor="hand2")
            s.overrideredirect(True)
            s.attributes("-topmost", True)
            tk.Label(s, text="\u26a0  CASSAFORTE APERTA", bg="#D32027", fg="white",
                     font=(self.font[0], 13, "bold")).pack(padx=16, pady=(6, 0), anchor="w")
            tk.Label(s, text="Rischio fuga di notizie. Clic qui per chiudere e proteggere.",
                     bg="#D32027", fg="white", font=(self.font[0], 9)).pack(
                         padx=16, pady=(0, 7), anchor="w")
            for w in (s, *s.winfo_children()):
                w.bind("<Button-1>", lambda e: self._torna_alla_finestra())
            self.striscia = s
        s = self.striscia
        s.deiconify()
        s.update_idletasks()
        _, _, destra, basso = self._area_di_lavoro()
        larghezza, altezza = max(s.winfo_reqwidth(), 420), s.winfo_reqheight()
        s.geometry(f"{larghezza}x{altezza}+{destra - larghezza - 12}+{basso - altezza - 8}")
        s.lift()

    def _torna_alla_finestra(self) -> None:
        self.finestra.deiconify()
        self.finestra.lift()
        aperti = self.registro.aperti()
        if aperti:
            self.seleziona(aperti[0].nome)
        self.campo_frase.focus_force()

    def _promemoria(self, minuti: int) -> None:
        """Finestrella in primo piano: la cassaforte è aperta da tanto."""
        vecchia = getattr(self, "finestra_promemoria", None)
        if vecchia is not None and vecchia.winfo_exists():
            vecchia.destroy()
        w = tk.Toplevel(self.finestra, bg="#D32027")
        w.title("Cassaforte aperta")
        w.attributes("-topmost", True)
        tk.Label(w, text=f"\u26a0  La cassaforte è aperta da {minuti} minuti.", bg="#D32027",
                 fg="white", font=(self.font[0], 13, "bold")).pack(padx=24, pady=(18, 6))
        tk.Label(w, text="Finché resta aperta i file sono in chiaro: c'è rischio di fuga di "
                 "notizie.", bg="#D32027", fg="white", wraplength=380).pack(padx=24)
        riga = tk.Frame(w, bg="#D32027")
        riga.pack(pady=16)

        def chiudi_ora():
            w.destroy()
            self._torna_alla_finestra()

        ttk.Button(riga, text="Chiudi e proteggi ora", command=chiudi_ora).pack(side="left")
        ttk.Button(riga, text="Più tardi", command=w.destroy).pack(side="left", padx=8)
        if os.name == "nt":
            try:
                import ctypes

                ctypes.windll.user32.FlashWindow(int(self.finestra.wm_frame(), 16), True)
            except Exception:  # noqa: BLE001
                pass
        self.finestra_promemoria = w

    def aggiorna_elenco(self) -> None:
        scelto = self.elenco.selection()
        self.elenco.delete(*self.elenco.get_children())
        for p in self.registro.progetti:
            stato = p.stato()
            self.elenco.insert("", "end", iid=p.nome, text=p.nome,
                               values=(BREVI[stato],), tags=(stato,))
        if scelto and self.elenco.exists(scelto[0]):
            self.elenco.selection_set(scelto[0])
        elif self.registro.progetti:
            self.elenco.selection_set(self.registro.progetti[0].nome)
        self._mostra_dettaglio()
        self._aggiorna_icona()

    def _mostra_dettaglio(self) -> None:
        p = self.progetto_scelto()
        if p is None:
            self.etichetta_nome.config(text="Nessun progetto")
            self.etichetta_stato.config(text="", bg="white")
            self.spiegazione.config(text="Premi «Nuovo progetto» per crearne uno.")
            for b in (self.pulsante_apri, self.pulsante_chiudi, self.pulsante_cartella,
                      self.pulsante_recupero):
                b.state(["disabled"])
            self.pulsante_nuovo.state(["disabled"] if self.occupato else ["!disabled"])
            return
        stato = p.stato()
        titolo, colore, testo = STATI[stato]
        self.etichetta_nome.config(text=p.nome)
        self.etichetta_stato.config(text=titolo, bg=colore)
        self.spiegazione.config(text=testo)
        abilita = {
            self.pulsante_apri: stato == "chiuso",
            self.pulsante_chiudi: stato == "aperto",
            self.pulsante_cartella: stato == "aperto",
            self.pulsante_recupero: stato != "assente",
            self.pulsante_nuovo: True,
        }
        for pulsante, attivo in abilita.items():
            pulsante.state(["!disabled"] if attivo and not self.occupato else ["disabled"])
        self.campo_frase.state(["disabled"] if self.occupato or stato == "assente" else ["!disabled"])

    def _ricontrolla(self) -> None:
        if not self.occupato:
            stati = {p.nome: p.stato() for p in self.registro.progetti}
            if stati != getattr(self, "_stati_precedenti", None):
                self._stati_precedenti = stati
                self.aggiorna_elenco()
        self._attese["ricontrolla"] = self.finestra.after(3000, self._ricontrolla)

    def _invio(self) -> None:
        p = self.progetto_scelto()
        if p and p.stato() == "chiuso":
            self.azione_apri()
        elif p and p.stato() == "aperto":
            self.azione_chiudi()

    def _prendi_frase(self) -> str | None:
        frase = self.campo_frase.get()
        self.campo_frase.delete(0, "end")
        if not frase:
            self.avvisa(TITOLO, "Scrivi prima la frase segreta.", "attenzione")
            self.campo_frase.focus_set()
            return None
        return frase

    # -- lavori in sottofondo --------------------------------------------------
    def _avvia(self, descrizione: str, lavoro, al_termine) -> None:
        """Esegue ``lavoro(invia, domanda)`` in un thread; ``al_termine(esito)``
        gira nella finestra. Il thread non deve toccare oggetti della finestra
        (tkinter non lo permette): riceve solo ``invia`` e ``domanda``."""
        self.occupato = True
        self._al_termine = al_termine
        self.barra.config(value=0, maximum=1)
        self._scrivi(descrizione)
        self._mostra_dettaglio()
        coda, risposte = self.coda, self._risposta

        def invia(*messaggio):
            coda.put(messaggio)

        def domanda(titolo: str, testo: str) -> bool:
            evento = threading.Event()
            coda.put(("domanda", titolo, testo, evento))
            evento.wait()
            return risposte.pop(evento)

        def esegui():
            try:
                coda.put(("fine", lavoro(invia, domanda), None))
            except BaseException as errore:  # noqa: BLE001
                coda.put(("fine", None, errore))

        threading.Thread(target=esegui, daemon=True).start()

    def _ascolta(self) -> None:
        try:
            while True:
                messaggio = self.coda.get_nowait()
                tipo = messaggio[0]
                if tipo == "testo":
                    self._scrivi(messaggio[1])
                elif tipo == "avanzamento":
                    fatti, totale = messaggio[1], messaggio[2]
                    self.barra.config(maximum=max(totale, 1), value=fatti)
                    self._scrivi(f"{messaggio[3]} {fatti} di {totale}…")
                elif tipo == "domanda":
                    _, titolo, testo, evento = messaggio
                    self._risposta[evento] = self.chiedi(titolo, testo)
                    evento.set()
                elif tipo == "fine":
                    _, esito, errore = messaggio
                    al_termine, self._al_termine = self._al_termine, None
                    self.occupato = False
                    self.barra.config(value=0)
                    self.registro = Registro.carica(self.registro.radice)
                    self.aggiorna_elenco()
                    if errore is not None:
                        self._scrivi("")
                        self.avvisa(TITOLO, messaggio_errore(errore), "errore")
                    else:
                        al_termine(esito)
        except queue.Empty:
            pass
        self._attese["ascolta"] = self.finestra.after(100, self._ascolta)

    def _scrivi(self, testo: str) -> None:
        self.messaggio.config(text=testo)

    # -- azioni ------------------------------------------------------------------
    def azione_apri(self) -> None:
        p = self.progetto_scelto()
        if not p or self.occupato or p.stato() != "chiuso":
            return
        frase = self._prendi_frase()
        if frase is None:
            return
        fattore, istruzione = self.crea_fattore(p)
        opzioni = dict(self.opzioni_apri)

        def lavoro(invia, domanda):
            with Archivio.apri(p.cartella_archivio, frase, fattore, **opzioni) as a:
                invia("testo", "Estrazione dei file nella cartella di lavoro…")
                return apri_lavoro(a, p.cartella_lavoro,
                                   avanzamento=lambda f, t: invia("avanzamento", f, t, "File"))

        def fine(esito):
            self._scrivi(f"Aperto: {esito['estratti']} file nella cartella di lavoro.")
            self.mostra_cartella(p.cartella_lavoro)

        self._avvia(istruzione, lavoro, fine)

    def azione_chiudi(self) -> None:
        p = self.progetto_scelto()
        if not p or self.occupato or p.stato() != "aperto":
            return
        frase = self._prendi_frase()
        if frase is None:
            return
        fattore, istruzione = self.crea_fattore(p)
        opzioni = dict(self.opzioni_apri)

        def lavoro(invia, domanda):
            with Archivio.apri(p.cartella_archivio, frase, fattore, **opzioni) as a:
                rimuovi = False
                cancellati = conta_cancellati(a, p.cartella_lavoro)
                if cancellati:
                    rimuovi = domanda(
                        TITOLO,
                        f"{cancellati} file dell'archivio non ci sono più nella cartella di "
                        "lavoro.\n\nVuoi toglierli anche dall'archivio?\n\n"
                        "Sì: vengono tolti per sempre.\nNo (consigliato se hai dubbi): "
                        "restano nell'archivio.")
                invia("testo", "Salvataggio nell'archivio e verifica…")
                return chiudi_lavoro(a, p.cartella_lavoro, rimuovi_cancellati=rimuovi,
                                     avanzamento=lambda f, t: invia("avanzamento", f, t, "Controllati"))

        self._avvia(istruzione, lavoro, self._esito_chiusura)

    def _esito_chiusura(self, e: dict) -> None:
        if e["errori"] or e["verifica_fallita"]:
            self._scrivi("")
            self.avvisa(TITOLO,
                        f"La verifica non è riuscita su {e['errori'] + e['verifica_fallita']} file: "
                        "la cartella di lavoro NON è stata cancellata e resta aperta.\n\n"
                        "Chiudi i programmi che usano quei file e premi di nuovo "
                        "«Chiudi e proteggi».", "errore")
            return
        if e["non_cancellabili"]:
            self._scrivi("")
            self.avvisa(TITOLO,
                        "Il lavoro è salvato e verificato nell'archivio, ma "
                        f"{e['non_cancellabili']} file sono ancora aperti in un altro programma "
                        "(per esempio Word) e non si possono cancellare.\n\n"
                        "Chiudi quel programma e premi di nuovo «Chiudi e proteggi».",
                        "attenzione")
            return
        if e["ripresa"]:
            riepilogo = "Pulizia completata: la cartella di lavoro è stata distrutta."
        else:
            cancellati = (f"tolti dall'archivio {e['cancellati_rimossi']}" if e["cancellati_rimossi"]
                          else f"cancellati ma conservati nell'archivio {e['cancellati']}")
            riepilogo = (f"Protetto. Nuovi {e['nuovi']}, modificati {e['modificati']}, "
                         f"invariati {e['invariati']}, {cancellati}. "
                         f"Verificati con SHA-256: {e['verificati']}. "
                         "Cartella di lavoro sovrascritta e cancellata.")
        self._scrivi(riepilogo)

    def azione_mostra(self) -> None:
        p = self.progetto_scelto()
        if p and p.stato() == "aperto":
            self.mostra_cartella(p.cartella_lavoro)

    def azione_chiave_recupero(self) -> None:
        p = self.progetto_scelto()
        if not p or self.occupato or p.stato() == "assente":
            return
        if not self.chiedi(
            TITOLO,
            "Verrà creata una NUOVA chiave di recupero per questo progetto e mostrata sullo "
            "schermo, da scrivere a mano su carta.\n\nAttenzione: la chiave di recupero "
            "precedente (se c'è) smetterà di funzionare.\n\nControlla che nessuno veda lo "
            "schermo. Continuare?"):
            return
        frase = self._prendi_frase()
        if frase is None:
            return
        fattore, istruzione = self.crea_fattore(p)
        opzioni = dict(self.opzioni_apri)

        def lavoro(invia, domanda):
            with Archivio.apri(p.cartella_archivio, frase, fattore, **opzioni) as a:
                return a.crea_chiave_recupero(frase)

        self._avvia(istruzione, lavoro, self._mostra_chiave)

    def _mostra_chiave(self, chiave: str) -> None:
        self._scrivi("")
        finestra = tk.Toplevel(self.finestra, bg="white")
        finestra.title("Chiave di recupero")
        finestra.transient(self.finestra)
        finestra.grab_set()
        tk.Label(finestra, text="Scrivi questa chiave a mano su carta.\nNon fotografarla, "
                 "non copiarla nel PC, nel telefono o in chat.", bg="white", fg=TESTO,
                 justify="left").pack(padx=24, pady=(20, 10), anchor="w")
        tk.Label(finestra, text=chiave, bg="#FFF8E6", fg=TESTO, font=("Consolas", 15, "bold"),
                 padx=14, pady=12, wraplength=520).pack(padx=24)
        tk.Label(finestra, text="Con questa chiave e la frase si riapre il progetto anche se "
                 "l'impronta non funziona più.", bg="white", fg=GRIGIO,
                 wraplength=520, justify="left").pack(padx=24, pady=10, anchor="w")
        ttk.Button(finestra, text="L'ho trascritta e ricontrollata",
                   command=finestra.destroy).pack(pady=(0, 20))
        self.finestra_chiave = finestra

    def finestra_nuovo(self) -> None:
        if self.occupato:
            return
        d = tk.Toplevel(self.finestra, bg="white")
        d.title("Nuovo progetto")
        d.transient(self.finestra)
        d.grab_set()
        d.resizable(False, False)
        campi = {}
        for chiave, testo, nascosto in (("nome", "Nome del progetto", False),
                                        ("frase", "Frase segreta", True),
                                        ("ripeti", "Ripeti la frase", True)):
            tk.Label(d, text=testo, bg="white", font=(self.font[0], 10, "bold")).pack(
                anchor="w", padx=22, pady=(14 if chiave == "nome" else 8, 2))
            campo = ttk.Entry(d, width=44, show="*" if nascosto else "", font=(self.font[0], 11))
            campo.pack(padx=22, anchor="w")
            campi[chiave] = campo
        tk.Label(d, text=f"Almeno {LUNGHEZZA_MINIMA_FRASE} caratteri. Scegli un nome che non "
                 "riveli il contenuto.", bg="white", fg=GRIGIO, wraplength=380,
                 justify="left").pack(anchor="w", padx=22, pady=(6, 8))
        scelta = tk.StringVar(value="hello")
        for valore, testo in (("hello", "Impronta su questo PC (Windows Hello)"),
                              ("passkey", "Impronta sul telefono (passkey)")):
            ttk.Radiobutton(d, text=testo, value=valore, variable=scelta).pack(anchor="w", padx=22)

        def crea():
            nome, frase = campi["nome"].get().strip(), campi["frase"].get()
            if frase != campi["ripeti"].get():
                self.avvisa("Nuovo progetto", "Le due frasi non coincidono.", "attenzione")
                return
            for c in campi.values():
                c.delete(0, "end")
            d.destroy()
            self.crea_progetto(nome, frase, scelta.get())

        riga = tk.Frame(d, bg="white")
        riga.pack(pady=16)
        ttk.Button(riga, text="Crea", style="Primario.TButton", command=crea).pack(side="left")
        ttk.Button(riga, text="Annulla", command=d.destroy).pack(side="left", padx=8)
        campi["nome"].focus_set()
        self.finestra_nuovo_progetto = (d, campi, scelta, crea)

    def crea_progetto(self, nome: str, frase: str, fattore: str) -> None:
        provvisorio = Progetto(nome, "", "", fattore)
        biometria, istruzione = self.crea_fattore(provvisorio)
        registro, opzioni = self.registro, dict(self.opzioni_crea)

        def lavoro(invia, domanda):
            return registro.nuovo(nome, frase, biometria, fattore=fattore, **opzioni)

        def fine(progetto):
            self.seleziona(progetto.nome)
            self._scrivi("Progetto creato. Premi «Apri per lavorare» e metti i file "
                         "nella cartella che si apre; alla fine «Chiudi e proteggi».")

        self._avvia(istruzione, lavoro, fine)

    # -- uscita --------------------------------------------------------------------
    def chiudi_finestra(self) -> None:
        if self.occupato:
            self.avvisa(TITOLO, "Attendi la fine dell'operazione in corso.", "attenzione")
            return
        aperti = self.registro.aperti()
        if aperti:
            risposta = self.chiedi_tre(
                TITOLO,
                f"Il progetto «{aperti[0].nome}» è ancora APERTO: i file sono in "
                "chiaro sul disco.\n\nVuoi chiuderlo e proteggerlo adesso?\n\n"
                "Sì: torna alla finestra per chiuderlo.\nNo: esci lasciandolo aperto.\n"
                "Annulla: resta qui.")
            if risposta is None or risposta:
                self.seleziona(aperti[0].nome)
                self.campo_frase.focus_set()
                return
        self.distruggi()

    def distruggi(self) -> None:
        for attesa in self._attese.values():
            try:
                self.finestra.after_cancel(attesa)
            except tk.TclError:
                pass
        self.finestra.destroy()


def _nitido_su_windows() -> None:
    if os.name == "nt":
        try:
            import ctypes

            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:  # noqa: BLE001
            pass


def avvia(radice: Path | None = None) -> int:
    _nitido_su_windows()
    app = AppCassaforte(radice)
    app.finestra.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(avvia())
