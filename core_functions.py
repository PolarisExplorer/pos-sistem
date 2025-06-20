import customtkinter as ctk
from config import SVJETLO_ZELENA, TAMNO_TIRKIZNA
from tkinter import messagebox
from database import dohvati_aktivne_racune, dohvati_stavke_racuna

class CoreFunctions:
    def __init__(self, app, db_conn):
        self.app = app
        self.db_conn = db_conn
        self.trenutni_racun_id = 1
        self.win = self

        # Fontovi
        self.FONT = ("Segoe UI", 16)
        self.FONT_BOLD = ("Segoe UI", 18, "bold")

        # Inicijalizacija ukupne vrednosti na 0 ako nije postavljena
        if not hasattr(self.app, 'ukupno'):
            self.app.ukupno = 0.0

        # Postavljanje osnovnih bindinga
        self.setup_basic_bindings()

        # Inicijalno osvježavanje računa
        self.osvjezi_trenutni_racun()
        self.focus_barkod_entry()

    def setup_basic_bindings(self):
        """Postavlja osnovne bindinge koji ne zavise od specifičnih modula."""
        self.app.barkod_entry.bind("<Return>", lambda event: None)
        self.app.naziv_entry.bind("<Return>", lambda event: None)
        self.app.sifra_entry.bind("<Return>", lambda event: None)
        self.app.novac_entry.bind("<Return>", lambda event: self.izracunaj_kusur())
        self.app.dodatno_entry.bind("<KeyRelease>", lambda event: self.izracunaj_ukupnu_cijenu())
        self.app.novac_entry.bind("<KeyRelease>", lambda event: self.izracunaj_kusur())
        print("CoreFunctions bindingi postavljeni, <Double-1> ostavljen slobodan.")

    def focus_barkod_entry(self):
        """Postavlja fokus na barkod polje."""
        self.app.barkod_entry.focus_set()

    def add_money(self, amount, currency):
        """Dodaje iznos u polje 'Novac od kupca' i konvertuje EUR u KM ako je potrebno."""
        try:
            current_amount = float(self.app.novac_var.get().replace(",", ".")) if self.app.novac_var.get() else 0.0
        except ValueError:
            current_amount = 0.0

        if currency == "EUR":
            amount = amount * 1.94  # Konverzija EUR u KM po tečaju 1,94

        new_amount = current_amount + amount
        self.app.novac_var.set(f"{new_amount:.2f}")
        self.izracunaj_kusur()

    def izracunaj_ukupnu_cijenu(self):
        """Izračunava ukupnu cijenu svih artikala u tabeli i dodaje vrednost 'Dodatno'."""
        ukupno_artikala = 0.0
        for item in self.app.tree.get_children():
            ukupna_cijena = float(self.app.tree.item(item, "values")[5].replace(" KM", ""))
            ukupno_artikala += ukupna_cijena
        
        try:
            dodatno = float(self.app.dodatno_var.get().replace(",", ".")) if self.app.dodatno_var.get() else 0.0
        except ValueError:
            dodatno = 0.0
        
        self.app.ukupno = ukupno_artikala + dodatno
        self.app.cijena_label.configure(text=f"{self.app.ukupno:.2f} KM")
        self.izracunaj_kusur()

    def izracunaj_kusur(self):
        """Izračunava i prikazuje kusur na osnovu unesenog novca od kupca."""
        try:
            novac_od_kupca = float(self.app.novac_var.get().replace(",", ".")) if self.app.novac_var.get() else 0.0
            kusur = novac_od_kupca - self.app.ukupno
            self.app.kusur_label.configure(text=f"{kusur:.2f} KM")
        except ValueError:
            self.app.kusur_label.configure(text="0,00 KM")

    def resetuj_sve(self, reset_dodatno=True):
        """Resetuje sva polja i vrednosti na početne vrednosti za novi račun."""
        self.app.tree.delete(*self.app.tree.get_children())
        self.app.ukupno = 0.0
        if reset_dodatno:
            self.app.dodatno_var.set("0,00")  # Resetuj polje "Dodatno" samo ako je eksplicitno traženo
        self.app.novac_var.set("")
        self.app.cijena_label.configure(text="0,00 KM")
        self.app.kusur_label.configure(text="0,00 KM")
        self.app.barkod_var.set("")
        self.app.naziv_var.set("")
        self.app.sifra_var.set("")

    def osvjezi_trenutni_racun(self):
        """Osvježava trenutni račun i prikazuje stavke u tabeli, resetujući sve vrednosti."""
        racuni = dohvati_aktivne_racune(self.db_conn)
        for racun in racuni:
            if racun[0] == self.trenutni_racun_id:
                self.app.trenutni_racun_label.configure(text=racun[1], fg_color=racun[2])
                break
        else:
            self.app.trenutni_racun_label.configure(text="Račun 1")

        # Resetuj sve vrednosti pre učitavanja novog računa, uključujući polje "Dodatno"
        self.resetuj_sve(reset_dodatno=True)  # Resetuj polje "Dodatno" na "0,00" prilikom promjene računa

        # Učitaj stavke za trenutni račun sa bojama
        stavke = dohvati_stavke_racuna(self.db_conn, self.trenutni_racun_id)
        for i, (sifra, naziv, barkod, cijena, kolicina, ukupna_cijena) in enumerate(stavke):
            cijena = cijena if cijena is not None else 0.0
            kolicina = kolicina if kolicina is not None else 0.0
            ukupna_cijena = ukupna_cijena if ukupna_cijena is not None else 0.0
            item = self.app.tree.insert("", "end", values=(sifra, naziv, barkod, f"{cijena:.2f} KM", kolicina, f"{ukupna_cijena:.2f} KM"))
            if i % 2 == 0:
                self.app.tree.item(item, tags=('evenrow',))
            else:
                self.app.tree.item(item, tags=('oddrow',))
        
        self.izracunaj_ukupnu_cijenu()
        self.focus_barkod_entry()
