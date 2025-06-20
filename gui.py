import customtkinter as ctk
from config import SVJETLO_ZELENA, TAMNO_TIRKIZNA
from ui_components import setup_ui
from functions import POSFunctions
from windows import WindowManager
from database import get_db_connection, init_db

class POSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("POS Sistem")
        self.root.geometry("1920x1080")
        self.ukupno = 0

        # Kreiraj konekciju i inicijalizuj bazu
        self.db_conn = get_db_connection()
        init_db(self.db_conn)

        # Prvo definiši WindowManager jer je potreban za setup_ui
        self.win = WindowManager(self)

        # Postavi UI (ovo će dodeliti sve UI elemente kao atribute)
        setup_ui(self.root, self)

        # Inicijalizuj POSFunctions nakon što su UI elementi postavljeni
        self.func = POSFunctions(self, self.db_conn)

        # Menu
        menubar = ctk.CTkFrame(self.root, fg_color="#2E5077")  # Usklađeno sa TAMNO_PLAVA
        menubar.pack(fill="x")
        artikli_menu = ctk.CTkButton(menubar, text="Artikli", command=self.show_artikli_menu, fg_color=TAMNO_TIRKIZNA, text_color="#000000")
        artikli_menu.pack(side="left", padx=5)

    def show_artikli_menu(self):
        menu = ctk.CTkFrame(self.root, fg_color=SVJETLO_ZELENA)  # Usklađeno sa SVJETLO_ZELENA
        menu.place(relx=0.02, rely=0.05, anchor="nw")  # Blizu dugmeta "Artikli"
        ctk.CTkButton(menu, text="Unesi Artikal", command=self.win.otvori_artikli_prozor, fg_color=TAMNO_TIRKIZNA, text_color="#000000").pack(pady=5)
        ctk.CTkButton(menu, text="Prikaži Račune", command=self.func.prikazi_racune, fg_color=TAMNO_TIRKIZNA, text_color="#000000").pack(pady=5)
        menu.after(5000, menu.destroy)  # Sakrij nakon 5 sekundi

    def __del__(self):
        if hasattr(self, 'db_conn') and self.db_conn:
            self.db_conn.close()

if __name__ == "__main__":
    root = ctk.CTk()
    app = POSApp(root)
    root.mainloop()
