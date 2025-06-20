import customtkinter as ctk
from config import SVJETLO_ZELENA, TAMNO_TIRKIZNA
import tkinter as tk
import tkinter.ttk as ttk
import os
from PIL import Image

def setup_ui(root, app):
    root.configure(fg_color=SVJETLO_ZELENA)  # Svetlo zelena pozadina

    # Fontovi
    FONT = ("Segoe UI", 22)
    FONT_BOLD = ("Segoe UI", 24, "bold")
    FONT_TABLE = ("Segoe UI", 18)
    FONT_MONEY = ("Segoe UI", 16)  # Smanjeni font za KM i EUR dugmad
    app.FONT = FONT
    app.FONT_BOLD = FONT_BOLD

    # Podešavanje stila za Treeview
    style = ttk.Style()
    style.configure("Treeview", font=FONT_TABLE, rowheight=40)
    style.configure("Treeview.Heading", font=FONT_TABLE)

    # Levi deo (tabela i unos)
    left_frame = ctk.CTkFrame(root, fg_color=SVJETLO_ZELENA, corner_radius=10)
    left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    entry_frame = ctk.CTkFrame(left_frame, fg_color=SVJETLO_ZELENA)
    entry_frame.pack(fill="x", padx=10, pady=5)
    entry_frame.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(entry_frame, text="Barkod:", font=FONT, text_color="#000000").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    app.barkod_var = ctk.StringVar()
    app.barkod_entry = ctk.CTkEntry(entry_frame, textvariable=app.barkod_var, font=FONT, width=100, placeholder_text="Unesi barkod", fg_color="#FFFFFF", text_color="#000000")
    app.barkod_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    app.artikli_btn = ctk.CTkButton(
        entry_frame,
        text="Artikli",
        image=ctk.CTkImage(light_image=Image.open(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\items.ico")) if os.path.exists(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\items.ico") else None,
        compound="left",
        fg_color=TAMNO_TIRKIZNA,
        hover_color="#3A8B93",
        font=FONT
    )
    app.artikli_btn.grid(row=0, column=2, padx=5, pady=5)

    app.izmjeni_btn = ctk.CTkButton(
        entry_frame,
        text="Izmjeni",
        image=ctk.CTkImage(light_image=Image.open(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\edit.ico")) if os.path.exists(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\edit.ico") else None,
        compound="left",
        fg_color=TAMNO_TIRKIZNA,
        hover_color="#3A8B93",
        font=FONT
    )
    app.izmjeni_btn.grid(row=0, column=3, padx=5, pady=5)

    app.novi_artikal_btn = ctk.CTkButton(
        entry_frame,
        text="Novi artikal",
        fg_color=TAMNO_TIRKIZNA,
        hover_color="#3A8B93",
        font=FONT
    )
    app.novi_artikal_btn.grid(row=1, column=2, padx=5, pady=5)

    ctk.CTkLabel(entry_frame, text="Naziv:", font=FONT, text_color="#000000").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    app.naziv_var = ctk.StringVar()
    app.naziv_entry = ctk.CTkEntry(entry_frame, textvariable=app.naziv_var, font=FONT, width=100, placeholder_text="Unesi naziv", fg_color="#FFFFFF", text_color="#000000")
    app.naziv_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

    ctk.CTkLabel(entry_frame, text="Šifra:", font=FONT, text_color="#000000").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    app.sifra_var = ctk.StringVar()
    app.sifra_entry = ctk.CTkEntry(entry_frame, textvariable=app.sifra_var, font=FONT, width=100, placeholder_text="Unesi šifru", fg_color="#FFFFFF", text_color="#000000")
    app.sifra_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

    ctk.CTkLabel(entry_frame, text="Dodatno:", font=FONT, text_color="#000000").grid(row=3, column=0, padx=5, pady=5, sticky="w")
    app.dodatno_var = ctk.StringVar(value="0,00")
    app.dodatno_entry = ctk.CTkEntry(entry_frame, textvariable=app.dodatno_var, font=FONT, width=100, placeholder_text="Unesi dodatnu vrednost", fg_color="#FFFFFF", text_color="#000000")
    app.dodatno_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

    tree_frame = ctk.CTkFrame(left_frame, fg_color="white", corner_radius=10)
    tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

    app.tree = ttk.Treeview(tree_frame, columns=("Šifra", "Naziv", "Barkod", "Osn. Cijena", "Količina", "Uku. Cijena"), show="headings", selectmode="extended")
    app.tree.heading("Šifra", text="Šifra ▲▼", command=lambda: sort_column(app.tree, "Šifra", False))
    app.tree.heading("Naziv", text="Naziv ▲▼", command=lambda: sort_column(app.tree, "Naziv", False))
    app.tree.heading("Barkod", text="Barkod ▲▼", command=lambda: sort_column(app.tree, "Barkod", False))
    app.tree.heading("Osn. Cijena", text="Osn. Cijena ▲▼", command=lambda: sort_column(app.tree, "Osn. Cijena", False))
    app.tree.heading("Količina", text="Količina ▲▼", command=lambda: sort_column(app.tree, "Količina", False))
    app.tree.heading("Uku. Cijena", text="Uku. Cijena ▲▼", command=lambda: sort_column(app.tree, "Uku. Cijena", False))
    
    app.tree.column("Šifra", width=70)
    app.tree.column("Naziv", width=250)
    app.tree.column("Barkod", width=200)
    app.tree.column("Osn. Cijena", width=130)
    app.tree.column("Količina", width=70)
    app.tree.column("Uku. Cijena", width=130)
    
    app.tree.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=app.tree.yview)
    app.tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    app.tree.tag_configure('evenrow', background='#8bd4e3')
    app.tree.tag_configure('oddrow', background='#8be3dc')

    column_limits = {
        "Šifra": {"min": 50, "max": 100},
        "Naziv": {"min": 150, "max": 300},
        "Barkod": {"min": 150, "max": 250},
        "Osn. Cijena": {"min": 100, "max": 150},
        "Količina": {"min": 50, "max": 100},
        "Uku. Cijena": {"min": 100, "max": 150}
    }

    def enforce_column_widths(event=None):
        for col in column_limits:
            current_width = app.tree.column(col, "width")
            min_width = column_limits[col]["min"]
            max_width = column_limits[col]["max"]
            if current_width < min_width:
                app.tree.column(col, width=min_width)
            elif current_width > max_width:
                app.tree.column(col, width=max_width)

    app.tree.bind("<ButtonRelease-1>", enforce_column_widths)
    app.tree.bind("<Configure>", enforce_column_widths)

    # Frame za "Svi aktivni računi", "Račun 1", "Raniji računi", "QR Kodovi"
    racun_frame = ctk.CTkFrame(left_frame, fg_color=SVJETLO_ZELENA)
    racun_frame.pack(fill="x", padx=10, pady=5)

    # Lijevi podframe za "Svi aktivni računi"
    left_button_frame = ctk.CTkFrame(racun_frame, fg_color=SVJETLO_ZELENA)
    left_button_frame.pack(side="left", padx=5)

    app.svi_racuni_btn = ctk.CTkButton(
        left_button_frame,
        text="Svi aktivni računi",
        image=ctk.CTkImage(light_image=Image.open(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\receipts.ico")) if os.path.exists(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\receipts.ico") else None,
        compound="left",
        fg_color=TAMNO_TIRKIZNA,
        hover_color="#3A8B93",
        font=FONT
    )
    app.svi_racuni_btn.pack(side="left", padx=5, pady=5)

    # Središnja labela "Račun 1"
    app.trenutni_racun_label = ctk.CTkLabel(racun_frame, text="Račun 1", font=FONT_BOLD, text_color="#000000")
    app.trenutni_racun_label.pack(side="left", expand=True)

    # Desni podframe za "Raniji računi" i "QR Kodovi"
    right_button_frame = ctk.CTkFrame(racun_frame, fg_color=SVJETLO_ZELENA)
    right_button_frame.pack(side="right", padx=5)

    app.raniji_racuni_btn = ctk.CTkButton(
        right_button_frame,
        text="Raniji računi",
        image=ctk.CTkImage(light_image=Image.open(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\history.ico")) if os.path.exists(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\history.ico") else None,
        compound="left",
        fg_color=TAMNO_TIRKIZNA,
        hover_color="#3A8B93",
        font=FONT
    )
    app.raniji_racuni_btn.pack(side="left", padx=5, pady=5)

    app.qr_kodovi_btn = ctk.CTkButton(
        right_button_frame,
        text="QR Kodovi",
        fg_color=TAMNO_TIRKIZNA,
        hover_color="#3A8B93",
        font=FONT,
        command=app.show_qr_codes
    )
    app.qr_kodovi_btn.pack(side="left", padx=5, pady=5)

    button_frame = ctk.CTkFrame(left_frame, fg_color=SVJETLO_ZELENA)
    button_frame.pack(fill="x", padx=10, pady=5)

    app.dodaj_btn = ctk.CTkButton(
        button_frame,
        text="Dodaj artikal",
        image=ctk.CTkImage(light_image=Image.open(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\add.ico")) if os.path.exists(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\add.ico") else None,
        compound="left",
        fg_color=TAMNO_TIRKIZNA,
        hover_color="#3A8B93",
        font=FONT
    )
    app.dodaj_btn.pack(side="left", padx=5)

    app.obrisi_btn = ctk.CTkButton(
        button_frame,
        text="Obriši",
        image=ctk.CTkImage(light_image=Image.open(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\delete.ico")) if os.path.exists(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\delete.ico") else None,
        compound="left",
        fg_color="#FF6F61",
        hover_color="#E65A50",
        font=FONT
    )
    app.obrisi_btn.pack(side="left", padx=5)

    app.zavrsi_novi_btn = ctk.CTkButton(
        button_frame,
        text="Završi i Novi Račun",
        image=ctk.CTkImage(light_image=Image.open(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\finish.ico")) if os.path.exists(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\finish.ico") else None,
        compound="left",
        fg_color=TAMNO_TIRKIZNA,
        hover_color="#3A8B93",
        font=FONT
    )
    app.zavrsi_novi_btn.pack(side="left", padx=5)

    # Desni deo (kategorije i total)
    right_frame = ctk.CTkFrame(root, fg_color=SVJETLO_ZELENA, corner_radius=10)
    right_frame.pack(side="right", fill="y", padx=10, pady=10)

    category_frame = ctk.CTkFrame(right_frame, fg_color=SVJETLO_ZELENA)
    category_frame.pack(fill="x", padx=10, pady=5)

    app.voce_btn = ctk.CTkButton(
        category_frame,
        text="Voće",
        image=ctk.CTkImage(light_image=Image.open(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\voce.ico")) if os.path.exists(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\voce.ico") else None,
        compound="left",
        fg_color=TAMNO_TIRKIZNA,
        hover_color="#3A8B93",
        font=FONT,
        height=50,
        command=app.win.prikazi_voce
    )
    app.voce_btn.pack(fill="x", pady=2)

    app.povrce_btn = ctk.CTkButton(
        category_frame,
        text="Povrće",
        image=ctk.CTkImage(light_image=Image.open(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\povrce.ico")) if os.path.exists(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\povrce.ico") else None,
        compound="left",
        fg_color=TAMNO_TIRKIZNA,
        hover_color="#3A8B93",
        font=FONT,
        height=50,
        command=app.win.prikazi_povrce
    )
    app.povrce_btn.pack(fill="x", pady=2)

    app.hljeb_ljubinje_btn = ctk.CTkButton(
        category_frame,
        text="Hljeb Ljubinje",
        image=ctk.CTkImage(light_image=Image.open(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\hljeb_l.ico")) if os.path.exists(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\hljeb_l.ico") else None,
        compound="left",
        fg_color=TAMNO_TIRKIZNA,
        hover_color="#3A8B93",
        font=FONT,
        height=50,
        command=app.win.prikazi_hljeb_ljubinje
    )
    app.hljeb_ljubinje_btn.pack(fill="x", pady=2)

    app.hljeb_dubrave_btn = ctk.CTkButton(
        category_frame,
        text="Hljeb Dubrave",
        image=ctk.CTkImage(light_image=Image.open(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\hljeb_d.ico")) if os.path.exists(r"C:\Users\Danilo Ćorović\Desktop\POS SISTEM\Ikonice\hljeb_d.ico") else None,
        compound="left",
        fg_color=TAMNO_TIRKIZNA,
        hover_color="#3A8B93",
        font=FONT,
        height=50,
        command=app.win.prikazi_hljeb_dubrave
    )
    app.hljeb_dubrave_btn.pack(fill="x", pady=2)

    total_frame = ctk.CTkFrame(right_frame, fg_color=SVJETLO_ZELENA)
    total_frame.pack(fill="x", padx=10, pady=5)

    cijena_frame = ctk.CTkFrame(total_frame, fg_color=TAMNO_TIRKIZNA, corner_radius=10)
    cijena_frame.pack(anchor="w", padx=5, pady=5)
    ctk.CTkLabel(cijena_frame, text="Cijena:", font=FONT_BOLD, text_color="#FFFFFF").pack(padx=5, pady=2)
    app.cijena_label = ctk.CTkLabel(cijena_frame, text="0,00 KM", font=("Segoe UI", 30, "bold"), text_color="#FFFFFF")
    app.cijena_label.pack(padx=5, pady=2)

    # Frame za "Novac od kupca" i dugme "⌫"
    novac_frame = ctk.CTkFrame(total_frame, fg_color=SVJETLO_ZELENA)
    novac_frame.pack(anchor="w", padx=5, pady=2)
    ctk.CTkLabel(novac_frame, text="Novac od kupca:", font=FONT, text_color="#000000").pack(side="top", anchor="w")
    
    app.novac_var = ctk.StringVar()
    app.novac_entry = ctk.CTkEntry(novac_frame, textvariable=app.novac_var, font=FONT, width=120, fg_color="#FFFFFF", text_color="#000000")
    app.novac_entry.pack(side="left", padx=(5, 2), pady=2)

    def reset_novac_and_kusur():
        app.novac_var.set("")  # Briše polje "Novac od kupca"
        try:
            app.core.reset_kusur()  # Pretpostavljena funkcija za resetovanje kusura
        except AttributeError:
            # Ako funkcija ne postoji, ručno postavi kusur na negativnu vrednost ukupne cene
            cijena_text = app.cijena_label.cget("text").replace(" KM", "").replace(",", ".")
            try:
                cijena = float(cijena_text)
                app.kusur_label.configure(text=f"-{cijena:.2f} KM".replace(".", ","))
            except ValueError:
                app.kusur_label.configure(text="0,00 KM")
        app.novac_entry.focus()  # Vraća fokus na polje za unos

    app.ocisti_btn = ctk.CTkButton(
        novac_frame,
        text="⌫",
        fg_color="#FF6F61",
        hover_color="#E65A50",
        font=("Segoe UI", 18, "bold"),
        width=30,
        height=30,
        command=reset_novac_and_kusur
    )
    app.ocisti_btn.pack(side="left", padx=(2, 5), pady=2)

    kusur_frame = ctk.CTkFrame(total_frame, fg_color=TAMNO_TIRKIZNA, corner_radius=10)
    kusur_frame.pack(anchor="w", padx=5, pady=5)
    app.kusur_title_label = ctk.CTkLabel(kusur_frame, text="Kusur:", font=FONT_BOLD, text_color="#FFFFFF")
    app.kusur_title_label.pack(padx=5, pady=2)
    app.kusur_label = ctk.CTkLabel(kusur_frame, text="0,00 KM", font=("Segoe UI", 25, "bold"), text_color="#FFFFFF")
    app.kusur_label.pack(padx=5, pady=2)

    # Tabview za KM i EUR
    tabview = ctk.CTkTabview(total_frame, fg_color=SVJETLO_ZELENA, width=180, height=150)
    tabview.pack(anchor="w", padx=5, pady=2)

    # Dodaj tabove
    tab_km = tabview.add("KM")
    tab_eur = tabview.add("EUR")

    # Frame za KM apoene
    km_frame = ctk.CTkFrame(tab_km, fg_color=SVJETLO_ZELENA)
    km_frame.pack(pady=1)

    # Definiraj apoene za KM
    km_apoeni = [0.10, 0.20, 0.50, 1, 2, 5, 10, 20, 50, 100]

    # Stvori dugmad za KM apoene (3 po redu)
    for i, value in enumerate(km_apoeni):
        text = f"{value:.2f}" if value < 1 else f"{int(value)}"
        btn = ctk.CTkButton(
            km_frame,
            text=text,
            fg_color="#F5C45E",
            hover_color="#E78B48",
            font=FONT_MONEY,
            text_color="#000000",  # Crni font za KM tab
            width=50,
            command=lambda v=value: app.core.add_money(v, "KM")
        )
        btn.grid(row=i // 3, column=i % 3, padx=2, pady=2, sticky="ew")

    # Konfiguracija grid kolona za KM frame
    for i in range(3):
        km_frame.grid_columnconfigure(i, weight=1)

    # Frame za EUR apoene
    eur_frame = ctk.CTkFrame(tab_eur, fg_color=SVJETLO_ZELENA)
    eur_frame.pack(pady=1)

    # Definiraj apoene za EUR
    eur_apoeni = [0.01, 0.02, 0.05, 0.10, 0.20, 0.50, 1, 2, 5, 10, 20, 50, 100]

    # Stvori dugmad za EUR apoene (3 po redu)
    for i, value in enumerate(eur_apoeni):
        text = f"{value:.2f}" if value < 1 else f"{int(value)}"
        btn = ctk.CTkButton(
            eur_frame,
            text=text,
            fg_color="#03A791",
            hover_color="#028A7A",
            font=FONT_MONEY,
            width=50,
            command=lambda v=value: app.core.add_money(v, "EUR")
        )
        btn.grid(row=i // 3, column=i % 3, padx=2, pady=2, sticky="ew")

    # Konfiguracija grid kolona za EUR frame
    for i in range(3):
        eur_frame.grid_columnconfigure(i, weight=1)

def sort_column(tree, col, reverse):
    data = [(tree.set(item, col), item) for item in tree.get_children()]
    try:
        data.sort(key=lambda x: float(x[0].replace(" KM", "").replace(",", ".")), reverse=reverse)
    except ValueError:
        data.sort(key=lambda x: x[0].lower(), reverse=reverse)
    
    for index, (val, item) in enumerate(data):
        tree.move(item, '', index)
    
    tree.heading(col, command=lambda: sort_column(tree, col, not reverse))
