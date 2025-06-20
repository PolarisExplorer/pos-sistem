import tkinter as tk
from config import SVJETLO_ZELENA, TAMNO_TIRKIZNA
from tkinter import messagebox
import sqlite3
import customtkinter as ctk
import tkinter.ttk as ttk
from database import dodaj_aktivni_racun, dohvati_aktivne_racune, zavrsi_racun
from windows import QRProzor

class ReceiptFunctions:
    def __init__(self, core):
        self.core = core
        self.app = core.app
        self.db_conn = core.db_conn
        self.setup_receipt_bindings()

    def setup_receipt_bindings(self):
        self.app.zavrsi_novi_btn.configure(command=self.zavrsi_i_novi_racun)
        self.app.svi_racuni_btn.configure(command=self.prikazi_aktivne_racune)
        self.app.raniji_racuni_btn.configure(command=self.prikazi_ranije_racune)
        self.app.dodatno_entry.bind("<Return>", self.update_total_with_dodatno)
        self.app.root.bind("<Caps_Lock>", lambda event: self.zavrsi_i_novi_racun())

    def update_total_with_dodatno(self, event=None):
        try:
            dodatno = float(self.app.dodatno_var.get().replace(",", ".")) if self.app.dodatno_var.get() else 0.0
            ukupno_artikala = sum(float(self.app.tree.item(item, "values")[5].replace(" KM", "")) for item in self.app.tree.get_children())
            nova_ukupna_cijena = ukupno_artikala + dodatno
            self.app.ukupno = nova_ukupna_cijena
            self.app.cijena_label.configure(text=f"{nova_ukupna_cijena:.2f} KM")
        except ValueError:
            messagebox.showerror("Greška", "Unesi validan iznos za 'Dodatno'!")
        self.core.focus_barkod_entry()

    def zavrsi_i_novi_racun(self):
        if not self.app.tree.get_children():
            messagebox.showwarning("Info", "Nema artikala za završetak računa!")
            return
        try:
            if self.core.trenutni_racun_id != 1:
                zavrsi_racun(self.db_conn, self.core.trenutni_racun_id)
                ukupno = self.app.ukupno if self.app.ukupno is not None else 0.0
                messagebox.showinfo("Info", f"Račun je završen i iznosi: {ukupno:.2f} KM\nRačun je obrisan i vraćam se na Račun 1.")
            else:
                messagebox.showinfo("Info", "Račun 1 ne može biti obrisan, ostaje aktivan.")
            self.core.resetuj_sve()
            racuni = dohvati_aktivne_racune(self.db_conn)
            for racun in racuni:
                if racun[1] == "Račun 1":
                    self.core.trenutni_racun_id = racun[0]
                    self.app.trenutni_racun_label.configure(text="Račun 1")
                    break
            else:
                self.core.trenutni_racun_id = dodaj_aktivni_racun(self.db_conn, "Račun 1")
                self.app.trenutni_racun_label.configure(text="Račun 1")
            self.core.osvjezi_trenutni_racun()
        except Exception as e:
            messagebox.showerror("Greška", f"Došlo je do greške prilikom završavanja računa: {e}")
        self.core.focus_barkod_entry()

    def prikazi_aktivne_racune(self):
        prozor = ctk.CTkToplevel(self.app.root)
        prozor.title("Svi aktivni računi")
        prozor.geometry("500x600")
        prozor.configure(fg_color=SVJETLO_ZELENA)
        prozor.transient(self.app.root)
        prozor.lift()
        title_frame = ctk.CTkFrame(prozor, fg_color=TAMNO_TIRKIZNA, corner_radius=10)
        title_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(title_frame, text="Svi aktivni računi", font=self.core.FONT_BOLD, text_color="#000000").pack(side="left", padx=10)
        ctk.CTkButton(title_frame, text="X", command=prozor.destroy, width=30, fg_color="#FF6F61", hover_color="#E65A50").pack(side="right", padx=5)
        tree_frame = ctk.CTkFrame(prozor, fg_color="white", corner_radius=10)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        tree = ttk.Treeview(tree_frame, columns=("ID", "Naziv", "Ukupno"), show="headings")
        tree.heading("ID", text="ID")
        tree.heading("Naziv", text="Naziv")
        tree.heading("Ukupno", text="Ukupno (KM)")
        tree.column("ID", width=50)
        tree.column("Naziv", width=200)
        tree.column("Ukupno", width=100)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        racuni = dohvati_aktivne_racune(self.db_conn)
        for racun in racuni:
            ukupno = racun[3] if racun[3] is not None else 0.0
            tree.insert("", "end", values=(racun[0], racun[1], f"{ukupno:.2f} KM"))
        def prebaci_na_racun(event=None):
            selektovano = tree.selection()
            if not selektovano:
                messagebox.showwarning("Info", "Nijedan račun nije selektovan!")
                return
            item = selektovano[0]
            self.core.trenutni_racun_id = int(tree.item(item, "values")[0])
            naziv_racuna = tree.item(item, "values")[1]
            self.app.trenutni_racun_label.configure(text=naziv_racuna)
            self.core.osvjezi_trenutni_racun()
            prozor.destroy()
        def dodaj_novi_racun():
            racuni = dohvati_aktivne_racune(self.db_conn)
            novi_broj = len(racuni) + 1
            naziv = f"Račun {novi_broj}"
            novi_racun_id = dodaj_aktivni_racun(self.db_conn, naziv)
            if novi_racun_id:
                tree.insert("", "end", values=(novi_racun_id, naziv, "0,00 KM"))
                self.core.trenutni_racun_id = novi_racun_id
                self.app.trenutni_racun_label.configure(text=naziv)
                self.core.osvjezi_trenutni_racun()
                prozor.destroy()
        ctk.CTkButton(prozor, text="Prebaci na račun", command=prebaci_na_racun, fg_color=TAMNO_TIRKIZNA, hover_color="#3A8B93").pack(side="left", padx=10, pady=10)
        ctk.CTkButton(prozor, text="+ Novi račun", command=dodaj_novi_racun, fg_color=TAMNO_TIRKIZNA, hover_color="#3A8B93").pack(side="left", padx=10, pady=10)
        tree.bind("<Double-1>", prebaci_na_racun)
        self.core.focus_barkod_entry()

    def dohvati_stavke_racuna(self, conn, racun_id):
        cursor = conn.cursor()
        cursor.execute("""
            SELECT rs.sifra, a.naziv, a.barkod, rs.cijena, rs.kolicina, rs.ukupna_cijena
            FROM racun_stavke rs
            JOIN artikli a ON rs.barkod = a.barkod
            WHERE rs.racun_id = ?
        """, (racun_id,))
        stavke = [
            {
                'sifra': row[0],
                'naziv': row[1],
                'barkod': row[2],
                'cijena': row[3],
                'kolicina': row[4],
                'ukupna_cijena': row[5]
            }
            for row in cursor.fetchall()
        ]
        return stavke

    def prikazi_ranije_racune(self):
        prozor = ctk.CTkToplevel(self.app.root)
        prozor.title("Raniji Računi")
        prozor.geometry("800x600")
        prozor.configure(fg_color=SVJETLO_ZELENA)
        prozor.transient(self.app.root)
        prozor.lift()
        title_frame = ctk.CTkFrame(prozor, fg_color=TAMNO_TIRKIZNA, corner_radius=10)
        title_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(title_frame, text="Raniji Računi", font=self.core.FONT_BOLD, text_color="#000000").pack(side="left", padx=10)
        ctk.CTkButton(title_frame, text="X", command=prozor.destroy, width=30, fg_color="#FF6F61", hover_color="#E65A50").pack(side="right", padx=5)
        tree_frame = ctk.CTkFrame(prozor, fg_color="white", corner_radius=10)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        tree = ttk.Treeview(tree_frame, columns=("ID", "Datum i Vrijeme", "Ukupno"), show="headings")
        tree.heading("ID", text="ID")
        tree.heading("Datum i Vrijeme", text="Datum i Vrijeme")
        tree.heading("Ukupno", text="Ukupno (KM)")
        tree.column("ID", width=50)
        tree.column("Datum i Vrijeme", width=200)
        tree.column("Ukupno", width=100)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        try:
            c = self.db_conn.cursor()
            c.execute("SELECT id, datum_vrijeme, ukupno FROM racuni ORDER BY datum_vrijeme DESC")
            racuni = c.fetchall()
            for racun in racuni:
                ukupno = racun[2] if racun[2] is not None else 0.0
                tree.insert("", "end", values=(racun[0], racun[1], f"{ukupno:.2f} KM"))
        except sqlite3.Error as e:
            messagebox.showerror("Greška", f"Došlo je do greške: {e}")
        def prikazi_stavke(event=None):
            selektovano = tree.selection()
            if not selektovano:
                messagebox.showwarning("Info", "Nijedan račun nije selektovan!")
                return
            item = selektovano[0]
            racun_id = tree.item(item, "values")[0]
            stavke_prozor = ctk.CTkToplevel(self.app.root)
            stavke_prozor.title(f"Stavke računa {racun_id}")
            stavke_prozor.geometry("800x400")
            stavke_prozor.configure(fg_color=SVJETLO_ZELENA)
            stavke_prozor.transient(self.app.root)
            stavke_prozor.lift()
            title_frame = ctk.CTkFrame(stavke_prozor, fg_color=TAMNO_TIRKIZNA, corner_radius=10)
            title_frame.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(title_frame, text=f"Stavke računa {racun_id}", font=self.core.FONT_BOLD, text_color="#000000").pack(side="left", padx=10)
            ctk.CTkButton(title_frame, text="X", command=stavke_prozor.destroy, width=30, fg_color="#FF6F61", hover_color="#E65A50").pack(side="right", padx=5)
            stavke_frame = ctk.CTkFrame(stavke_prozor, fg_color="white", corner_radius=10)
            stavke_frame.pack(fill="both", expand=True, padx=10, pady=10)
            stavke_tree = ttk.Treeview(stavke_frame, columns=("Šifra", "Naziv", "Barkod", "Cijena", "Količina", "Ukupna Cijena"), show="headings")
            stavke_tree.heading("Šifra", text="Šifra")
            stavke_tree.heading("Naziv", text="Naziv")
            stavke_tree.heading("Barkod", text="Barkod")
            stavke_tree.heading("Cijena", text="Cijena")
            stavke_tree.heading("Količina", text="Količina")
            stavke_tree.heading("Ukupna Cijena", text="Ukupna Cijena")
            stavke_tree.column("Šifra", width=50)
            stavke_tree.column("Naziv", width=200)
            stavke_tree.column("Barkod", width=150)
            stavke_tree.column("Cijena", width=100)
            stavke_tree.column("Količina", width=100)
            stavke_tree.column("Ukupna Cijena", width=100)
            stavke_tree.pack(side="left", fill="both", expand=True)
            scrollbar = ttk.Scrollbar(stavke_frame, orient="vertical", command=stavke_tree.yview)
            stavke_tree.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            try:
                c = self.db_conn.cursor()
                c.execute("SELECT sifra, naziv, barkod, cijena, kolicina, ukupna_cijena FROM racun_stavke WHERE racun_id = ?", (racun_id,))
                stavke = c.fetchall()
                for stavka in stavke:
                    stavke_tree.insert("", "end", values=(stavka[0], stavka[1], stavka[2], f"{stavka[3]:.2f} KM", stavka[4], f"{stavka[5]:.2f} KM"))
            except sqlite3.Error as e:
                messagebox.showerror("Greška", f"Došlo je do greške: {e}")
            stavke_za_qr = self.dohvati_stavke_racuna(self.db_conn, racun_id)
            qr_btn = ctk.CTkButton(
                stavke_prozor,
                text="QR Kod",
                command=lambda: self.prikazi_qr_kodove_za_racun(stavke_za_qr),
                fg_color=TAMNO_TIRKIZNA,
                hover_color="#3A8B93"
            )
            qr_btn.pack(pady=10)
        tree.bind("<Double-1>", prikazi_stavke)
        ctk.CTkButton(prozor, text="Prikaži stavke", command=prikazi_stavke, fg_color=TAMNO_TIRKIZNA, hover_color="#3A8B93").pack(pady=10)
        self.core.focus_barkod_entry()

    def prikazi_qr_kodove_za_racun(self, stavke):
        """Prikazuje QR kodove za stavke računa u zasebnim prozorima."""
        if not stavke:
            messagebox.showinfo("Info", "Nema stavki za prikaz QR kodova!")
            return
        QRProzor(self.app.root, stavke)
