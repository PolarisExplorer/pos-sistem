import tkinter as tk
from config import SVJETLO_ZELENA, TAMNO_TIRKIZNA
from tkinter import messagebox
import sqlite3
import customtkinter as ctk
import tkinter.ttk as ttk
from database import pretrazi_barkod, pretrazi_sifru, dodaj_stavku_racuna, azuriraj_ukupno_racuna

class SearchFunctions:
    def __init__(self, core):
        self.core = core
        self.app = core.app
        self.db_conn = core.db_conn
        self.setup_search_bindings()

    def setup_search_bindings(self):
        self.app.barkod_entry.bind("<Return>", self.pretrazi_barkod)
        self.app.naziv_entry.bind("<Return>", self.prikazi_nazive)
        self.app.sifra_entry.bind("<Return>", self.pretrazi_sifru)

    def prikazi_nazive(self, event):
        naziv = self.app.naziv_var.get().strip()
        if not naziv:
            return
        
        try:
            c = self.db_conn.cursor()
            c.execute("SELECT id, barkod, naziv, cijena FROM artikli WHERE naziv LIKE ?", (f"%{naziv}%",))
            rezultati = c.fetchall()
            if rezultati:
                if len(rezultati) > 1:
                    prozor = ctk.CTkToplevel(self.app.root)
                    prozor.title("Rezultati pretrage")
                    prozor.geometry("1000x500")
                    prozor.configure(fg_color=SVJETLO_ZELENA)
                    prozor.transient(self.app.root)
                    prozor.lift()

                    title_frame = ctk.CTkFrame(prozor, fg_color=TAMNO_TIRKIZNA, corner_radius=10)
                    title_frame.pack(fill="x", padx=10, pady=5)
                    ctk.CTkLabel(title_frame, text="Rezultati pretrage", font=self.core.FONT_BOLD, text_color="#000000").pack(side="left", padx=10)
                    ctk.CTkButton(title_frame, text="X", command=prozor.destroy, width=30, fg_color="#FF6F61", hover_color="#E65A50", font=self.core.FONT).pack(side="right", padx=5)

                    tree_frame = ctk.CTkFrame(prozor, fg_color="white", corner_radius=10)
                    tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

                    tree = ttk.Treeview(tree_frame, columns=("Šifra", "Naziv", "Barkod", "Cijena"), show="headings", selectmode="browse")
                    tree.heading("Šifra", text="Šifra")
                    tree.heading("Naziv", text="Naziv")
                    tree.heading("Barkod", text="Barkod")
                    tree.heading("Cijena", text="Cijena")
                    tree.column("Šifra", width=50)
                    tree.column("Naziv", width=200)
                    tree.column("Barkod", width=150)
                    tree.column("Cijena", width=100)
                    tree.pack(side="left", fill="both", expand=True)

                    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
                    tree.configure(yscrollcommand=scrollbar.set)
                    scrollbar.pack(side="right", fill="y")

                    for sifra, barkod, naziv, cijena in rezultati:
                        tree.insert("", "end", values=(sifra, naziv, barkod, f"{cijena:.2f} KM"))

                    def dodaj_selektovano():
                        selektovano = tree.selection()
                        if not selektovano:
                            messagebox.showwarning("Info", "Nijedan artikal nije selektovan!")
                            return
                        item = selektovano[0]
                        sifra, naziv, barkod, cijena = tree.item(item, "values")
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
                                self.app.naziv_var.set("")  # Resetuj samo polje "Naziv"
                                self.core.izracunaj_ukupnu_cijenu()  # Osvježi ukupnu cijenu, ali ne resetuj polje "Dodatno"
                                return
                        item = self.app.tree.insert("", "end", values=(sifra, naziv, str(barkod), f"{cijena:.2f} KM", kolicina, f"{ukupna_cijena:.2f} KM"))
                        # Dodela boje na osnovu broja redova
                        if len(self.app.tree.get_children()) % 2 == 0:
                            self.app.tree.item(item, tags=('evenrow',))
                        else:
                            self.app.tree.item(item, tags=('oddrow',))
                        self.app.ukupno += ukupna_cijena
                        dodaj_stavku_racuna(self.db_conn, self.core.trenutni_racun_id, sifra, naziv, barkod, cijena, kolicina, ukupna_cijena)
                        azuriraj_ukupno_racuna(self.db_conn, self.core.trenutni_racun_id, self.app.ukupno)
                        self.core.izracunaj_ukupnu_cijenu()  # Osvježi ukupnu cijenu, ali ne resetuj polje "Dodatno"
                        prozor.destroy()
                        self.app.naziv_var.set("")  # Resetuj samo polje "Naziv"

                    ctk.CTkButton(prozor, text="Dodaj", command=dodaj_selektovano, fg_color=TAMNO_TIRKIZNA, hover_color="#3A8B93", font=self.core.FONT).pack(pady=10)
                    tree.bind("<Return>", lambda event: dodaj_selektovano())
                else:
                    # Ako je pronađen samo jedan artikal, automatski ga dodaj
                    sifra, barkod, naziv, cijena = rezultati[0]
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
                            self.app.naziv_var.set("")  # Resetuj samo polje "Naziv"
                            self.core.izracunaj_ukupnu_cijenu()  # Osvježi ukupnu cijenu, ali ne resetuj polje "Dodatno"
                            return
                    item = self.app.tree.insert("", "end", values=(sifra, naziv, str(barkod), f"{cijena:.2f} KM", kolicina, f"{ukupna_cijena:.2f} KM"))
                    # Dodela boje na osnovu broja redova
                    if len(self.app.tree.get_children()) % 2 == 0:
                        self.app.tree.item(item, tags=('evenrow',))
                    else:
                        self.app.tree.item(item, tags=('oddrow',))
                    self.app.ukupno += ukupna_cijena
                    dodaj_stavku_racuna(self.db_conn, self.core.trenutni_racun_id, sifra, naziv, barkod, cijena, kolicina, ukupna_cijena)
                    azuriraj_ukupno_racuna(self.db_conn, self.core.trenutni_racun_id, self.app.ukupno)
                    self.app.naziv_var.set("")  # Resetuj samo polje "Naziv"
                    self.core.izracunaj_ukupnu_cijenu()  # Osvježi ukupnu cijenu, ali ne resetuj polje "Dodatno"
            else:
                messagebox.showerror("Greška", "Nijedan artikal nije pronađen!")
        except sqlite3.Error as e:
            messagebox.showerror("Greška", f"Došlo je do greške: {e}")
        self.core.focus_barkod_entry()

    def pretrazi_barkod(self, event):
        barkod = self.app.barkod_var.get().strip()
        if not barkod:
            return
        
        print(f"Skenirani barkod: '{barkod}'")
        
        try:
            c = self.db_conn.cursor()
            c.execute("SELECT id, naziv, cijena FROM artikli WHERE barkod = ?", (barkod,))
            rezultat = c.fetchone()
            print(f"Rezultat pretrage: {rezultat}")
            
            if rezultat:
                sifra, naziv, cijena = rezultat
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
                        self.core.izracunaj_ukupnu_cijenu()
                        self.core.focus_barkod_entry()
                        return
                item = self.app.tree.insert("", "end", values=(sifra, naziv, str(barkod), f"{cijena:.2f} KM", kolicina, f"{ukupna_cijena:.2f} KM"))
                # Dodela boje na osnovu broja redova
                if len(self.app.tree.get_children()) % 2 == 0:
                    self.app.tree.item(item, tags=('evenrow',))
                else:
                    self.app.tree.item(item, tags=('oddrow',))
                self.app.ukupno += ukupna_cijena
                dodaj_stavku_racuna(self.db_conn, self.core.trenutni_racun_id, sifra, naziv, barkod, cijena, kolicina, ukupna_cijena)
                azuriraj_ukupno_racuna(self.db_conn, self.core.trenutni_racun_id, self.app.ukupno)
                self.app.barkod_var.set("")
                self.core.izracunaj_ukupnu_cijenu()
            else:
                messagebox.showerror("Greška", f"Artikal sa barkodom {barkod} nije pronađen!")
                # Selektuj sav tekst u polju za barkod
                self.app.barkod_entry.select_range(0, tk.END)
        except sqlite3.Error as e:
            messagebox.showerror("Greška", f"Došlo je do greške: {e}")
        self.core.focus_barkod_entry()

    def pretrazi_sifru(self, event):
        sifra = self.app.sifra_var.get().strip()
        if not sifra:
            return
        
        rezultat = pretrazi_sifru(self.db_conn, sifra)
        if rezultat:
            barkod, naziv, cijena = rezultat
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
                    self.app.sifra_var.set("")
                    self.core.izracunaj_ukupnu_cijenu()
                    return
            item = self.app.tree.insert("", "end", values=(sifra, naziv, str(barkod), f"{cijena:.2f} KM", kolicina, f"{ukupna_cijena:.2f} KM"))
            # Dodela boje na osnovu broja redova
            if len(self.app.tree.get_children()) % 2 == 0:
                self.app.tree.item(item, tags=('evenrow',))
            else:
                self.app.tree.item(item, tags=('oddrow',))
            self.app.ukupno += ukupna_cijena
            dodaj_stavku_racuna(self.db_conn, self.core.trenutni_racun_id, sifra, naziv, barkod, cijena, kolicina, ukupna_cijena)
            azuriraj_ukupno_racuna(self.db_conn, self.core.trenutni_racun_id, self.app.ukupno)
            self.app.sifra_var.set("")
            self.core.izracunaj_ukupnu_cijenu()
        else:
            messagebox.showerror("Greška", "Artikal nije pronađen!")
        self.core.focus_barkod_entry()