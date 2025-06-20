import tkinter as tk
from PIL import Image, ImageTk
import qrcode

class QRProzor(tk.Toplevel):
    def __init__(self, parent, stavke):
        super().__init__(parent)
        self.stavke = stavke  # Lista stavki računa
        self.index = 0  # Trenutni indeks stavke
        self.title("QR Kodovi Artikala")
        self.geometry("700x700")  # Veličina prozora

        # Label za prikaz QR koda
        self.qr_label = tk.Label(self)
        self.qr_label.pack(pady=20)

        # Label za prikaz informacija o artiklu
        self.info_label = tk.Label(self, font=("Arial", 14))
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
        # Generisanje QR koda iz barkoda
        qr = qrcode.QRCode(version=1, box_size=20, border=5)
        qr.add_data(barkod)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        return img

    def show_current(self):
        # Ako smo prešli kraj liste, zatvori prozor
        if self.index >= len(self.stavke):
            self.destroy()
            return

        # Dohvati trenutnu stavku
        stavka = self.stavke[self.index]
        barkod = stavka['barkod']

        # Generiši QR kod i pretvori ga u Tkinter sliku
        img = self.generisi_qr(barkod)
        self.current_photo = ImageTk.PhotoImage(img)
        self.qr_label.configure(image=self.current_photo)

        # Formatiraj tekstualne informacije
        info_text = (f"Šifra: {stavka['sifra']}\n"
                     f"Naziv: {stavka['naziv']}\n"
                     f"Barkod: {stavka['barkod']}\n"
                     f"Cijena: {stavka['cijena']}\n"
                     f"Količina: {stavka['kolicina']}\n"
                     f"Ukupna cijena: {stavka['ukupna_cijena']}")
        self.info_label.configure(text=info_text)

    def show_next(self, event=None):
        # Prelazak na sljedeću stavku
        self.index += 1
        self.show_current()

# Primjer kako pozvati prozor iz otvori_raniji_racun_prozor
def prikazi_qr_kodove(self, stavke):
    QRProzor(self.app.root, stavke)