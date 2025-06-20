import sqlite3
import pandas as pd
from tkinter import messagebox, filedialog

DB_FILE = "pos.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, timeout=10)
    return conn

def init_db(conn):
    try:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS artikli (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barkod TEXT UNIQUE,
            naziv TEXT NOT NULL,
            cijena REAL NOT NULL
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS racuni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datum_vrijeme TEXT,
            ukupno REAL
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS racun_stavke (
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
        c.execute("""
        CREATE TABLE IF NOT EXISTS aktivni_racuni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            naziv TEXT UNIQUE NOT NULL,
            boja TEXT,
            ukupno REAL DEFAULT 0.0
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS aktivne_stavke (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            racun_id INTEGER,
            sifra TEXT,
            naziv TEXT,
            barkod TEXT,
            cijena REAL,
            kolicina REAL,
            ukupna_cijna REAL,
            FOREIGN KEY (racun_id) REFERENCES aktivni_racuni(id)
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS kategorije (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            artikal_id INTEGER,
            kategorija TEXT,
            FOREIGN KEY (artikal_id) REFERENCES artikli(id)
        )
        """)
        c.execute("DELETE FROM aktivne_stavke")
        c.execute("DELETE FROM aktivni_racuni")
        c.execute("INSERT OR IGNORE INTO aktivni_racuni (naziv, boja) VALUES ('Račun 1', '#FFFFFF')")
        conn.commit()
    except sqlite3.Error as e:
        messagebox.showerror("Greška u bazi", f"Došlo je do greške: {e}")

def pretrazi_barkod(conn, barkod):
    try:
        c = conn.cursor()
        c.execute("SELECT naziv, cijena FROM artikli WHERE barkod = ?", (barkod,))
        rezultat = c.fetchone()
        return rezultat
    except sqlite3.Error as e:
        messagebox.showerror("Greška", f"Došlo je do greške: {e}")
        return None

def pretrazi_sifru(conn, sifra):
    try:
        c = conn.cursor()
        c.execute("SELECT barkod, naziv, cijena FROM artikli WHERE id = ?", (sifra,))
        rezultat = c.fetchone()
        return rezultat
    except sqlite3.Error as e:
        messagebox.showerror("Greška", f"Došlo je do greške: {e}")
        return None

def pretrazi_naziv(conn, naziv):
    try:
        c = conn.cursor()
        c.execute("SELECT id, barkod, cijena FROM artikli WHERE naziv LIKE ?", (f"%{naziv}%",))
        rezultati = c.fetchall()
        return rezultati
    except sqlite3.Error as e:
        messagebox.showerror("Greška", f"Došlo je do greške: {e}")
        return None

def dodaj_artikal_u_bazu(conn, barkod, naziv, cijena):
    try:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO artikli (barkod, naziv, cijena) VALUES (?, ?, ?)",
                  (barkod, naziv, cijena))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        messagebox.showerror("Greška", "Artikal sa ovim barkodom već postoji!")
        return False
    except sqlite3.Error as e:
        messagebox.showerror("Greška", f"Došlo je do greške: {e}")
        return False

def dodaj_aktivni_racun(conn, naziv):
    try:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM aktivni_racuni WHERE naziv = ?", (naziv,))
        if c.fetchone()[0] > 0:
            messagebox.showerror("Greška", f"Račun sa nazivom '{naziv}' već postoji!")
            return None
        c.execute("INSERT INTO aktivni_racuni (naziv, boja) VALUES (?, '#FFFFFF')", (naziv,))
        conn.commit()
        return c.lastrowid
    except sqlite3.Error as e:
        messagebox.showerror("Greška", f"Došlo je do greške: {e}")
        return None

def dohvati_aktivne_racune(conn):
    try:
        c = conn.cursor()
        c.execute("SELECT id, naziv, boja, ukupno FROM aktivni_racuni")
        return c.fetchall()
    except sqlite3.Error as e:
        messagebox.showerror("Greška", f"Došlo je do greške: {e}")
        return []

def dohvati_stavke_racuna(conn, racun_id):
    try:
        c = conn.cursor()
        c.execute("SELECT sifra, naziv, barkod, cijena, kolicina, ukupna_cijena FROM aktivne_stavke WHERE racun_id = ?", (racun_id,))
        return c.fetchall()
    except sqlite3.Error as e:
        messagebox.showerror("Greška", f"Došlo je do greške: {e}")
        return []

def dodaj_stavku_racuna(conn, racun_id, sifra, naziv, barkod, cijena, kolicina, ukupna_cijena):
    try:
        c = conn.cursor()
        c.execute("DELETE FROM aktivne_stavke WHERE racun_id = ? AND barkod = ?", (racun_id, barkod))
        c.execute("""
            INSERT INTO aktivne_stavke (racun_id, sifra, naziv, barkod, cijena, kolicina, ukupna_cijena)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (racun_id, sifra, naziv, barkod, cijena, kolicina, ukupna_cijena))
        conn.commit()
    except sqlite3.Error as e:
        messagebox.showerror("Greška", f"Došlo je do greške: {e}")

def azuriraj_ukupno_racuna(conn, racun_id, ukupno):
    try:
        c = conn.cursor()
        c.execute("UPDATE aktivni_racuni SET ukupno = ? WHERE id = ?", (ukupno, racun_id))
        conn.commit()
    except sqlite3.Error as e:
        messagebox.showerror("Greška", f"Došlo je do greške: {e}")

def zavrsi_racun(conn, racun_id):
    try:
        c = conn.cursor()
        c.execute("SELECT ukupno FROM aktivni_racuni WHERE id = ?", (racun_id,))
        ukupno = c.fetchone()[0]
        datum_vrijeme = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO racuni (datum_vrijeme, ukupno) VALUES (?, ?)", (datum_vrijeme, ukupno))
        novi_racun_id = c.lastrowid
        c.execute("SELECT sifra, naziv, barkod, cijena, kolicina, ukupna_cijena FROM aktivne_stavke WHERE racun_id = ?", (racun_id,))
        stavke = c.fetchall()
        for stavka in stavke:
            c.execute("""
                INSERT INTO racun_stavke (racun_id, sifra, naziv, barkod, cijena, kolicina, ukupna_cijena)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (novi_racun_id, *stavka))
        c.execute("DELETE FROM aktivne_stavke WHERE racun_id = ?", (racun_id,))
        c.execute("DELETE FROM aktivni_racuni WHERE id = ?", (racun_id,))
        conn.commit()
    except sqlite3.Error as e:
        messagebox.showerror("Greška", f"Došlo je do greške: {e}")

def dohvati_kategoriju(conn, kategorija):
    try:
        c = conn.cursor()
        c.execute("""
            SELECT a.id, a.barkod, a.naziv, a.cijena 
            FROM artikli a 
            JOIN kategorije k ON a.id = k.artikal_id 
            WHERE k.kategorija = ? 
            ORDER BY a.id
        """, (kategorija,))
        return c.fetchall()
    except sqlite3.Error as e:
        messagebox.showerror("Greška", f"Došlo je do greške: {e}")
        return []

def dodaj_u_kategoriju(conn, artikal_id, kategorija):
    try:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO kategorije (artikal_id, kategorija) VALUES (?, ?)", (artikal_id, kategorija))
        conn.commit()
        return True
    except sqlite3.Error as e:
        messagebox.showerror("Greška", f"Došlo je do greške: {e}")
        return False

def ukloni_iz_kategorije(conn, artikal_id, kategorija):
    try:
        c = conn.cursor()
        c.execute("DELETE FROM kategorije WHERE artikal_id = ? AND kategorija = ?", (artikal_id, kategorija))
        conn.commit()
        return True
    except sqlite3.Error as e:
        messagebox.showerror("Greška", f"Došlo je do greške: {e}")
        return False

def uvoz_iz_excela(conn):
    try:
        c = conn.cursor()
        file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xls")])
        if not file_path:
            return
        
        df = pd.read_excel(file_path)
        expected_columns = ["Šifra", "Barkod", "Naziv", "Cijena"]
        if not all(col in df.columns for col in expected_columns):
            raise ValueError("Excel mora imati kolone: Šifra, Barkod, Naziv, Cijena!")
        
        print("Učitane kolone iz Excel-a:", df.columns.tolist())
        print("Primer reda:", df.iloc[0].to_dict())
        
        excel_barkodovi = set(df["Barkod"].astype(str).tolist())
        c.execute("SELECT barkod FROM artikli")
        db_barkodovi = set(row[0] for row in c.fetchall())
        barkodovi_za_brisanje = db_barkodovi - excel_barkodovi
        for barkod in barkodovi_za_brisanje:
            c.execute("DELETE FROM artikli WHERE barkod = ?", (barkod,))
        
        for index, row in df.iterrows():
            sifra = row["Šifra"] if not pd.isna(row["Šifra"]) else None
            barkod = str(row["Barkod"]).replace(".0", "") if not pd.isna(row["Barkod"]) else ""
            naziv = str(row["Naziv"]) if not pd.isna(row["Naziv"]) else ""
            cijena = float(row["Cijena"]) if not pd.isna(row["Cijena"]) else 0.0
            
            if not barkod or not naziv:
                continue
            
            print(f"Unosim red: Šifra={sifra}, Barkod={barkod}, Naziv={naziv}, Cijena={cijena}")
            
            if sifra is not None:
                c.execute("INSERT OR REPLACE INTO artikli (id, barkod, naziv, cijena) VALUES (?, ?, ?, ?)",
                          (sifra, barkod, naziv, cijena))
            else:
                c.execute("INSERT OR REPLACE INTO artikli (barkod, naziv, cijena) VALUES (?, ?, ?)",
                          (barkod, naziv, cijena))
        
        conn.commit()
        print("Uvoz završen.")
        messagebox.showinfo("Uspešno", "Artikli su uspešno uvezeni i baza je sinkronizirana!")
    except Exception as e:
        messagebox.showerror("Greška", f"Došlo je do greške prilikom uvoza: {e}")

def export_to_excel(conn):
    try:
        c = conn.cursor()
        c.execute("SELECT id, barkod, naziv, cijena FROM artikli")
        artikli = c.fetchall()
        df = pd.DataFrame(artikli, columns=["Šifra", "Barkod", "Naziv", "Cijena"])
        df.to_excel("artikli.xlsx", index=False)
        print("Izvoz u Excel završen.")
        messagebox.showinfo("Uspešno", "Baza je izvezena u artikli.xlsx!")
    except Exception as e:
        messagebox.showerror("Greška", f"Došlo je do greške prilikom izvoza: {e}")

conn = get_db_connection()
init_db(conn)