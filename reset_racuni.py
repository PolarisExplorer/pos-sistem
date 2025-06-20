 SVJETLO_ZELENA

# Povezivanje s bazom (prilagodi ime baze ako koristiš "pos.db" umjesto "pos_database.db")
conn = sqlite3.connect("C:\\Users\\Danilo Ćorović\\Desktop\\POS SISTEM 5\\pos_database.db")
c = conn.cursor()

# Brisanje tablica
c.execute("DROP TABLE IF EXISTS racun_stavke")
c.execute("DROP TABLE IF EXISTS racuni")

# Ponovno kreiranje tablica
c.execute("""
    CREATE TABLE racuni (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        datum_vrijeme TEXT,
        ukupno REAL
    )
""")
c.execute("""
    CREATE TABLE racun_stavke (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        racun_id INTEGER,
        sifra TEXT,
        naziv TEXT,
        barkod TEXT,
        cijena REAL,
        kolicina REAL,
        ukupna_cijena REAL,
        FOREIGN KEY (racun_id) REFERENCES racuni(id)
    )
""")

conn.commit()
conn.close()
print("Tablice 'racuni' i 'racun_stavke' su resetovane.")