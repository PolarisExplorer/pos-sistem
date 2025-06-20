import tkinter as tk
from config import SVJETLO_ZELENA, TAMNO_TIRKIZNA
from tkinter import ttk, messagebox, filedialog
import sqlite3
import pandas as pd
from PIL import Image, ImageTk
from database import dodaj_artikal_u_bazu, dodaj_stavku_racuna, azuriraj_ukupno_racuna, get_db_connection
import customtkinter as ctk
import qrcode

class WindowManager:
    def __init__(self, app):
        self.app = app
        self.kategorije = {
            "Voće": [],
            "Povrće": [],
            "Hljeb Ljubinje": [],
            "Hljeb Dubrave": []
        }

    def dohvati_poslednju_sifru(self):
        """Dohvata sledeću šifru na osnovu maksimalne vrednosti iz Excel-a."""
        try:
            df = pd.read_excel("artikli.xlsx")
            if df.empty:
                return 1
            max_sifra = df['Šifra'].max()
            return max_sifra + 1 if pd.notna(max_sifra) else 1
        except Exception as e:
            print(f"Greška pri čitanju Excela: {e}")
            return 1

    def prikazi_sve_artikle(self):
        prozor = tk.Toplevel(self.app.root)
        prozor.title("Svi Artikli")
        prozor.geometry("800x600")

        search_frame = tk.Frame(prozor)
        search_frame.pack(pady=5)

        ttk.Label(search_frame, text="Pretraži:").pack(side=tk.LEFT, padx=5)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(search_frame, text="Traži", command=lambda: azuriraj_pretragu()).pack(side=tk.LEFT, padx=5)

        tree_frame = tk.Frame(prozor)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        tree = ttk.Treeview(tree_frame, columns=("Šifra", "Naziv", "Barkod", "Cijena"), show="headings", selectmode="extended")
        tree.heading("Šifra", text="Šifra")
        tree.heading("Naziv", text="Naziv")
        tree.heading("Barkod", text="Barkod")
        tree.heading("Cijena", text="Cijena")
        tree.column("Šifra", width=50)
        tree.column("Naziv", width=250)
        tree.column("Barkod", width=150)
        tree.column("Cijena", width=100)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def dodaj_selektovani_artikal():
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
                    dodaj_stavku_racuna(self.app.db_conn, self.app.func.trenutni_racun_id, sifra, naziv, barkod, cijena, nova_kolicina, nova_ukupna_cijena)
                    azuriraj_ukupno_racuna(self.app.db_conn, self.app.func.trenutni_racun_id, self.app.ukupno)
                    self.app.cijena_label.configure(text=f"{self.app.ukupno:.2f} KM")
                    prozor.destroy()
                    return
            self.app.tree.insert("", "end", values=(sifra, naziv, barkod, f"{cijena:.2f} KM", kolicina, f"{ukupna_cijena:.2f} KM"))
            self.app.ukupno += ukupna_cijena
            dodaj_stavku_racuna(self.app.db_conn, self.app.func.trenutni_racun_id, sifra, naziv, barkod, cijena, kolicina, ukupna_cijena)
            azuriraj_ukupno_racuna(self.app.db_conn, self.app.func.trenutni_racun_id, self.app.ukupno)
            self.app.cijena_label.configure(text=f"{self.app.ukupno:.2f} KM")
            prozor.destroy()

        def izmjeni_artikal():
            selektovano = tree.selection()
            if not selektovano:
                messagebox.showwarning("Info", "Nijedan artikal nije selektovan!")
                return
            item = selektovano[0]
            sifra, naziv, barkod, cijena = tree.item(item, "values")
            cijena = float(cijena.replace(" KM", ""))

            uredi_prozor = tk.Toplevel(self.app.root)
            uredi_prozor.title("Izmjeni Artikal")
            uredi_prozor.geometry("400x300")

            ttk.Label(uredi_prozor, text="Barkod:").pack(pady=5)
            barkod_var = tk.StringVar(value=barkod)
            barkod_entry = ttk.Entry(uredi_prozor, textvariable=barkod_var)
            barkod_entry.pack(pady=5)

            ttk.Label(uredi_prozor, text="Naziv:").pack(pady=5)
            naziv_var = tk.StringVar(value=naziv)
            naziv_entry = ttk.Entry(uredi_prozor, textvariable=naziv_var)
            naziv_entry.pack(pady=5)

            ttk.Label(uredi_prozor, text="Cijena:").pack(pady=5)
            cijena_var = tk.StringVar(value=f"{cijena:.2f}")
            cijena_entry = ttk.Entry(uredi_prozor, textvariable=cijena_var)
            cijena_entry.pack(pady=5)

            def spremi_izmjene():
                novi_barkod = barkod_var.get().strip()
                novi_naziv = naziv_var.get().strip()
                nova_cijena_str = cijena_var.get().strip()

                if not novi_barkod or not novi_naziv or not nova_cijna_str:
                    messagebox.showerror("Greška", "Sva polja su obavezna!")
                    return

                try:
                    nova_cijna = float(nova_cijna_str.replace(",", "."))
                    if nova_cijna <= 0:
                        messagebox.showerror("Greška", "Cijena mora biti veća od 0!")
                        return
                except ValueError:
                    messagebox.showerror("Greška", "Cijena mora biti broj!")
                    return

                try:
                    c = self.app.db_conn.cursor()
                    c.execute("UPDATE artikli SET barkod = ?, naziv = ?, cijena = ? WHERE id = ?", 
                              (novi_barkod, novi_naziv, nova_cijna, sifra))
                    self.app.db_conn.commit()
                    azuriraj_pretragu()
                    uredi_prozor.destroy()
                except sqlite3.Error as e:
                    messagebox.showerror("Greška", f"Došlo je do greške: {e}")

            ttk.Button(uredi_prozor, text="Spremi", command=spremi_izmjene).pack(pady=20)

        def dodaj_u_kategoriju(kategorija):
            selektovano = tree.selection()
            if not selektovano:
                messagebox.showwarning("Info", "Nijedan artikal nije selektovan!")
                return
            item = selektovano[0]
            sifra, naziv, barkod, cijena = tree.item(item, "values")
            artikal = (sifra, barkod, naziv, float(cijena.replace(" KM", "")))
            
            if artikal not in self.kategorije[kategorija]:
                self.kategorije[kategorija].append(artikal)
                messagebox.showinfo("Uspeh", f"Artikal '{naziv}' dodan u '{kategorija}'!")
            else:
                messagebox.showinfo("Info", f"Artikal '{naziv}' već postoji u '{kategorija}'!")

        tree.bind("<Return>", lambda event: dodaj_selektovani_artikal())
        ttk.Button(search_frame, text="Dodaj u tabelu", command=dodaj_selektovani_artikal).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Uvezi iz Excela", command=self.app.func.uvoz_iz_excela).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Novi Artikal", command=self.dodaj_novi_artikal).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Izmjeni Artikal", command=izmjeni_artikal).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Dodaj u Voće", command=lambda: dodaj_u_kategoriju("Voće")).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Dodaj u Povrće", command=lambda: dodaj_u_kategoriju("Povrće")).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Dodaj u Hljeb Ljubinje", command=lambda: dodaj_u_kategoriju("Hljeb Ljubinje")).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Dodaj u Hljeb Dubrave", command=lambda: dodaj_u_kategoriju("Hljeb Dubrave")).pack(side=tk.LEFT, padx=5)

        def azuriraj_pretragu():
            unos = search_var.get().strip().lower()
            tree.delete(*tree.get_children())
            try:
                c = self.app.db_conn.cursor()
                if unos:
                    c.execute("SELECT id, barkod, naziv, cijena FROM artikli WHERE naziv LIKE ? OR barkod LIKE ? ORDER BY id", (f"%{unos}%", f"%{unos}%"))
                else:
                    c.execute("SELECT id, barkod, naziv, cijena FROM artikli ORDER BY id")
                artikli = c.fetchall()
                for artikal in artikli:
                    sifra, barkod, naziv, cijena = artikal
                    tree.insert("", "end", values=(sifra, naziv, barkod, f"{cijena:.2f} KM"))
            except sqlite3.Error as e:
                messagebox.showerror("Greška", f"Došlo je do greške: {e}")

        search_entry.bind("<Return>", lambda event: azuriraj_pretragu())
        azuriraj_pretragu()

    def prikazi_voce(self):
        self.prikazi_kategoriju("Voće")

    def prikazi_povrce(self):
        self.prikazi_kategoriju("Povrće")

    def prikazi_hljeb_ljubinje(self):
        self.prikazi_kategoriju("Hljeb Ljubinje")

    def prikazi_hljeb_dubrave(self):
        self.prikazi_kategoriju("Hljeb Dubrave")

    def prikazi_kategoriju(self, naziv_kategorije):
        prozor = ctk.CTkToplevel(self.app.root)
        prozor.title(naziv_kategorije)
        prozor.geometry("1200x800")
        prozor.configure(fg_color=SVJETLO_ZELENA)

        scroll_frame = ctk.CTkScrollableFrame(prozor, fg_color=SVJETLO_ZELENA)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        artikli = self.kategorije.get(naziv_kategorije, [])
        if not artikli:
            ctk.CTkLabel(scroll_frame, text=f"Nema artikala u kategoriji '{naziv_kategorije}'. Dodaj ih putem 'Svi Artikli'.", font=("Arial", 14)).pack(pady=20)
            return

        def dodaj_sliku(artikal_id, frame, img_label):
            image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
            if image_path:
                try:
                    c = self.app.db_conn.cursor()
                    c.execute("UPDATE artikli SET image_path = ? WHERE id = ?", (image_path, artikal_id))
                    self.app.db_conn.commit()

                    img = Image.open(image_path).resize((100, 100), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    img_label.configure(image=photo)
                    frame.image = photo
                except Exception as e:
                    messagebox.showerror("Greška", f"Nije moguće dodati sliku: {e}")

        for i, artikal in enumerate(artikli):
            artikal_id, barkod, naziv, cijena = artikal
            frame = ctk.CTkFrame(scroll_frame, fg_color="white", corner_radius=10, width=200, height=200)
            frame.grid(row=i//3, column=i%3, padx=10, pady=10, sticky="nsew")

            image_path = self.app.db_conn.cursor().execute("SELECT image_path FROM artikli WHERE id = ?", (artikal_id,)).fetchone()
            if image_path and image_path[0]:
                try:
                    img = Image.open(image_path[0]).resize((50, 50), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    img_label = ctk.CTkLabel(frame, image=photo, text="")
                    img_label.image = photo
                except Exception as e:
                    img_label = ctk.CTkLabel(frame, text="Slika nije učitana")
            else:
                img_label = ctk.CTkLabel(frame, text="Nema slike")
            img_label.pack(pady=2)

            ctk.CTkButton(frame, text="Dodaj sliku", command=lambda aid=artikal_id, f=frame, il=img_label: dodaj_sliku(aid, f, il), fg_color=TAMNO_TIRKIZNA).pack(pady=2)

            ctk.CTkLabel(frame, text=f"Naziv: {naziv}", font=("Arial", 10)).pack()
            ctk.CTkLabel(frame, text=f"Cijena: {cijena:.2f} KM", font=("Arial", 10, "bold")).pack()
            ctk.CTkLabel(frame, text=f"Šifra: {artikal_id}", font=("Arial", 10)).pack()
            ctk.CTkLabel(frame, text=f"Barkod: {barkod}", font=("Arial", 10)).pack()

            frame.bind("<Button-1>", lambda event, a=artikal: self.dodaj_na_racun(a))
            for child in frame.winfo_children():
                if not isinstance(child, ctk.CTkButton):
                    child.bind("<Button-1>", lambda event, a=artikal: self.dodaj_na_racun(a))

    def dodaj_na_racun(self, artikal):
        sifra, barkod, naziv, cijena = artikal
        cijena = float(cijena)
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
                dodaj_stavku_racuna(self.app.db_conn, self.app.func.trenutni_racun_id, sifra, naziv, barkod, cijena, nova_kolicina, nova_ukupna_cijena)
                azuriraj_ukupno_racuna(self.app.db_conn, self.app.func.trenutni_racun_id, self.app.ukupno)
                self.app.cijena_label.configure(text=f"{self.app.ukupno:.2f} KM")
                return

        self.app.tree.insert("", "end", values=(sifra, naziv, barkod, f"{cijena:.2f} KM", kolicina, f"{ukupna_cijena:.2f} KM"))
        self.app.ukupno += ukupna_cijena
        dodaj_stavku_racuna(self.app.db_conn, self.app.func.trenutni_racun_id, sifra, naziv, barkod, cijena, kolicina, ukupna_cijena)
        azuriraj_ukupno_racuna(self.app.db_conn, self.app.func.trenutni_racun_id, self.app.ukupno)
        self.app.cijena_label.configure(text=f"{self.app.ukupno:.2f} KM")

    def dodaj_novi_artikal(self):
        print("Pozvana funkcija: dodaj_novi_artikal")
        prozor = tk.Toplevel(self.app.root)
        prozor.title("Novi Artikal")
        prozor.geometry("400x500")

        nova_sifra = self.dohvati_poslednju_sifru()
        print(f"Nova šifra iz Excela: {nova_sifra}")

        ttk.Label(prozor, text=f"Šifra: {nova_sifra}", font=("Arial", 12, "bold")).pack(pady=10)

        ttk.Label(prozor, text="Barkod:").pack(pady=5)
        barkod_var = tk.StringVar()
        barkod_entry = ttk.Entry(prozor, textvariable=barkod_var)
        barkod_entry.pack(pady=5)

        ttk.Label(prozor, text="Naziv artikla:").pack(pady=5)
        naziv_var = tk.StringVar()
        naziv_entry = ttk.Entry(prozor, textvariable=naziv_var)
        naziv_entry.pack(pady=5)

        ttk.Label(prozor, text="Cijena:").pack(pady=5)
        cijena_var = tk.StringVar()
        cijena_entry = ttk.Entry(prozor, textvariable=cijena_var)
        cijena_entry.pack(pady=5)

        def spremi_novi_artikal():
            print("Kliknuto dugme 'Spremi' u dodaj_novi_artikal")
            barkod = barkod_var.get().strip()
            naziv = naziv_var.get().strip()
            cijena_str = cijena_var.get().strip()
            
            print(f"Uneseni podaci - Barkod: {barkod}, Naziv: {naziv}, Cijena: {cijena_str}")

            if not barkod or not naziv or not cijena_str:
                messagebox.showerror("Greška", "Sva polja su obavezna!")
                print("Greška: Sva polja nisu popunjena")
                return
            
            try:
                cijena = float(cijena_str.replace(",", "."))
                print(f"Cijena pretvorena u float: {cijena}")
            except ValueError:
                messagebox.showerror("Greška", "Cijena mora biti broj!")
                print("Greška: Cijena nije validan broj")
                return
            
            if cijena <= 0:
                messagebox.showerror("Greška", "Cijena mora biti veća od 0!")
                print("Greška: Cijena je <= 0")
                return

            try:
                if dodaj_artikal_u_bazu(self.app.db_conn, barkod, naziv, cijena):
                    messagebox.showinfo("Uspeh", f"Artikal je uspešno dodat sa šifrom {nova_sifra}!")
                    print("Artikal uspešno dodat u bazu")
                    prozor.destroy()
                else:
                    messagebox.showerror("Greška", "Neuspešno dodavanje artikla u bazu!")
                    print("Greška: dodaj_artikal_u_bazu vratila False")
            except sqlite3.Error as e:
                messagebox.showerror("Greška", f"Došlo je do greške pri dodavanju artikla: {e}")
                print(f"Greška u bazi: {e}")

        ttk.Button(prozor, text="Spremi", command=spremi_novi_artikal).pack(pady=20)

    def otvori_artikli_prozor(self):
        print("Pozvana funkcija: otvori_artikli_prozor")
        prozor = ctk.CTkToplevel(self.app.root)
        prozor.title("Unos Artikla")
        prozor.geometry("400x500")

        nova_sifra = self.dohvati_poslednju_sifru()
        print(f"Nova šifra iz Excela: {nova_sifra}")

        ctk.CTkLabel(prozor, text=f"Šifra: {nova_sifra}", font=("Arial", 12, "bold"), text_color="white").pack(pady=10)

        ctk.CTkLabel(prozor, text="Barkod:", font=("Arial", 12)).pack(pady=5)
        barkod_var = ctk.StringVar()
        barkod_entry = ctk.CTkEntry(prozor, textvariable=barkod_var)
        barkod_entry.pack(pady=5)

        ctk.CTkLabel(prozor, text="Naziv artikla:", font=("Arial", 12)).pack(pady=5)
        naziv_var = ctk.StringVar()
        naziv_entry = ctk.CTkEntry(prozor, textvariable=naziv_var)
        naziv_entry.pack(pady=5)

        ctk.CTkLabel(prozor, text="Cijena:", font=("Arial", 12)).pack(pady=5)
        cijena_var = ctk.StringVar()
        cijena_entry = ctk.CTkEntry(prozor, textvariable=cijena_var)
        cijena_entry.pack(pady=5)

        def dodaj_artikal_u_bazu_wrapper():
            print("Kliknuto dugme 'Dodaj Artikal' u otvori_artikli_prozor")
            barkod = barkod_var.get().strip()
            naziv = naziv_var.get().strip()
            cijena_str = cijena_var.get().strip()

            print(f"Uneseni podaci - Barkod: {barkod}, Naziv: {naziv}, Cijena: {cijena_str}")

            if not naziv or not barkod or not cijena_str:
                messagebox.showerror("Greška", "Sva polja su obavezna!")
                print("Greška: Sva polja nisu popunjena")
                return
            
            try:
                cijena = float(cijena_str.replace(",", "."))
                print(f"Cijena pretvorena u float: {cijena}")
            except ValueError:
                messagebox.showerror("Greška", "Cijena mora biti broj (npr. 10.50 ili 10,50)!")
                print("Greška: Cijena nije validan broj")
                return
            
            if cijena <= 0:
                messagebox.showerror("Greška", "Cijena mora biti veća od 0!")
                print("Greška: Cijena je <= 0")
                return
            
            try:
                if dodaj_artikal_u_bazu(self.app.db_conn, barkod, naziv, cijena):
                    messagebox.showinfo("Uspeh", f"Artikal je uspešno dodat sa šifrom {nova_sifra}!")
                    print("Artikal uspešno dodat u bazu")
                    prozor.destroy()
                else:
                    messagebox.showerror("Greška", "Neuspešno dodavanje artikla u bazu!")
                    print("Greška: dodaj_artikal_u_bazu vratila False")
            except sqlite3.Error as e:
                messagebox.showerror("Greška", f"Došlo je do greške pri dodavanju artikla: {e}")
                print(f"Greška u bazi: {e}")

        ctk.CTkButton(prozor, text="Dodaj Artikal", command=dodaj_artikal_u_bazu_wrapper, fg_color=TAMNO_TIRKIZNA).pack(pady=20)

    def otvori_raniji_racuni_prozor(self):
        """Prikazuje prozor sa listom ranijih računa."""
        prozor = ctk.CTkToplevel(self.app.root)
        prozor.title("Raniji Računi")
        prozor.geometry("900x900")
        prozor.configure(fg_color=SVJETLO_ZELENA)

        tree_frame = tk.Frame(prozor)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("racun_id", "datum", "ukupno")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        tree.heading("racun_id", text="ID Računa")
        tree.heading("datum", text="Datum")
        tree.heading("ukupno", text="Ukupno (KM)")
        tree.column("racun_id", width=100)
        tree.column("datum", width=200)
        tree.column("ukupno", width=150)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Dohvatanje računa iz baze
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, datum_vrijeme, ukupno FROM racuni ORDER BY datum_vrijeme DESC")
            racuni = cursor.fetchall()
            for racun in racuni:
                racun_id, datum, ukupno = racun
                tree.insert("", tk.END, values=(racun_id, datum, f"{ukupno:.2f} KM"))
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Greška", f"Došlo je do greške: {e}")

        # Otvaranje detalja računa na dvoklik
        tree.bind("<Double-1>", lambda event: self.otvori_raniji_racun_prozor(tree))

    def otvori_raniji_racun_prozor(self, tree):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Upozorenje", "Odaberite račun!")
            return

        racun_id = tree.item(selected_item)['values'][0]
        prozor = ctk.CTkToplevel(self.app.root)
        prozor.title(f"Račun {racun_id}")
        prozor.geometry("800x700")  # Postavljena početna visina na 700 piksela
        prozor.configure(fg_color=SVJETLO_ZELENA)

        # Konfiguracija grid-a za prozor
        prozor.grid_rowconfigure(0, weight=0)  # Red za naslov (fiksna visina)
        prozor.grid_rowconfigure(1, weight=1)  # Red za tabelu (proširivi)
        prozor.grid_rowconfigure(2, weight=0)  # Red za dugme (fiksna visina)
        prozor.grid_columnconfigure(0, weight=1)

        # Frame za naslov
        title_frame = ctk.CTkFrame(prozor, fg_color=TAMNO_TIRKIZNA, corner_radius=10)
        title_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 5))
        ctk.CTkLabel(title_frame, text=f"Stavke računa {racun_id}", font=("Arial", 14, "bold"), text_color="white").pack(side="left", padx=10)
        ctk.CTkButton(title_frame, text="X", command=prozor.destroy, width=30, fg_color="#FF6F61", hover_color="#E65A50").pack(side="right", padx=5)

        # Frame za tabelu
        tree_frame = ctk.CTkFrame(prozor, fg_color="white", corner_radius=10)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))

        # Postavljanje minimalne visine za tree_frame (npr. 300 piksela za prikaz nekoliko redova)
        tree_frame.configure(height=300)  # Fiksna minimalna visina tabele

        columns = ("sifra", "naziv", "barkod", "cijena", "kolicina", "ukupno")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        tree.heading("sifra", text="Šifra")
        tree.heading("naziv", text="Naziv")
        tree.heading("barkod", text="Barkod")
        tree.heading("cijena", text="Cijena (KM)")
        tree.heading("kolicina", text="Količina")
        tree.heading("ukupno", text="Ukupno (KM)")
        tree.column("sifra", width=70)
        tree.column("naziv", width=250)
        tree.column("barkod", width=150)
        tree.column("cijena", width=100)
        tree.column("kolicina", width=80)
        tree.column("ukupno", width=100)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        # Dohvatanje stavki računa iz racun_stavke
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sifra, naziv, barkod, cijena, kolicina, ukupna_cijena
                FROM racun_stavke
                WHERE racun_id = ?
            """, (racun_id,))
            stavke = cursor.fetchall()
            self.stavke = []
            if not stavke:
                ctk.CTkLabel(tree_frame, text="Nema stavki za ovaj račun.", font=("Arial", 14), text_color="black").pack(pady=20)
            else:
                for stavka in stavke:
                    sifra, naziv, barkod, cijena, kolicina, ukupna_cijena = stavka
                    tree.insert("", tk.END, values=(sifra, naziv, barkod, f"{cijena:.2f}", kolicina, f"{ukupna_cijena:.2f}"))
                    self.stavke.append({
                        'sifra': sifra,
                        'naziv': naziv,
                        'barkod': barkod,
                        'cijena': cijena,
                        'kolicina': kolicina,
                        'ukupna_cijena': ukupna_cijena
                    })
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Greška", f"Došlo je do greške: {e}")
            self.stavke = []

        # Dugme za QR kod
        qr_btn = ctk.CTkButton(
            prozor,
            text="QR Kod",
            command=lambda: self.prikazi_qr_kodove_za_racun(self.stavke),
            fg_color=TAMNO_TIRKIZNA,
            hover_color="#3A8B93",
            width=200,
            height=40,
            font=("Arial", 14, "bold")
        )
        qr_btn.grid(row=2, column=0, pady=5, sticky="s")

    def prikazi_qr_kodove_za_racun(self, stavke):
        """Prikazuje QR kodove za artikle sa računa, jedan po prozoru."""
        if not stavke:
            messagebox.showinfo("Info", "Nema stavki za prikaz QR kodova!")
            return
        QRProzor(self.app.root, stavke)

class QRProzor(ctk.CTkToplevel):
    def __init__(self, parent, stavke):
        super().__init__(parent)
        self.stavke = stavke  # Lista stavki računa
        self.index = 0  # Trenutni indeks stavke
        self.title("QR Kod Artikla")
        self.geometry("700x700")
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

        # Prikaz prve stavke
        self.show_current()

        # Osiguravamo da prozor bude ispred i ima fokus
        self.grab_set()
        self.focus_set()

    def generisi_qr(self, barkod):
        """Generiše QR kod iz barkoda."""
        qr = qrcode.QRCode(version=1, box_size=20, border=5)
        qr.add_data(barkod)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        img = img.resize((500, 500), Image.Resampling.LANCZOS)  # Veliki QR kod
        return ImageTk.PhotoImage(img)

    def show_current(self):
        """Prikazuje trenutnu stavku."""
        if self.index >= len(self.stavke):
            self.destroy()
            return

        stavka = self.stavke[self.index]
        barkod = stavka['barkod']

        # Generiši QR kod
        qr_photo = self.generisi_qr(barkod)
        self.qr_label.configure(image=qr_photo)
        self.qr_label.image = qr_photo  # Čuvanje reference

        # Prikaz informacija
        info_text = (f"Šifra: {stavka['sifra']}\n"
                     f"Naziv: {stavka['naziv']}\n"
                     f"Barkod: {stavka['barkod']}\n"
                     f"Cijena: {stavka['cijena']:.2f} KM\n"
                     f"Količina: {stavka['kolicina']}\n"
                     f"Ukupna cijena: {stavka['ukupna_cijena']:.2f} KM")
        
        # Ako je količina veća od 1, postavi crvenu boju, inače crnu
        text_color = "red" if stavka['kolicina'] > 1 else "black"
        self.info_label.configure(text=info_text, text_color=text_color)

    def show_next(self, event=None):
        """Prikazuje sljedeću stavku."""
        self.index += 1
        self.show_current()