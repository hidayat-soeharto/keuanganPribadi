import sqlite3
from datetime import datetime

DB_NAME = 'keuangan.db'

def init_db():
    """Inisialisasi database dan tabel transaksi jika belum ada."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            tanggal TEXT NOT NULL,
            tipe TEXT NOT NULL,
            kategori TEXT NOT NULL,
            jumlah REAL NOT NULL,
            catatan TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Cek kolom user_id manual untuk memastikan (double check)
    try:
        c.execute('SELECT user_id FROM transaksi LIMIT 1')
    except sqlite3.OperationalError:
         c.execute('ALTER TABLE transaksi ADD COLUMN user_id INTEGER')
         
    conn.commit()
    conn.close()

def tambah_transaksi(user_id, tanggal, tipe, kategori, jumlah, catatan):
    """Menambahkan transaksi baru."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO transaksi (user_id, tanggal, tipe, kategori, jumlah, catatan)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, tanggal, tipe, kategori, jumlah, catatan))
    conn.commit()
    conn.close()



def tambah_user(username, password):
    """Menambahkan user baru."""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def cek_user(username):
    """Mengambil data user berdasarkan username."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    return user

def update_password(user_id, new_password):
    """Update password user."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE users SET password = ? WHERE id = ?', (new_password, user_id))
    conn.commit()
    conn.close()

def hapus_user(user_id):
    """Hapus user dan semua transaksinya."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Hapus transaksi user dulu
    c.execute('DELETE FROM transaksi WHERE user_id = ?', (user_id,))
    # Hapus user
    c.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

def update_user(user_id, username, password=None):
    """Update data user (username dan/atau password)."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if password:
        c.execute('UPDATE users SET username = ?, password = ? WHERE id = ?', (username, password, user_id))
    else:
        c.execute('UPDATE users SET username = ? WHERE id = ?', (username, user_id))
    conn.commit()
    conn.close()

def get_user_by_id(user_id):
    """Mengambil data user berdasarkan ID."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return user


def ambil_semua_transaksi(user_id, start_date=None, end_date=None, tipe=None):
    """Mengambil data transaksi dengan opsi filter tanggal dan tipe."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row 
    c = conn.cursor()
    
    query = 'SELECT * FROM transaksi WHERE user_id = ?'
    params = [user_id]
    
    if start_date:
        query += " AND tanggal >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND tanggal <= ?"
        params.append(end_date)
        
    if tipe and tipe != 'Semua':
        query += " AND tipe = ?"
        params.append(tipe)
        
    query += ' ORDER BY tanggal DESC, id DESC'
    
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows

def ambil_transaksi_limit(user_id, limit=5, bulan=None, tahun=None):
    """Mengambil n transaksi terbaru, opsional difilter per bulan."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = 'SELECT * FROM transaksi WHERE user_id = ?'
    params = [user_id]
    
    if bulan and tahun:
        query += " AND strftime('%m', tanggal) = ? AND strftime('%Y', tanggal) = ?"
        bulan_str = f"{int(bulan):02d}"
        params.extend([bulan_str, str(tahun)])
        
    query += ' ORDER BY tanggal DESC, id DESC LIMIT ?'
    params.append(limit)
    
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows

def hapus_transaksi(id_transaksi, user_id):
    """Menghapus transaksi berdasarkan ID dan user_id."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM transaksi WHERE id = ? AND user_id = ?', (id_transaksi, user_id))
    conn.commit()
    conn.close()

def ambil_satu_transaksi(id_transaksi, user_id):
    """Mengambil satu data transaksi berdasarkan ID dan user_id."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM transaksi WHERE id = ? AND user_id = ?', (id_transaksi, user_id))
    row = c.fetchone()
    conn.close()
    return row

def edit_transaksi(id_transaksi, user_id, tanggal, tipe, kategori, jumlah, catatan):
    """Mengubah data transaksi yang sudah ada."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        UPDATE transaksi 
        SET tanggal = ?, tipe = ?, kategori = ?, jumlah = ?, catatan = ?
        WHERE id = ? AND user_id = ?
    ''', (tanggal, tipe, kategori, jumlah, catatan, id_transaksi, user_id))
    conn.commit()
    conn.close()

def get_available_months(user_id):
    """Mengambil daftar bulan dan tahun yang tersedia dari data transaksi."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  
    c = conn.cursor()
    # Mengambil tahun dan bulan unik dari kolom tanggal (format YYYY-MM-DD)
    c.execute('''
        SELECT DISTINCT strftime('%Y', tanggal) as tahun, strftime('%m', tanggal) as bulan 
        FROM transaksi 
        WHERE user_id = ?
        ORDER BY tahun DESC, bulan DESC
    ''', (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def hitung_ringkasan(user_id, bulan=None, tahun=None):
    """Menghitung total pemasukan, pengeluaran, dan saldo (opsional: per bulan)."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    query_pemasukan = "SELECT SUM(jumlah) FROM transaksi WHERE user_id = ? AND tipe = 'Pemasukan'"
    query_pengeluaran = "SELECT SUM(jumlah) FROM transaksi WHERE user_id = ? AND tipe = 'Pengeluaran'"
    params = [user_id]
    
    if bulan and tahun:
        filter_clause = " AND strftime('%m', tanggal) = ? AND strftime('%Y', tanggal) = ?"
        query_pemasukan += filter_clause
        query_pengeluaran += filter_clause
        # Format bulan menjadi 2 digit string (misal '01', '12')
        bulan_str = f"{int(bulan):02d}"
        params.extend([bulan_str, str(tahun)])

    c.execute(query_pemasukan, params)
    result_pemasukan = c.fetchone()
    pemasukan = result_pemasukan[0] if result_pemasukan and result_pemasukan[0] else 0
    
    c.execute(query_pengeluaran, params)
    result_pengeluaran = c.fetchone()
    pengeluaran = result_pengeluaran[0] if result_pengeluaran and result_pengeluaran[0] else 0
    
    conn.close()
    
    saldo = pemasukan - pengeluaran
    return {
        'pemasukan': pemasukan,
        'pengeluaran': pengeluaran,
        'saldo': saldo
    }

def admin_hitung_ringkasan():
    """Menghitung total ringkasan untuk admin (semua user)."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute("SELECT SUM(jumlah) FROM transaksi WHERE tipe = 'Pemasukan'")
    pemasukan = c.fetchone()[0] or 0
    
    c.execute("SELECT SUM(jumlah) FROM transaksi WHERE tipe = 'Pengeluaran'")
    pengeluaran = c.fetchone()[0] or 0
    
    conn.close()
    
    return {
        'pemasukan': pemasukan,
        'pengeluaran': pengeluaran,
        'saldo': pemasukan - pengeluaran
    }

def admin_ambil_semua_transaksi():
    """Mengambil semua transaksi gabungan dengan data user for admin."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = '''
        SELECT t.*, u.username 
        FROM transaksi t
        LEFT JOIN users u ON t.user_id = u.id
        ORDER BY t.tanggal DESC, t.id DESC
    '''
    
    c.execute(query)
    rows = c.fetchall()
    conn.close()
    return rows

def admin_get_stats_per_user():
    """Mengambil statistik per user untuk chart admin."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = '''
        SELECT u.username,
               COALESCE(SUM(CASE WHEN t.tipe = 'Pemasukan' THEN t.jumlah ELSE 0 END), 0) as pemasukan,
               COALESCE(SUM(CASE WHEN t.tipe = 'Pengeluaran' THEN t.jumlah ELSE 0 END), 0) as pengeluaran
        FROM users u
        LEFT JOIN transaksi t ON u.id = t.user_id
        WHERE u.username != 'admin'
        GROUP BY u.id, u.username
    '''
    
    c.execute(query)
    rows = c.fetchall()
    conn.close()
    return rows

def admin_get_all_users():
    """Mengambil semua user untuk dropdown filter."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE username != 'admin'")
    rows = c.fetchall()
    conn.close()
    return rows

def admin_get_all_users_detail():
    """Mengambil semua user dengan detail untuk manajemen."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT u.id, u.username, 
               COUNT(t.id) as total_transaksi,
               COALESCE(SUM(CASE WHEN t.tipe = 'Pemasukan' THEN t.jumlah ELSE 0 END), 0) as total_pemasukan,
               COALESCE(SUM(CASE WHEN t.tipe = 'Pengeluaran' THEN t.jumlah ELSE 0 END), 0) as total_pengeluaran
        FROM users u
        LEFT JOIN transaksi t ON u.id = t.user_id
        WHERE u.username != 'admin'
        GROUP BY u.id, u.username
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def admin_laporan(start_date=None, end_date=None, user_id=None, tipe=None):
    """Mengambil laporan transaksi dengan filter untuk admin."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = '''
        SELECT t.*, u.username 
        FROM transaksi t
        LEFT JOIN users u ON t.user_id = u.id
        WHERE 1=1
    '''
    params = []
    
    if start_date:
        query += " AND t.tanggal >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND t.tanggal <= ?"
        params.append(end_date)
    
    if user_id:
        query += " AND t.user_id = ?"
        params.append(user_id)
        
    if tipe and tipe != 'Semua':
        query += " AND t.tipe = ?"
        params.append(tipe)
        
    query += ' ORDER BY t.tanggal DESC, t.id DESC'
    
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows
