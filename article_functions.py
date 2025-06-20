import tkinter as tk
from config import SVJETLO_ZELENA, TAMNO_TIRKIZNA
from tkinter import messagebox
import sqlite3
import customtkinter as ctk
import tkinter.ttk as ttk
from database import pretrazi_barkod, dodaj_stavku_racuna, azuriraj_ukupno_racuna, dodaj_artikal_u_bazu
from ui_components import sort_column
from datetime import datetime
import qrcode
from PIL import Image, ImageTk

class ArticleFunctions:
    def __init__(self, core, io_categories):
        self.core = core
        self.io_categories = io_categories
        self.app = core.app
        self.db_conn = core.db_conn
        self.dodatno_brojac = 0
        self.setup_article_bindings()

    def setup_article_bindings(self):
        self.app.dodaj_btn.configure(command=self.dodaj_artikal)
        self.app.artikli_btn.configure(command=self.prikazi_sve_artikle)
        self.app.obrisi_btn.configure(command=self.obrisi_artikal)
        self.app.izmjeni_btn.configure(command=self.izmjeni_artikal)
        self.app.tree.bind("<Double-1>", self.uredi_stavku)
        self.app.tree.bind("<Delete>", self.obrisi_artikal)
        self.app.dodatno_entry.bind("<Return>", self.dodaj_dodatnu_vrednost)
        self.app.novi_artikal_btn.configure(command=self.dodaj_novi_artikal)
        print("Bindings postavljeni:", self.app.tree.bind("<Double-1>"))
        print("Svi bindingi na Treeview:", self.app.tree.bind())

    def dodaj_dodatnu_vrednost(self, event=None):
        dodatno = self.app.dodatno_var.get().strip()
        if not dodatno:
            messagebox.showerror("Greška", "Unesi vrednost u polje Dodatno!")
            return
        try:
            cijena = float(dodatno.replace(",", "."))
            if cijena <= 0:
                messagebox.showerror("Greška", "Vrednost mora biti veća od 0!")
                return
            self.dodatno_brojac += 1
            sifra = f"DOD{self.dodatno_brojac:03d}"
            naziv = f"Dodatna stavka {self.dodatno_brojac}"
            barkod = f"DODATNO_{self.dodatno_brojac}_{datetime.now().strftime('%H%M%S')}"
            kolicina = 1.0
            ukupna_cijena = cijena * kolicina
            item = self.app.tree.insert("", "end", values=(sifra, naziv, barkod, f"{cijena:.2f} KM", kolicina, f"{ukupna_cijena:.2f} KM"))
            if len(self.app.tree.get_children()) % 2 == 0:
                self.app.tree.item(item, tags=('evenrow',))
            else:
                self.app.tree.item(item, tags=('oddrow',))
            self.app.ukupno += ukupna_cijena
            dodaj_stavku_racuna(self.db_conn, self.core.trenutni_racun_id, sifra, naziv, barkod, cijena, kolicina, ukupna_cijena)
            azuriraj_ukupno_racuna(self.db_conn, self.core.trenutni_racun_id, self.app.ukupno)
            self.app.dodatno_var.set("0,00")
            self.core.izracunaj_ukupnu_cijenu()
            self.app.tree.see(item)
            print(f"Dodata stavka: {sifra}, {naziv}, {barkod}, {cijena:.2f} KM, {kolicina}, {ukupna_cijena:.2f} KM")
        except ValueError:
            messagebox.showerror("Greška", "Unesi validan broj (npr. 10,00 ili 10.00)!")
        self.core.focus_barkod_entry()

    def dodaj_artikal(self):
        barkod = self.app.barkod_var.get().strip()
        naziv = self.app.naziv_var.get().strip()
        sifra = self.app.sifra_var.get().strip() or None
        if not barkod or not naziv:
            messagebox.showerror("Greška", "Barkod i Naziv su obavezni!")
            return
        rezultat = pretrazi_barkod(self.db_conn, barkod)
        if rezultat:
            naziv, cijena = rezultat
            kolicina = 1.0
            ukupna_cijena = cijena * kolicina
            for item in self.app.tree.get_children():
                if self.app.tree.item(item, "values")[2] == str(barkod):
                    trenutna_kolicina = float(self.app.tree.item(item, "values")[4])
                    nova_kolicina = trenutna_kolicina + kolicina
                    nova_ukupna_cijena = cijena * nova_kolicina
                    self.app.ukupno -= float(self.app.tree.item(item, "values")[5].replace(" KM", ""))
                    self.app.ukupno += nova_ukupna_cijena
                    self.app.tree.item(item, values=(sifra, naziv, str(barkod), f"{cijena:.2f} KM", nova_kolicina, f"{nova_ukupna_cijena:.2f} KM"))
                    dodaj_stavku_racuna(self.db_conn, self.core.trenutni_racun_id, sifra, naziv, barkod, cijena, nova_kolicina, nova_ukupna_cijena)
                    azuriraj_ukupno_racuna(self.db_conn, self.core.trenutni_racun_id, self.app.ukupno)
                    self.app.barkod_var.set("")
                    self.app.naziv_var.set("")
                    self.app.sifra_var.set("")
                    self.core.izracunaj_ukupnu_cijenu()
                    return
            item = self.app.tree.insert("", "end", values=(sifra, naziv, str(barkod), f"{cijena:.2f} KM", kolicina, f"{ukupna_cijena:.2f} KM"))
            if len(self.app.tree.get_children()) % 2 == 0:
                self.app.tree.item(item, tags=('evenrow',))
            else:
                self.app.tree.item(item, tags=('oddrow',))
            self.app.ukupno += ukupna_cijena
            dodaj_stavku_racuna(self.db_conn, self.core.trenutni_racun_id, sifra, naziv, barkod, cijena, kolicina, ukupna_cijena)
            azuriraj_ukupno_racuna(self.db_conn, self.core.trenutni_racun_id, self.app.ukupno)
            self.app.barkod_var.set("")
            self.app.naziv_var.set("")
            self.app.sifra_var.set("")
            self.core.izracunaj_ukupnu_cijenu()
        else:
            messagebox.showerror("Greška", "Artikal nije pronađen u bazi! Dodaj ga prvo.")
        self.core.focus_barkod_entry()

    def uredi_stavku(self, event):
        print("Dvoklik detektiran na koordinatama:", event.x, event.y)
        if self.app.tree.focus() == "":
            print("Tablica nije u fokusu, pokušavam postaviti fokus...")
            self.app.tree.focus_set()
        selektovano = self.app.tree.selection()
        if not selektovano:
            messagebox.showwarning("Info", "Nijedan artikal nije selektovan! Prvo selektiraj red.")
            print("Nema selektiranih stavki!")
            return
        item = selektovano[0]
        kolona = self.app.tree.identify_column(event.x)
        if not kolona:
            print("Nije identificirana kolona!")
            return
        values = list(self.app.tree.item(item, "values"))
        print(f"Selektirani item: {values}, kliknuta kolona: {kolona}")
        if kolona == "#4":
            trenutna_cijena = float(values[3].replace(" KM", ""))
            trenutna_kolicina = float(values[4])
            prozor = ctk.CTkToplevel(self.app.root)
            prozor.title("Uredi Osnovnu Cijenu")
            prozor.geometry("300x200")
            prozor.configure(fg_color=SVJETLO_ZELENA)
            prozor.transient(self.app.root)
            prozor.lift()
            title_frame = ctk.CTkFrame(prozor, fg_color=TAMNO_TIRKIZNA, corner_radius=10)
            title_frame.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(title_frame, text="Uredi Osnovnu Cijenu", font=self.core.FONT_BOLD, text_color="#000000").pack(side="left", padx=10)
            ctk.CTkButton(title_frame, text="X", command=prozor.destroy, width=30, fg_color="#FF6F61", hover_color="#E65A50", font=self.core.FONT).pack(side="right", padx=5)
            content_frame = ctk.CTkFrame(prozor, fg_color=SVJETLO_ZELENA)
            content_frame.pack(padx=10, pady=10, fill="both", expand=True)
            content_frame.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(content_frame, text="Nova cijena:", font=self.core.FONT).grid(row=0, column=0, padx=10, pady=10, sticky="w")
            nova_cijena_var = ctk.StringVar(value=f"{trenutna_cijena:.2f}")
            nova_cijena_entry = ctk.CTkEntry(content_frame, textvariable=nova_cijena_var, font=self.core.FONT)
            nova_cijena_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
            prozor.after(100, lambda: nova_cijena_entry.focus_set())
            prozor.after(100, lambda: nova_cijena_entry.select_range(0, tk.END))
            def spremi_cijenu():
                try:
                    nova_cijena = float(nova_cijena_var.get().replace(",", "."))
                    if nova_cijena < 0:
                        messagebox.showerror("Greška", "Cijena ne može biti manja od 0!")
                        return
                    nova_ukupna_cijena = nova_cijena * trenutna_kolicina
                    values[3] = f"{nova_cijena:.2f} KM"
                    values[5] = f"{nova_ukupna_cijena:.2f} KM"
                    self.app.tree.item(item, values=values)
                    dodaj_stavku_racuna(self.db_conn, self.core.trenutni_racun_id, values[0], values[1], values[2], nova_cijena, trenutna_kolicina, nova_ukupna_cijena)
                    azuriraj_ukupno_racuna(self.db_conn, self.core.trenutni_racun_id, self.app.ukupno)
                    self.core.izracunaj_ukupnu_cijenu()
                    prozor.destroy()
                    print(f"Cijena ažurirana: {values}")
                except ValueError:
                    messagebox.showerror("Greška", "Cijena mora biti broj!")
                    print("Greška pri unosu cijene:", nova_cijena_var.get())
            ctk.CTkButton(content_frame, text="Spremi", command=spremi_cijenu, fg_color=TAMNO_TIRKIZNA, hover_color="#3A8B93", font=self.core.FONT).grid(row=1, column=0, columnspan=2, pady=10)
            nova_cijena_entry.bind("<Return>", lambda e: spremi_cijenu())
        elif kolona == "#5":
            trenutna_kolicina = float(values[4])
            trenutna_cijena = float(values[3].replace(" KM", ""))
            prozor = ctk.CTkToplevel(self.app.root)
            prozor.title("Uredi Količinu")
            prozor.geometry("300x200")
            prozor.configure(fg_color=SVJETLO_ZELENA)
            prozor.transient(self.app.root)
            prozor.lift()
            title_frame = ctk.CTkFrame(prozor, fg_color=TAMNO_TIRKIZNA, corner_radius=10)
            title_frame.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(title_frame, text="Uredi Količinu", font=self.core.FONT_BOLD, text_color="#000000").pack(side="left", padx=10)
            ctk.CTkButton(title_frame, text="X", command=prozor.destroy, width=30, fg_color="#FF6F61", hover_color="#E65A50", font=self.core.FONT).pack(side="right", padx=5)
            content_frame = ctk.CTkFrame(prozor, fg_color=SVJETLO_ZELENA)
            content_frame.pack(padx=10, pady=10, fill="both", expand=True)
            content_frame.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(content_frame, text="Nova količina:", font=self.core.FONT).grid(row=0, column=0, padx=10, pady=10, sticky="w")
            nova_kolicina_var = ctk.StringVar(value=str(trenutna_kolicina))
            nova_kolicina_entry = ctk.CTkEntry(content_frame, textvariable=nova_kolicina_var, font=self.core.FONT)
            nova_kolicina_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
            prozor.after(100, lambda: nova_kolicina_entry.focus_set())
            prozor.after(100, lambda: nova_kolicina_entry.select_range(0, tk.END))
            def spremi_kolicinu():
                try:
                    nova_kolicina = float(nova_kolicina_var.get().replace(",", "."))
                    if nova_kolicina <= 0:
                        messagebox.showerror("Greška", "Količina mora biti veća od 0!")
                        return
                    nova_ukupna_cijena = trenutna_cijena * nova_kolicina
                    values[4] = nova_kolicina
                    values[5] = f"{nova_ukupna_cijena:.2f} KM"
                    self.app.tree.item(item, values=values)
                    dodaj_stavku_racuna(self.db_conn, self.core.trenutni_racun_id, values[0], values[1], values[2], trenutna_cijena, nova_kolicina, nova_ukupna_cijena)
                    azuriraj_ukupno_racuna(self.db_conn, self.core.trenutni_racun_id, self.app.ukupno)
                    self.core.izracunaj_ukupnu_cijenu()
                    prozor.destroy()
                    print(f"Količina ažurirana: {values}")
                except ValueError:
                    messagebox.showerror("Greška", "Količina mora biti broj!")
                    print("Greška pri unosu količine:", nova_kolicina_var.get())
            ctk.CTkButton(content_frame, text="Spremi", command=spremi_kolicinu, fg_color=TAMNO_TIRKIZNA, hover_color="#3A8B93", font=self.core.FONT).grid(row=1, column=0, columnspan=2, pady=10)
            nova_kolicina_entry.bind("<Return>", lambda e: spremi_kolicinu())
        else:
            print(f"Kliknuta kolona {kolona} nije podložna uređivanju!")
        self.core.focus_barkod_entry()

    def izmjeni_artikal(self):
        selektovano = self.app.tree.selection()
        if not selektovano:
            messagebox.showwarning("Info", "Nijedan artikal nije selektovan!")
            return
        item = selektovano[0]
        sifra, naziv, barkod, osnovna_cijena, kolicina, ukupna_cijena = self.app.tree.item(item, "values")
        osnovna_cijena = float(osnovna_cijena.replace(" KM", ""))
        kolicina = float(kolicina)
        ukupna_cijena = float(ukupna_cijena.replace(" KM", ""))
        prozor = ctk.CTkToplevel(self.app.root)
        prozor.title("Izmjeni Artikal")
        prozor.geometry("400x400")
        prozor.configure(fg_color=SVJETLO_ZELENA)
        prozor.transient(self.app.root)
        prozor.lift()
        title_frame = ctk.CTkFrame(prozor, fg_color=TAMNO_TIRKIZNA, corner_radius=10)
        title_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(title_frame, text="Izmjeni Artikal", font=self.core.FONT_BOLD, text_color="#000000").pack(side="left", padx=10)
        ctk.CTkButton(title_frame, text="X", command=prozor.destroy, width=30, fg_color="#FF6F61", hover_color="#E65A50", font=self.core.FONT).pack(side="right", padx=5)
        content_frame = ctk.CTkFrame(prozor, fg_color=SVJETLO_ZELENA)
        content_frame.pack(padx=20, pady=20, fill="both", expand=True)
        content_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(content_frame, text="Šifra:", font=self.core.FONT).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        sifra_var = ctk.StringVar(value=sifra)
        sifra_entry = ctk.CTkEntry(content_frame, textvariable=sifra_var, font=self.core.FONT)
        sifra_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(content_frame, text="Naziv:", font=self.core.FONT).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        naziv_var = ctk.StringVar(value=naziv)
        naziv_entry = ctk.CTkEntry(content_frame, textvariable=naziv_var, font=self.core.FONT)
        naziv_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(content_frame, text="Barkod:", font=self.core.FONT).grid(row=2, column=0, padx=10, pady=10, sticky="w")
        barkod_var = ctk.StringVar(value=barkod)
        barkod_entry = ctk.CTkEntry(content_frame, textvariable=barkod_var, font=self.core.FONT)
        barkod_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(content_frame, text="Cijena:", font=self.core.FONT).grid(row=3, column=0, padx=10, pady=10, sticky="w")
        cijena_var = ctk.StringVar(value=f"{osnovna_cijena:.2f}")
        cijena_entry = ctk.CTkEntry(content_frame, textvariable=cijena_var, font=self.core.FONT)
        cijena_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(content_frame, text="Količina:", font=self.core.FONT).grid(row=4, column=0, padx=10, pady=10, sticky="w")
        kolicina_var = ctk.StringVar(value=str(kolicina))
        kolicina_entry = ctk.CTkEntry(content_frame, textvariable=kolicina_var, font=self.core.FONT)
        kolicina_entry.grid(row=4, column=1, padx=10, pady=10, sticky="ew")
        def spremi_izmjene():
            try:
                nova_sifra = sifra_var.get().strip()
                novi_naziv = naziv_var.get().strip()
                novi_barkod = barkod_var.get().strip()
                nova_cijena = float(cijena_var.get().replace(",", "."))
                nova_kolicina = float(kolicina_var.get().replace(",", "."))
                if not novi_barkod or not novi_naziv:
                    messagebox.showerror("Greška", "Barkod i Naziv ne smeju biti prazni!")
                    return
                if nova_cijena < 0 or nova_kolicina <= 0:
                    messagebox.showerror("Greška", "Cijena i količina moraju biti pozitivni!")
                    return
                nova_ukupna_cijena = nova_cijena * nova_kolicina
                self.app.tree.item(item, values=(nova_sifra, novi_naziv, novi_barkod, f"{nova_cijena:.2f} KM", nova_kolicina, f"{nova_ukupna_cijena:.2f} KM"))
                self.app.ukupno = self.app.ukupno - ukupna_cijena + nova_ukupna_cijena
                dodaj_stavku_racuna(self.db_conn, self.core.trenutni_racun_id, nova_sifra, novi_naziv, novi_barkod, nova_cijena, nova_kolicina, nova_ukupna_cijena)
                azuriraj_ukupno_racuna(self.db_conn, self.core.trenutni_racun_id, self.app.ukupno)
                c = self.db_conn.cursor()
                c.execute("SELECT id FROM artikli WHERE barkod = ?", (barkod,))
                rezultat = c.fetchone()
                if rezultat:
                    c.execute("UPDATE artikli SET id = ?, barkod = ?, naziv = ?, cijena = ? WHERE barkod = ?",
                              (nova_sifra, novi_barkod, novi_naziv, nova_cijena, barkod))
                    self.db_conn.commit()
                    print(f"Artikal sa barkodom {barkod} ažuriran u tabeli artikli.")
                else:
                    c.execute("INSERT INTO artikli (id, barkod, naziv, cijena) VALUES (?, ?, ?, ?)",
                              (nova_sifra, novi_barkod, novi_naziv, nova_cijena))
                    self.db_conn.commit()
                    print(f"Artikal sa barkodom {novi_barkod} dodat u tabelu artikli jer nije postojao.")
                self.io_categories.izvoz_iz_baze()
                print("Excel fajl ažuriran.")
                self.core.izracunaj_ukupnu_cijenu()
                prozor.destroy()
            except ValueError:
                messagebox.showerror("Greška", "Cijena i količina moraju biti brojevi!")
            except sqlite3.Error as e:
                messagebox.showerror("Greška", f"Došlo je do greške u bazi: {e}")
        ctk.CTkButton(content_frame, text="Spremi", command=spremi_izmjene, fg_color=TAMNO_TIRKIZNA, hover_color="#3A8B93", font=self.core.FONT).grid(row=5, column=0, columnspan=2, pady=10)
        sifra_entry.focus_set()

    def obrisi_artikal(self, event=None):
        selektovano = self.app.tree.selection()
        if not selektovano:
            messagebox.showwarning("Info", "Nijedan artikal nije selektovan!")
            return
        try:
            c = self.db_conn.cursor()
            for item in selektovano:
                ukupna_cijena = float(self.app.tree.item(item, "values")[5].replace(" KM", ""))
                self.app.ukupno -= ukupna_cijena
                if self.app.ukupno < 0:
                    self.app.ukupno = 0
                barkod = self.app.tree.item(item, "values")[2]
                c.execute("DELETE FROM aktivne_stavke WHERE racun_id = ? AND barkod = ?", (self.core.trenutni_racun_id, barkod))
                self.app.tree.delete(item)
            self.db_conn.commit()
            azuriraj_ukupno_racuna(self.db_conn, self.core.trenutni_racun_id, self.app.ukupno)
            self.core.izracunaj_ukupnu_cijenu()
        except sqlite3.Error as e:
            messagebox.showerror("Greška", f"Došlo je do greške: {e}")
        self.core.focus_barkod_entry()

    def prikazi_sve_artikle(self):
        prozor = ctk.CTkToplevel(self.app.root)
        prozor.title("Svi Artikli")
        prozor.geometry("800x600")
        prozor.configure(fg_color=SVJETLO_ZELENA)
        prozor.transient(self.app.root)
        prozor.lift()
        title_frame = ctk.CTkFrame(prozor, fg_color=TAMNO_TIRKIZNA, corner_radius=10)
        title_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(title_frame, text="Svi Artikli", font=self.core.FONT_BOLD, text_color="#000000").pack(side="left", padx=10)
        ctk.CTkButton(title_frame, text="X", command=prozor.destroy, width=30, fg_color="#FF6F61", hover_color="#E65A50", font=self.core.FONT).pack(side="right", padx=5)
        main_frame = ctk.CTkFrame(prozor, fg_color=SVJETLO_ZELENA)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        search_frame = ctk.CTkFrame(main_frame, fg_color=SVJETLO_ZELENA)
        search_frame.pack(fill="x", pady=10)
        search_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(search_frame, text="Pretraži:", font=self.core.FONT).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(search_frame, textvariable=search_var, font=self.core.FONT)
        search_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        search_entry.focus_set()
        sort_var = ctk.StringVar(value="Šifra (rastuće)")
        sort_menu = ctk.CTkOptionMenu(search_frame, values=["Šifra (rastuće)", "Šifra (opadajuće)", "Naziv (A-Z)"],
                                      variable=sort_var, fg_color=TAMNO_TIRKIZNA, button_hover_color="#3A8B93", font=self.core.FONT)
        sort_menu.grid(row=0, column=2, padx=10, pady=5)
        tree_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=10)
        tree_frame.pack(fill="both", expand=True, pady=10)
        tree = ttk.Treeview(tree_frame, columns=("Šifra", "Barkod", "Naziv", "Cijena"), show="headings", selectmode="extended")
        tree.heading("Šifra", text="Šifra ▲▼", command=lambda: sort_column(tree, "Šifra", False))
        tree.heading("Barkod", text="Barkod ▲▼", command=lambda: sort_column(tree, "Barkod", False))
        tree.heading("Naziv", text="Naziv ▲▼", command=lambda: sort_column(tree, "Naziv", False))
        tree.heading("Cijena", text="Cijena ▲▼", command=lambda: sort_column(tree, "Cijena", False))
        tree.column("Šifra", width=70)
        tree.column("Barkod", width=200)
        tree.column("Naziv", width=350)
        tree.column("Cijena", width=130)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        menu_frame = ctk.CTkFrame(main_frame, fg_color=SVJETLO_ZELENA)
        menu_frame.pack(side="right", fill="y", padx=10)
        menu = tk.Menu(prozor, tearoff=0)
        menu.add_command(label="Obriši", command=lambda: self.obrisi_artikal_iz_baze(tree))
        menu.add_command(label="Uvezi iz Excel-a", command=self.io_categories.uvoz_iz_excela)
        menu.add_command(label="Izvoz u Excel", command=self.io_categories.izvoz_iz_baze)
        menu.add_command(label="Novi artikal", command=lambda: self.dodaj_novi_artikal(tree))
        menu.add_command(label="Izmjeni artikal", command=lambda: self.izmjeni_artikal_iz_baze(tree))
        menu_btn = ctk.CTkButton(menu_frame, text="Opcije", command=lambda: menu.post(menu_btn.winfo_rootx(), menu_btn.winfo_rooty() + menu_btn.winfo_height()), fg_color=TAMNO_TIRKIZNA, hover_color="#3A8B93", font=self.core.FONT)
        menu_btn.pack(pady=5)
        ctk.CTkButton(main_frame, text="Dodaj u tabelu", command=lambda: self.dodaj_u_tabelu(tree, prozor), fg_color=TAMNO_TIRKIZNA, hover_color="#3A8B93", font=self.core.FONT).pack(pady=10)
        def pretrazi_i_sortiraj(event=None):
            search_term = search_var.get().strip()
            sort_option = sort_var.get()
            tree.delete(*tree.get_children())
            try:
                c = self.db_conn.cursor()
                query = "SELECT id, barkod, naziv, cijena FROM artikli"
                params = ()
                if search_term:
                    query += " WHERE naziv LIKE ? OR barkod LIKE ?"
                    params = (f"%{search_term}%", f"%{search_term}%")
                if sort_option == "Šifra (rastuće)":
                    query += " ORDER BY id ASC"
                elif sort_option == "Šifra (opadajuće)":
                    query += " ORDER BY id DESC"
                elif sort_option == "Naziv (A-Z)":
                    query += " ORDER BY naziv ASC"
                c.execute(query, params)
                for sifra, barkod, naziv, cijena in c.fetchall():
                    tree.insert("", "end", values=(sifra, barkod, naziv, f"{cijena:.2f} KM"))
            except sqlite3.Error as e:
                messagebox.showerror("Greška", f"Došlo je do greške: {e}")
        tree.bind("<Double-1>", lambda event: self.dodaj_u_tabelu(tree, prozor))
        tree.bind("<Return>", lambda event: self.dodaj_u_tabelu(tree, prozor))
        search_entry.bind("<KeyRelease>", pretrazi_i_sortiraj)
        sort_var.trace("w", lambda *args: pretrazi_i_sortiraj())
        pretrazi_i_sortiraj()

    def dodaj_u_tabelu(self, tree, prozor):
        selektovano = tree.selection()
        if not selektovano:
            messagebox.showwarning("Info", "Nijedan artikal nije selektovan!")
            return
        item = selektovano[0]
        sifra, barkod, naziv, cijena = tree.item(item, "values")
        cijena = float(cijena.replace(" KM", ""))
        kolicina = 1.0
        ukupna_cijena = cijena * kolicina
        for main_item in self.app.tree.get_children():
            if self.app.tree.item(main_item, "values")[2] == str(barkod):
                trenutna_kolicina = float(self.app.tree.item(main_item, "values")[4])
                nova_kolicina = trenutna_kolicina + kolicina
                nova_ukupna_cijena = cijena * nova_kolicina
                self.app.ukupno -= float(self.app.tree.item(main_item, "values")[5].replace(" KM", ""))
                self.app.ukupno += nova_ukupna_cijena
                self.app.tree.item(main_item, values=(sifra, naziv, str(barkod), f"{cijena:.2f} KM", nova_kolicina, f"{nova_ukupna_cijena:.2f} KM"))
                dodaj_stavku_racuna(self.db_conn, self.core.trenutni_racun_id, sifra, naziv, barkod, cijena, nova_kolicina, nova_ukupna_cijena)
                azuriraj_ukupno_racuna(self.db_conn, self.core.trenutni_racun_id, self.app.ukupno)
                self.app.cijena_label.configure(text=f"{self.app.ukupno:.2f} KM")
                prozor.destroy()
                self.core.osvjezi_trenutni_racun()
                return
        item = self.app.tree.insert("", "end", values=(sifra, naziv, str(barkod), f"{cijena:.2f} KM", kolicina, f"{ukupna_cijena:.2f} KM"))
        if len(self.app.tree.get_children()) % 2 == 0:
            self.app.tree.item(item, tags=('evenrow',))
        else:
            self.app.tree.item(item, tags=('oddrow',))
        self.app.ukupno += ukupna_cijena
        dodaj_stavku_racuna(self.db_conn, self.core.trenutni_racun_id, sifra, naziv, barkod, cijena, kolicina, ukupna_cijena)
        azuriraj_ukupno_racuna(self.db_conn, self.core.trenutni_racun_id, self.app.ukupno)
        self.core.izracunaj_ukupnu_cijenu()
        prozor.destroy()
        self.core.osvjezi_trenutni_racun()

    def obrisi_artikal_iz_baze(self, tree):
        selektovano = tree.selection()
        if not selektovano:
            messagebox.showwarning("Info", "Nijedan artikal nije selektovan!")
            return
        item = selektovano[0]
        barkod = tree.item(item, "values")[1]
        if messagebox.askyesno("Potvrda", f"Da li ste sigurni da želite obrisati artikal sa barkodom {barkod}?"):
            c = self.db_conn.cursor()
            c.execute("DELETE FROM artikli WHERE barkod = ?", (barkod,))
            self.db_conn.commit()
            tree.delete(item)

    def dodaj_novi_artikal(self, tree=None):
        prozor = ctk.CTkToplevel(self.app.root)
        prozor.title("Novi Artikal")
        prozor.geometry("600x400")
        prozor.configure(fg_color=SVJETLO_ZELENA)
        prozor.transient(self.app.root)
        prozor.lift()
        prozor.attributes('-topmost', True)
        title_frame = ctk.CTkFrame(prozor, fg_color=TAMNO_TIRKIZNA, corner_radius=10)
        title_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(title_frame, text="Novi Artikal", font=self.core.FONT_BOLD, text_color="#000000").pack(side="left", padx=10)
        ctk.CTkButton(title_frame, text="X", command=prozor.destroy, width=30, fg_color="#FF6F61", hover_color="#E65A50", font=self.core.FONT).pack(side="right", padx=5)
        content_frame = ctk.CTkFrame(prozor, fg_color=SVJETLO_ZELENA)
        content_frame.pack(padx=20, pady=20, fill="both", expand=True)
        content_frame.grid_columnconfigure(1, weight=1)
        c = self.db_conn.cursor()
        c.execute("SELECT MAX(id) FROM artikli")
        max_id = c.fetchone()[0]
        nova_sifra = int(max_id) + 1 if max_id else 2023
        ctk.CTkLabel(content_frame, text=f"Šifra: {nova_sifra}", font=self.core.FONT, text_color="#000000").grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        ctk.CTkLabel(content_frame, text="Barkod:", font=self.core.FONT).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        barkod_var = ctk.StringVar()
        barkod_entry = ctk.CTkEntry(content_frame, textvariable=barkod_var, font=self.core.FONT, border_color="#000000")
        barkod_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(content_frame, text="Naziv:", font=self.core.FONT).grid(row=2, column=0, padx=10, pady=10, sticky="w")
        naziv_var = ctk.StringVar()
        naziv_entry = ctk.CTkEntry(content_frame, textvariable=naziv_var, font=self.core.FONT)
        naziv_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(content_frame, text="Cijena:", font=self.core.FONT).grid(row=3, column=0, padx=10, pady=10, sticky="w")
        cijena_var = ctk.StringVar()
        cijena_entry = ctk.CTkEntry(content_frame, textvariable=cijena_var, font=self.core.FONT)
        cijena_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        spremi_btn = ctk.CTkButton(content_frame, text="Spremi", command=None, fg_color=TAMNO_TIRKIZNA, hover_color="#3A8B93", font=self.core.FONT, state="disabled")
        spremi_btn.grid(row=4, column=0, columnspan=2, pady=10)
        def validate_barcode(event=None):
            barkod = barkod_var.get().strip()
            if not barkod:
                barkod_entry.configure(border_color="#000000")
                spremi_btn.configure(state="disabled")
                return
            c = self.db_conn.cursor()
            c.execute("SELECT barkod FROM artikli WHERE barkod = ?", (barkod,))
            if c.fetchone():
                barkod_entry.configure(border_color="#FF0000")
                spremi_btn.configure(state="disabled")
            else:
                barkod_entry.configure(border_color="#00FF00")
                spremi_btn.configure(state="normal")
        def spremi_novi():
            barkod = barkod_var.get().strip()
            naziv = naziv_var.get().strip()
            try:
                cijena = float(cijena_var.get().replace(",", "."))
                if not barkod or not naziv or cijena < 0:
                    messagebox.showerror("Greška", "Sva polja moraju biti popunjena i cijena mora biti pozitivna!")
                    return
                c = self.db_conn.cursor()
                c.execute("SELECT barkod FROM artikli WHERE barkod = ?", (barkod,))
                if c.fetchone():
                    messagebox.showerror("Greška", "Barkod je već u upotrebi! Unesite drugi barkod.")
                    barkod_entry.configure(border_color="#FF0000")
                    spremi_btn.configure(state="disabled")
                    return
                c.execute("INSERT INTO artikli (id, barkod, naziv, cijena) VALUES (?, ?, ?, ?)", (nova_sifra, barkod, naziv, cijena))
                self.db_conn.commit()
                if tree:
                    tree.insert("", "end", values=(nova_sifra, barkod, naziv, f"{cijena:.2f} KM"))
                self.io_categories.izvoz_iz_baze()
                print("Excel fajl ažuriran.")
                prozor.destroy()
            except ValueError:
                messagebox.showerror("Greška", "Cijena mora biti broj!")
            except sqlite3.Error as e:
                messagebox.showerror("Greška", f"Došlo je do greške: {e}")
        spremi_btn.configure(command=spremi_novi)
        barkod_entry.bind("<FocusOut>", validate_barcode)
        barkod_entry.bind("<Return>", lambda e: [validate_barcode(), naziv_entry.focus_set()])
        naziv_entry.bind("<Return>", lambda e: cijena_entry.focus_set())
        cijena_entry.bind("<Return>", lambda e: spremi_novi() if spremi_btn.cget("state") == "normal" else None)
        barkod_entry.focus_set()

    def izmjeni_artikal_iz_baze(self, tree):
        selektovano = tree.selection()
        if not selektovano:
            messagebox.showwarning("Info", "Nijedan artikal nije selektovan!")
            return
        item = selektovano[0]
        sifra, barkod, naziv, cijena = tree.item(item, "values")
        cijena = float(cijena.replace(" KM", ""))
        prozor = ctk.CTkToplevel(self.app.root)
        prozor.title("Izmjeni Artikal")
        prozor.geometry("400x300")
        prozor.configure(fg_color=SVJETLO_ZELENA)
        prozor.transient(self.app.root)
        prozor.lift()
        title_frame = ctk.CTkFrame(prozor, fg_color=TAMNO_TIRKIZNA, corner_radius=10)
        title_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(title_frame, text="Izmjeni Artikal", font=self.core.FONT_BOLD, text_color="#000000").pack(side="left", padx=10)
        ctk.CTkButton(title_frame, text="X", command=prozor.destroy, width=30, fg_color="#FF6F61", hover_color="#E65A50", font=self.core.FONT).pack(side="right", padx=5)
        content_frame = ctk.CTkFrame(prozor, fg_color=SVJETLO_ZELENA)
        content_frame.pack(padx=20, pady=20, fill="both", expand=True)
        content_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(content_frame, text="Barkod:", font=self.core.FONT).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        barkod_var = ctk.StringVar(value=barkod)
        barkod_entry = ctk.CTkEntry(content_frame, textvariable=barkod_var, font=self.core.FONT)
        barkod_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(content_frame, text="Naziv:", font=self.core.FONT).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        naziv_var = ctk.StringVar(value=naziv)
        naziv_entry = ctk.CTkEntry(content_frame, textvariable=naziv_var, font=self.core.FONT)
        naziv_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(content_frame, text="Cijena:", font=self.core.FONT).grid(row=2, column=0, padx=10, pady=10, sticky="w")
        cijena_var = ctk.StringVar(value=f"{cijena:.2f}")
        cijena_entry = ctk.CTkEntry(content_frame, textvariable=cijena_var, font=self.core.FONT)
        cijena_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        def spremi_izmjene():
            novi_barkod = barkod_var.get().strip()
            novi_naziv = naziv_var.get().strip()
            try:
                nova_cijena = float(cijena_var.get().replace(",", "."))
                if not novi_barkod or not novi_naziv or nova_cijena < 0:
                    messagebox.showerror("Greška", "Sva polja moraju biti popunjena i cijena mora biti pozitivna!")
                    return
                c = self.db_conn.cursor()
                c.execute("UPDATE artikli SET barkod = ?, naziv = ?, cijena = ? WHERE id = ?",
                          (novi_barkod, novi_naziv, nova_cijena, sifra))
                self.db_conn.commit()
                tree.item(item, values=(sifra, novi_barkod, novi_naziv, f"{nova_cijena:.2f} KM"))
                prozor.destroy()
            except ValueError:
                messagebox.showerror("Greška", "Cijena mora biti broj!")
            except sqlite3.Error as e:
                messagebox.showerror("Greška", f"Došlo je do greške: {e}")
        ctk.CTkButton(content_frame, text="Spremi", command=spremi_izmjene, fg_color=TAMNO_TIRKIZNA, hover_color="#3A8B93", font=self.core.FONT).grid(row=3, column=0, columnspan=2, pady=10)

    def generisi_qr_kodove(self, artikli, parent):
        """Prikazuje QR kodove za artikle u zasebnim prozorima."""
        if not artikli:
            messagebox.showinfo("Info", "Nema artikala za prikaz QR kodova!")
            return
        ArticleQRProzor(parent, artikli)

class ArticleQRProzor(ctk.CTkToplevel):
    def __init__(self, parent, artikli):
        super().__init__(parent)
        self.artikli = artikli  # Lista artikala
        self.index = 0  # Trenutni indeks artikla
        self.title("QR Kod Artikla")
        self.geometry("500x600")
        self.configure(fg_color=SVJETLO_ZELENA)

        # Label za prikaz QR koda
        self.qr_label = tk.Label(self, bg=SVJETLO_ZELENA)
        self.qr_label.pack(pady=20)

        # Label za prikaz informacija o artiklu
        self.info_label = ctk.CTkLabel(self, text="", font=("Arial", 14), text_color="black")
        self.info_label.pack(pady=10)

        # Binding za tastere Space i Enter
        self.bind("<space>", self.show_next)
        self.bind("<Return>", self.show_next)

        # Prikaz prvog artikla
        self.show_current()

        # Osiguravamo da prozor bude ispred i ima fokus
        self.grab_set()
        self.focus_set()

    def generisi_qr(self, barkod):
        """Generiše QR kod iz barkoda."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(barkod)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((350, 350), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(qr_img)

    def show_current(self):
        """Prikazuje trenutni artikal."""
        if self.index >= len(self.artikli):
            self.destroy()
            return

        artikal = self.artikli[self.index]
        barkod = artikal['barkod']

        # Generiši QR kod
        qr_photo = self.generisi_qr(barkod)
        self.qr_label.configure(image=qr_photo)
        self.qr_label.image = qr_photo  # Čuvanje reference

        # Prikaz informacija
        info_text = (f"Šifra: {artikal.get('sifra', 'N/A')}\n"
                     f"Naziv: {artikal['naziv']}\n"
                     f"Barkod: {artikal['barkod']}\n"
                     f"Cijena: {artikal.get('cijena', 0):.2f} KM\n"
                     f"Količina: {artikal.get('kolicina', 1.0)}\n"
                     f"Ukupna cijena: {artikal.get('ukupna_cijena', artikal.get('cijena', 0) * artikal.get('kolicina', 1.0)):.2f} KM")
        self.info_label.configure(text=info_text)

    def show_next(self, event=None):
        """Prikazuje sljedeći artikal."""
        self.index += 1
        self.show_current()