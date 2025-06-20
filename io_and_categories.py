import tkinter as tk
from config import SVJETLO_ZELENA, TAMNO_TIRKIZNA
from tkinter import messagebox
import customtkinter as ctk
import tkinter.ttk as ttk
import sqlite3
from database import uvoz_iz_excela, export_to_excel, dodaj_stavku_racuna, azuriraj_ukupno_racuna

class IOAndCategories:
    def __init__(self, core):
        self.core = core
        self.app = core.app
        self.db_conn = core.db_conn
        self.setup_category_bindings()

    def setup_category_bindings(self):
        self.app.voce_btn.configure(command=self.prikazi_voce)
        self.app.povrce_btn.configure(command=self.prikazi_povrce)
        self.app.hljeb_ljubinje_btn.configure(command=self.prikazi_hljeb_ljubinje)
        self.app.hljeb_dubrave_btn.configure(command=self.prikazi_hljeb_dubrave)

    def uvoz_iz_excela(self):
        uvoz_iz_excela(self.db_conn)
        messagebox.showinfo("Uspešno", "Baza je uvezena", parent=self.app.root)
        self.core.osvjezi_trenutni_racun()
        self.core.focus_barkod_entry()

    def izvoz_iz_baze(self):
        export_to_excel(self.db_conn)
        messagebox.showinfo("Uspešno", "Baza je izvezena", parent=self.app.root)
        self.core.osvjezi_trenutni_racun()
        self.core.focus_barkod_entry()

    def prikazi_kategoriju(self, kategorija):
        prozor = ctk.CTkToplevel(self.app.root)
        prozor.title(f"Artikli - {kategorija}")
        prozor.geometry("800x600")
        prozor.configure(fg_color=SVJETLO_ZELENA)
        prozor.transient(self.app.root)
        prozor.lift()

        # Title frame
        title_frame = ctk.CTkFrame(prozor, fg_color=TAMNO_TIRKIZNA, corner_radius=10)
        title_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(title_frame, text=f"Artikli - {kategorija}", font=self.core.FONT_BOLD, text_color="#000000").pack(side="left", padx=10)
        ctk.CTkButton(title_frame, text="X", command=prozor.destroy, width=30, fg_color="#FF6F61", hover_color="#E65A50", font=self.core.FONT).pack(side="right", padx=5)

        # Search frame
        search_frame = ctk.CTkFrame(prozor, fg_color=SVJETLO_ZELENA)
        search_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(search_frame, text="Pretraži:", font=self.core.FONT).pack(side="left", padx=5)
        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(search_frame, textvariable=search_var, width=200, font=self.core.FONT)
        search_entry.pack(side="left", padx=5)

        # Tree frame
        tree_frame = ctk.CTkFrame(prozor, fg_color="white", corner_radius=10)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        tree = ttk.Treeview(tree_frame, columns=("Šifra", "Barkod", "Naziv", "Cijena"), show="headings", selectmode="browse")
        tree.heading("Šifra", text="Šifra")
        tree.heading("Barkod", text="Barkod")
        tree.heading("Naziv", text="Naziv")
        tree.heading("Cijena", text="Cijena")
        tree.column("Šifra", width=50)
        tree.column("Barkod", width=150)
        tree.column("Naziv", width=300)
        tree.column("Cijena", width=100)
        tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Funkcija za popunjavanje i filtriranje tabele
        def popuni_tabelu():
            unos = search_var.get().strip().lower()
            tree.delete(*tree.get_children())
            try:
                c = self.db_conn.cursor()
                if unos:
                    c.execute("SELECT id, barkod, naziv, cijena FROM artikli WHERE kategorija = ? AND (naziv LIKE ? OR id LIKE ?)", 
                              (kategorija, f"%{unos}%", f"%{unos}%"))
                else:
                    c.execute("SELECT id, barkod, naziv, cijena FROM artikli WHERE kategorija = ?", (kategorija,))
                artikli = c.fetchall()
                for artikal in artikli:
                    tree.insert("", "end", values=(artikal[0], artikal[1], artikal[2], f"{artikal[3]:.2f} KM"))
            except sqlite3.Error as e:
                messagebox.showerror("Greška", f"Došlo je do greške: {e}")

        # Bind za pretragu
        search_entry.bind("<KeyRelease>", lambda event: popuni_tabelu())
        popuni_tabelu()  # Inicijalno popunjavanje tabele

        def otvori_sve_artikle():
            svi_prozor = ctk.CTkToplevel(self.app.root)
            svi_prozor.title("Svi Artikli")
            svi_prozor.geometry("1000x800")
            svi_prozor.configure(fg_color=SVJETLO_ZELENA)
            svi_prozor.transient(self.app.root)
            svi_prozor.lift()

            search_frame = ctk.CTkFrame(svi_prozor, fg_color=SVJETLO_ZELENA)
            search_frame.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(search_frame, text="Pretraži:", font=self.core.FONT).pack(side="left", padx=5)
            search_var = tk.StringVar()
            search_entry = ctk.CTkEntry(search_frame, textvariable=search_var, width=200, font=self.core.FONT)
            search_entry.pack(side="left", padx=5)

            svi_tree_frame = ctk.CTkFrame(svi_prozor, fg_color="white", corner_radius=10)
            svi_tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

            svi_tree = ttk.Treeview(svi_tree_frame, columns=("Šifra", "Barkod", "Naziv", "Cijena"), show="headings", selectmode="extended")
            svi_tree.heading("Šifra", text="Šifra")
            svi_tree.heading("Barkod", text="Barkod")
            svi_tree.heading("Naziv", text="Naziv")
            svi_tree.heading("Cijena", text="Cijena")
            svi_tree.column("Šifra", width=50)
            svi_tree.column("Barkod", width=150)
            svi_tree.column("Naziv", width=300)
            svi_tree.column("Cijena", width=100)
            svi_tree.pack(side="left", fill="both", expand=True)

            svi_scrollbar = ttk.Scrollbar(svi_tree_frame, orient="vertical", command=svi_tree.yview)
            svi_tree.configure(yscrollcommand=svi_scrollbar.set)
            svi_scrollbar.pack(side="right", fill="y")

            def azuriraj_pretragu():
                unos = search_var.get().strip().lower()
                svi_tree.delete(*svi_tree.get_children())
                try:
                    c = self.db_conn.cursor()
                    if unos:
                        c.execute("SELECT id, barkod, naziv, cijena FROM artikli WHERE naziv LIKE ? OR barkod LIKE ? ORDER BY id", 
                                  (f"%{unos}%", f"%{unos}%"))
                    else:
                        c.execute("SELECT id, barkod, naziv, cijena FROM artikli ORDER BY id")
                    svi_artikli = c.fetchall()
                    for artikal in svi_artikli:
                        svi_tree.insert("", "end", values=(artikal[0], artikal[1], artikal[2], f"{artikal[3]:.2f} KM"))
                except sqlite3.Error as e:
                    messagebox.showerror("Greška", f"Došlo je do greške: {e}")

            search_entry.bind("<KeyRelease>", lambda event: azuriraj_pretragu())
            azuriraj_pretragu()

            def dodaj_u_kategoriju():
                selektovani = svi_tree.selection()
                if not selektovani:
                    messagebox.showwarning("Info", "Nijedan artikal nije selektovan!")
                    return
                
                try:
                    c = self.db_conn.cursor()
                    dodati_artikli = []
                    for item in selektovani:
                        sifra, barkod, naziv, cijena = svi_tree.item(item, "values")
                        c.execute("UPDATE artikli SET kategorija = ? WHERE id = ?", (kategorija, int(sifra)))
                        dodati_artikli.append(naziv)
                    self.db_conn.commit()
                    popuni_tabelu()
                    messagebox.showinfo("Uspeh", f"Dodati artikli u kategoriju '{kategorija}': {', '.join(dodati_artikli)}!")
                    svi_prozor.destroy()
                except sqlite3.Error as e:
                    messagebox.showerror("Greška", f"Došlo je do greške: {e}")

            ctk.CTkButton(svi_prozor, text="Dodaj u kategoriju", command=dodaj_u_kategoriju, fg_color=TAMNO_TIRKIZNA, hover_color="#3A8B93", font=self.core.FONT).pack(pady=10)
            svi_tree.bind("<Return>", lambda event: dodaj_u_kategoriju())

        def obrisi_iz_tabele():
            selektovano = tree.selection()
            if not selektovano:
                messagebox.showwarning("Info", "Nijedan artikal nije selektovan!")
                return
            item = selektovano[0]
            sifra, barkod, naziv, cijena = tree.item(item, "values")

            try:
                c = self.db_conn.cursor()
                c.execute("UPDATE artikli SET kategorija = '' WHERE id = ?", (int(sifra),))
                self.db_conn.commit()
                tree.delete(item)
                messagebox.showinfo("Uspeh", f"Artikal '{naziv}' uklonjen iz kategorije '{kategorija}'!")
            except sqlite3.Error as e:
                messagebox.showerror("Greška", f"Došlo je do greške: {e}")

        def dodaj_u_glavnu_tabelu_i_zatvori(event=None):
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
            self.app.cijena_label.configure(text=f"{self.app.ukupno:.2f} KM")
            prozor.destroy()
            self.core.osvjezi_trenutni_racun()

        tree.bind("<Double-1>", dodaj_u_glavnu_tabelu_i_zatvori)
        tree.bind("<Return>", dodaj_u_glavnu_tabelu_i_zatvori)

        button_frame = ctk.CTkFrame(prozor, fg_color=SVJETLO_ZELENA)
        button_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(button_frame, text="Dodaj u tabelu", command=otvori_sve_artikle, fg_color=TAMNO_TIRKIZNA, hover_color="#3A8B93", font=self.core.FONT).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Obriši iz tabele", command=obrisi_iz_tabele, fg_color="#FF6F61", hover_color="#E65A50", font=self.core.FONT).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Dodaj u glavnu tabelu", command=dodaj_u_glavnu_tabelu_i_zatvori, fg_color=TAMNO_TIRKIZNA, hover_color="#3A8B93", font=self.core.FONT).pack(side="left", padx=5)

        self.core.focus_barkod_entry()

    def prikazi_voce(self):
        self.prikazi_kategoriju("Voće")

    def prikazi_povrce(self):
        self.prikazi_kategoriju("Povrće")

    def prikazi_hljeb_ljubinje(self):
        self.prikazi_kategoriju("Hljeb Ljubinje")

    def prikazi_hljeb_dubrave(self):
        self.prikazi_kategoriju("Hljeb Dubrave")
