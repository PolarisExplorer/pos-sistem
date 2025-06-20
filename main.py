import customtkinter as ctk
from config import SVJETLO_ZELENA, TAMNO_TIRKIZNA
import sqlite3
import tkinter as tk
from core_functions import CoreFunctions
from search_functions import SearchFunctions
from article_functions import ArticleFunctions
from receipt_functions import ReceiptFunctions
from io_and_categories import IOAndCategories
from ui_components import setup_ui
from windows import WindowManager
import qrcode
from PIL import Image, ImageTk
from tkinter import messagebox

print("Tkinter verzija:", tk.TkVersion)

class POSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistem za naplatu - trgovačka radnja 'Ćorović'")
        self.root.iconbitmap(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\cashier.ico")
        self.ukupno = 0.0

        self.db_conn = sqlite3.connect("pos_database.db")
        self.initialize_database()

        # Inicijalizacija WindowManager prije setup_ui
        self.win = WindowManager(self)

        # Postavljanje UI prije inicijalizacije modula
        setup_ui(self.root, self)

        # Inicijalizacija svih modula nakon setup_ui
        self.core = CoreFunctions(self, self.db_conn)
        self.search = SearchFunctions(self.core)
        self.io_categories = IOAndCategories(self.core)
        self.article = ArticleFunctions(self.core, self.io_categories)
        self.receipt = ReceiptFunctions(self.core)

        # Postavljanje bindinga nakon inicijalizacije svih modula
        self.core.setup_basic_bindings()
        self.root.bind("<Delete>", self.article.obrisi_artikal)
        # Uklonjen binding za <Caps_Lock> jer se obrađuje u core_functions.py

        # Učitavanje kategorija iz baze pri pokretanju
        self.ucitaj_kategorije_iz_baze()

        self.clear_active_items()

        self.root.update_idletasks()
        self.root.after(100, lambda: self.root.state('zoomed'))

    def initialize_database(self):
        c = self.db_conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS artikli (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barkod TEXT UNIQUE,
            naziv TEXT,
            cijena REAL,
            kategorija TEXT DEFAULT '',
            image_path TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS aktivni_racuni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            naziv TEXT,
            boja TEXT,
            ukupno REAL
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS aktivne_stavke (
            racun_id INTEGER,
            sifra TEXT,
            naziv TEXT,
            barkod TEXT,
            cijena REAL,
            kolicina REAL,
            ukupna_cijna REAL,
            FOREIGN KEY (racun_id) REFERENCES aktivni_racuni(id)
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS racuni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datum_vrijeme TEXT,
            ukupno REAL
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS racun_stavke (
            racun_id INTEGER,
            sifra TEXT,
            naziv TEXT,
            barkod TEXT,
            cijena REAL,
            kolicina REAL,
            ukupna_cijena REAL,
            FOREIGN KEY (racun_id) REFERENCES racuni(id)
        )''')
        c.execute("SELECT id FROM aktivni_racuni WHERE naziv = 'Račun 1'")
        if not c.fetchone():
            c.execute("INSERT INTO aktivni_racuni (naziv, boja, ukupno) VALUES (?, ?, ?)", ("Račun 1", "#F5EFE7", 0.0))
        self.db_conn.commit()

    def ucitaj_kategorije_iz_baze(self):
        """Učitava artikle iz baze i dodeljuje ih odgovarajućim kategorijama u WindowManager-u."""
        try:
            c = self.db_conn.cursor()
            c.execute("SELECT id, barkod, naziv, cijena, kategorija FROM artikli WHERE kategorija != ''")
            artikli = c.fetchall()
            for artikal in artikli:
                sifra, barkod, naziv, cijena, kategorija = artikal
                if kategorija in self.win.kategorije:
                    self.win.kategorije[kategorija].append((sifra, barkod, naziv, cijena))
        except sqlite3.Error as e:
            messagebox.showerror("Greška", f"Došlo je do greške pri učitavanju kategorija: {e}")

    def clear_active_items(self):
        c = self.db_conn.cursor()
        c.execute("DELETE FROM aktivne_stavke WHERE racun_id = ?", (self.core.trenutni_racun_id,))
        c.execute("UPDATE aktivni_racuni SET ukupno = 0.0 WHERE id = ?", (self.core.trenutni_racun_id,))
        self.db_conn.commit()
        self.core.osvjezi_trenutni_racun()

    def show_qr_codes(self):
        items = self.tree.get_children()
        if not items:
            messagebox.showinfo("Info", "Nema artikala za prikaz QR kodova.")
            return

        qr_window = ctk.CTkToplevel(self.root)
        qr_window.title("QR Kodovi Artikala")
        qr_window.geometry("600x600")
        qr_window.configure(fg_color=SVJETLO_ZELENA)

        qr_window.lift()
        qr_window.focus_force()
        qr_window.attributes('-topmost', True)
        qr_window.grab_set()

        qr_frame = ctk.CTkFrame(qr_window, fg_color=SVJETLO_ZELENA)
        qr_frame.pack(pady=10)

        qr_label = ctk.CTkLabel(qr_frame, text="")
        qr_label.pack()

        details_label = ctk.CTkLabel(qr_window, text="", font=("Arial", 18), text_color="#000000")
        details_label.pack(pady=10)

        item_list = list(items)
        current_index = 0

        def show_current_item():
            nonlocal current_index
            if current_index >= len(item_list):
                qr_window.destroy()
                return
            item = item_list[current_index]
            values = self.tree.item(item, "values")
            barcode = values[2]
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(barcode)
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')
            img = img.resize((300, 300))
            ctk_img = ctk.CTkImage(light_image=img, size=(300, 300))
            qr_label.configure(image=ctk_img)
            qr_label.image = ctk_img
            details_text = f"Šifra: {values[0]}\nNaziv: {values[1]}\nBarkod: {values[2]}\nOsn. Cijena: {values[3]}\nKoličina: {values[4]}\nUku. Cijena: {values[5]}"
            details_label.configure(text=details_text)

        def next_item(event=None):
            nonlocal current_index
            current_index += 1
            show_current_item()

        qr_window.bind("<Return>", next_item)

        show_current_item()

    def __del__(self):
        if self.db_conn:
            self.db_conn.close()

if __name__ == "__main__":
    root = ctk.CTk()
    app = POSApp(root)
    root.mainloop()
