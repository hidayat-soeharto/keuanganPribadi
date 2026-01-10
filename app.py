from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import database as db
from datetime import datetime
import locale
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
# Use environment variable for secret key, fallback to random key for development
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24).hex()  

db.init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.template_filter('rupiah')
def format_rupiah(value):
    try:
        return f"Rp {float(value):,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return value

@app.route('/')
@login_required
def dashboard():
    user_id = session['user_id']
    username = session.get('username')
    
    if username == 'admin':
        ringkasan = db.admin_hitung_ringkasan()
        semua_transaksi = db.admin_ambil_semua_transaksi()
        stats_per_user = db.admin_get_stats_per_user()
        return render_template('admin_dashboard.html', 
                               ringkasan=ringkasan, 
                               transaksi=semua_transaksi,
                               stats_per_user=stats_per_user, 
                               active_page='dashboard')

    sekarang = datetime.now()
    bulan_ini = sekarang.month
    tahun_ini = sekarang.year
    
    ringkasan = db.hitung_ringkasan(user_id, bulan=bulan_ini, tahun=tahun_ini)
    
    transaksi_terbaru = db.ambil_transaksi_limit(user_id, 5)
    
    return render_template('dashboard.html', 
                           ringkasan=ringkasan, 
                           transaksi=transaksi_terbaru, 
                           active_page='dashboard')

@app.route('/api/edit-user', methods=['POST'])
@login_required
def api_edit_user():
    if session.get('username') != 'admin':
        return {'success': False, 'message': 'Akses ditolak.'}
    
    data = request.get_json()
    user_id = data.get('user_id')
    new_username = data.get('username', '')
    new_password = data.get('password', '')
    
    if not user_id:
        return {'success': False, 'message': 'User ID tidak valid.'}
    
    target_user = db.get_user_by_id(user_id)
    if not target_user or target_user['username'] == 'admin':
        return {'success': False, 'message': 'User tidak ditemukan.'}
    
    if new_username != target_user['username'] and db.cek_user(new_username):
        return {'success': False, 'message': 'Username sudah digunakan.'}
    
    if new_password and len(new_password) < 8:
        return {'success': False, 'message': 'Password minimal 8 karakter.'}
    
    if new_password:
        hashed = generate_password_hash(new_password)
        db.update_user(user_id, new_username, hashed)
    else:
        db.update_user(user_id, new_username)
    
    return {'success': True}

# Password reset API removed for security reasons
# In production, implement proper password reset with email verification



@app.route('/transaksi', methods=['GET', 'POST'])
@login_required
def transaksi():
    user_id = session['user_id']
    username = session.get('username')
    
    if request.method == 'POST':
        if username == 'admin':
             flash('Admin tidak dapat melakukan transaksi.', 'danger')
             return redirect(url_for('dashboard'))
             
        aksi = request.form.get('aksi')
        tanggal = request.form.get('tanggal', '')
        tipe = request.form.get('tipe', '')
        kategori = request.form.get('kategori', '')
        catatan = request.form.get('catatan', '')
        
        # Validate required fields
        if not tanggal or not tipe or not kategori:
            flash('Semua field wajib diisi.', 'danger')
            return redirect(url_for('transaksi'))
        
        # Validate and convert jumlah
        try:
            jumlah = float(request.form['jumlah'])
            if jumlah <= 0:
                flash('Jumlah harus lebih dari 0.', 'danger')
                return redirect(url_for('transaksi'))
        except (ValueError, KeyError):
            flash('Jumlah tidak valid. Harap masukkan angka yang benar.', 'danger')
            return redirect(url_for('transaksi'))
        
        if aksi == 'tambah':
            db.tambah_transaksi(user_id, tanggal, tipe, kategori, jumlah, catatan)
            flash('Transaksi berhasil ditambahkan!', 'success')
        elif aksi == 'edit':
            id_transaksi = request.form['id_transaksi']
            db.edit_transaksi(id_transaksi, user_id, tanggal, tipe, kategori, jumlah, catatan)
            flash('Transaksi berhasil diperbarui!', 'success')
            
        return redirect(url_for('transaksi'))
    
    # GET Request with Filters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    filter_tipe = request.args.get('tipe', '')
    
    # Jika tidak ada filter tanggal (awal buka halaman), set default bulan ini
    if start_date is None and end_date is None:
        today = datetime.now()
        start_date = today.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    
    semua_transaksi = db.ambil_semua_transaksi(user_id, start_date, end_date, filter_tipe)
    
    total_jumlah = sum(t['jumlah'] for t in semua_transaksi)
    
    return render_template('transaksi.html', 
                           transaksi=semua_transaksi, 
                           total_jumlah=total_jumlah,
                           active_page='transaksi',
                           filter_tipe=filter_tipe,
                           start_date=start_date,
                           end_date=end_date)

# API untuk mengambil data satu transaksi (untuk Edit Modal)
@app.route('/get_transaksi/<int:id_transaksi>')
@login_required
def get_transaksi(id_transaksi):
    if session.get('username') == 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    user_id = session['user_id']
    transaksi = db.ambil_satu_transaksi(id_transaksi, user_id)
    if transaksi:
        return jsonify({
            'id': transaksi['id'],
            'tanggal': transaksi['tanggal'],
            'tipe': transaksi['tipe'],
            'kategori': transaksi['kategori'],
            'jumlah': transaksi['jumlah'],
            'catatan': transaksi['catatan']
        })
    return jsonify({'error': 'Not found'}), 404

@app.route('/hapus/<int:id_transaksi>')
@login_required
def hapus(id_transaksi):
    if session.get('username') == 'admin':
        flash('Admin tidak diizinkan menghapus data user.', 'danger')
        return redirect(url_for('dashboard'))

    user_id = session['user_id']
    db.hapus_transaksi(id_transaksi, user_id)
    flash('Transaksi berhasil dihapus.', 'warning')
    return redirect(url_for('transaksi'))

@app.route('/laporan')
@login_required
def laporan():
    if session.get('username') != 'admin':
        flash('Halaman ini hanya untuk admin.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get filters from query params
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    filter_user = request.args.get('user_id')
    filter_tipe = request.args.get('tipe', '')
    
    # Default to today's date if not provided
    today = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = today
    if not end_date:
        end_date = today
    
    # Convert user_id to int if present
    filter_user_id = int(filter_user) if filter_user else None
    
    # Get filtered data
    transaksi = db.admin_laporan(start_date, end_date, filter_user_id, filter_tipe)
    
    # Calculate totals
    total_pemasukan = sum(t['jumlah'] for t in transaksi if t['tipe'] == 'Pemasukan')
    total_pengeluaran = sum(t['jumlah'] for t in transaksi if t['tipe'] == 'Pengeluaran')
    
    # Get users for filter dropdown
    users = db.admin_get_all_users()
    
    return render_template('admin_laporan.html',
                           transaksi=transaksi,
                           users=users,
                           total_pemasukan=total_pemasukan,
                           total_pengeluaran=total_pengeluaran,
                           start_date=start_date,
                           end_date=end_date,
                           filter_user=filter_user or '',
                           filter_tipe=filter_tipe,
                           active_page='laporan')

@app.route('/kelola-user')
@login_required
def kelola_user():
    if session.get('username') != 'admin':
        flash('Halaman ini hanya untuk admin.', 'danger')
        return redirect(url_for('dashboard'))
    
    users = db.admin_get_all_users_detail()
    return render_template('admin_kelola_user.html', users=users, active_page='kelola_user')

@app.route('/hapus-user/<int:user_id>')
@login_required
def hapus_user(user_id):
    if session.get('username') != 'admin':
        flash('Halaman ini hanya untuk admin.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get user info
    users = db.admin_get_all_users()
    target_user = None
    for u in users:
        if u['id'] == user_id:
            target_user = u
            break
    
    if not target_user:
        flash('User tidak ditemukan.', 'danger')
        return redirect(url_for('kelola_user'))
    
    db.hapus_user(user_id)
    flash(f'User "{target_user["username"]}" berhasil dihapus!', 'warning')
    return redirect(url_for('kelola_user'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = db.cek_user(username)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Berhasil login!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Username atau password salah.', 'danger')
            
    return render_template('login.html', active_page='login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validate username
        if not username or len(username) < 3:
            flash('Username minimal 3 karakter.', 'danger')
            return render_template('register.html', active_page='register')
        
        # Validate password strength
        if len(password) < 8:
            flash('Password minimal 8 karakter.', 'danger')
            return render_template('register.html', active_page='register')
        
        hashed_password = generate_password_hash(password)
        
        if db.tambah_user(username, hashed_password):
            flash('Registrasi berhasil! Silakan login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username sudah terdaftar.', 'danger')
            
    return render_template('register.html', active_page='register')

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
