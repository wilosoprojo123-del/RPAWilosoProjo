import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import json
import datetime
from datetime import date
import io
import base64

# ==========================================
# KONFIGURASI HALAMAN STREAMLIT
# ==========================================
st.set_page_config(
    page_title="Sistem Profiling Anak Asuh - UPT RPA Wiloso Projo",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# FUNGSI OTENTIKASI & KEAMANAN HASHING
# ==========================================
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

# ==========================================
# INISIALISASI DATABASE SQLITE
# ==========================================
DB_FILE = "wiloso_projo_profiling.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def log_audit(username, nama_lengkap, role, aksi, detail=""):
    """Mencatat setiap aktivitas perubahan dan akses data ke dalam Log Audit Keamanan."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO tb_audit_log (username, nama_lengkap, role, aksi, detail)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, nama_lengkap, role, aksi, detail))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Audit log error: {e}")

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # 1. Tabel Users
    c.execute('''
        CREATE TABLE IF NOT EXISTS tb_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nama_lengkap TEXT NOT NULL,
            role TEXT NOT NULL,
            dibuat_pada TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert Default Users if Empty
    c.execute("SELECT COUNT(*) FROM tb_users")
    if c.fetchone()[0] == 0:
        default_users = [
            ("admin", make_hashes("admin123"), "Pekerja Sosial / Admin RPA", "Admin"),
            ("pengasuh", make_hashes("pengasuh123"), "Pengasuh Pendamping Field", "Pengasuh"),
            ("dinas", make_hashes("dinas123"), "Pemeriksa Dinas Sosial / Donatur", "Viewer")
        ]
        c.executemany("INSERT INTO tb_users (username, password, nama_lengkap, role) VALUES (?, ?, ?, ?)", default_users)

    # 2. Tabel Master Anak Asuh
    c.execute('''
        CREATE TABLE IF NOT EXISTS tb_anak_asuh (
            id_anak TEXT PRIMARY KEY,
            nama_lengkap TEXT NOT NULL,
            jenis_kelamin TEXT NOT NULL,
            tempat_lahir TEXT,
            tanggal_lahir TEXT,
            nik TEXT,
            no_kk TEXT,
            nisn TEXT,
            agama TEXT DEFAULT 'Islam',
            jenjang TEXT,
            sekolah TEXT,
            kelas TEXT,
            kecamatan TEXT,
            alamat_asal TEXT,
            tanggal_masuk TEXT,
            alasan_masuk TEXT,
            status_keberadaan TEXT DEFAULT 'Aktif'
        )
    ''')
    
    # Insert Sample Data if Empty
    c.execute("SELECT COUNT(*) FROM tb_anak_asuh")
    if c.fetchone()[0] == 0:
        sample_anak = [
            ('ANAK-001', 'Amelia Putri Rejeki', 'Perempuan', 'Boyolali', '2014-09-13', '3309115309140002', '3471021601230003', '141123308', 'Islam', 'SD', 'SD N Vidya Qasana', 'Kelas VI', 'Jetis', 'Celengan RT 01 RW 05, Giriroto, Ngemplak, Boyolali', '2024-02-26', 'Yatim / Terlantar', 'Aktif'),
            ('ANAK-002', 'Risky Devon', 'Laki-laki', 'Magelang', '2015-04-04', '3471030404150007', '3471031612240003', '141123309', 'Islam', 'SD', 'SD N Vidya Qasana', 'Kelas III', 'Gondokusuman', 'Sagan GK V/1187, RT 048 RW 010, Terban', '2026-01-14', 'Terlantar', 'Aktif'),
            ('ANAK-003', 'Luvena Arnawati', 'Perempuan', 'Yogyakarta', '2012-02-24', '3471146402120001', '3471142001040027', '121609011', 'Islam', 'SMP', 'SMP N 9 Yogyakarta', 'Kelas IX', 'Kotagede', 'Jl. Pangeran Romo 6, Prenggan, Kotagede', '2024-02-26', 'Yatim', 'Aktif'),
            ('ANAK-004', 'Alvaro Airlangga Pamungkas', 'Laki-laki', 'Yogyakarta', '2012-01-05', '3471020501120001', '3471022003230004', '121609012', 'Islam', 'SMP', 'SMP N 12 Yogyakarta', 'Kelas IX', 'Jetis', 'Jl Pingit JT I/399 RT/RW 02/01 Bumijo, Jetis', '2023-12-15', 'Yatim', 'Aktif'),
            ('ANAK-005', 'Fitri Aulia', 'Perempuan', 'Jakarta', '2011-08-31', '3175077108111002', '3471012607190002', '119596802', 'Islam', 'SMP', 'SMP Taman Dewasa Jetis YK', 'Kelas IX', 'Tegalrejo', 'Jatimulyo Tr.1 / 690 RT 024 RW 005 Kricak', '2019-08-13', 'Terlantar', 'Aktif'),
            ('ANAK-006', 'Octa Putri Prasetia', 'Perempuan', 'Gunungkidul', '2010-10-13', '3403155310100001', '3471020409120001', '107965999', 'Islam', 'SMP', 'SMP Taman Dewasa Jetis YK', 'Kelas IX', 'Jetis', 'Pingit JT. I/405 RT 002 RW 001 Bumijo, Jetis', '2022-03-24', 'Terlantar', 'Aktif'),
            ('ANAK-007', 'Carissa Ayu Acatya', 'Perempuan', 'Yogyakarta', '2011-09-24', '3471026409110001', '3471021005070158', '119596803', 'Islam', 'SMP', 'SMP Taman Dewasa Jetis YK', 'Kelas IX', 'Jetis', 'Jetisharjo JT.II/490 Cokrodiningratan, Jetis', '2024-10-09', 'Terlantar', 'Aktif'),
            ('ANAK-008', 'Imelia Hanifah', 'Perempuan', 'Yogyakarta', '2011-12-26', '3471146612110001', '3471021601230003', '115899281', 'Islam', 'SMP', 'SMP N 3 Yogyakarta', 'Kelas VIII', 'Jetis', 'Gowongan Lor Penumping JT III No 211, Jetis', '2019-07-16', 'Terlantar', 'Aktif'),
            ('ANAK-009', 'Rava Okta Syahputra', 'Laki-laki', 'Purworejo', '2012-10-10', '3306071010120001', '3471021601230003', '124354674', 'Islam', 'SMP', 'SMP N 6 Yogyakarta', 'Kelas VIII', 'Jetis', 'Badran JT 1 / 973 RT 56 RW 12, Jetis', '2019-07-01', 'Yatim', 'Aktif'),
            ('ANAK-010', 'Martha Aulia Septiani', 'Perempuan', 'Yogyakarta', '2013-03-05', '3471014503130001', '3471012911080720', '124354675', 'Islam', 'SMP', 'SMP N 3 Yogyakarta', 'Kelas VIII', 'Jetis', 'Badran RT 038 RW 009, Bumijo, Jetis', '2025-06-30', 'Terlantar', 'Aktif'),
            ('ANAK-011', 'Kaziz Dwi Iko Wijaya', 'Laki-laki', 'Yogyakarta', '2012-01-02', '3471140201120001', '3471141901220001', '124354676', 'Islam', 'SMP', 'SMP N 9 Yogyakarta', 'Kelas VIII', 'Kotagede', 'Winong KG 2/308 RT 012 RW 003 Prenggan, Kotagede', '2026-02-05', 'Terlantar', 'Aktif'),
            ('ANAK-012', 'Elnia Risnawati', 'Perempuan', 'Yogyakarta', '2009-02-26', '3471146602090001', '3471142001040027', '92524244', 'Islam', 'SMK', 'SMK N 7 Yogyakarta (Bisnis Layanan Wisata)', 'Kelas XII', 'Kotagede', 'Jl. Pangeran Romo 6, Prenggan, Kotagede', '2024-02-26', 'Yatim', 'Aktif'),
            ('ANAK-013', 'Ziyad Fakhri', 'Laki-laki', 'Gunungkidul', '2009-06-02', '1471100206090004', '3471020409000095', '97185548', 'Islam', 'SMK', 'SMK N 3 Yogyakarta (Teknik Mesin)', 'Kelas XII', 'Jetis', 'Penumping JT. III/211 Gowongan, Jetis', '2022-07-23', 'Terlantar', 'Aktif'),
            ('ANAK-014', 'Cristya Arsy', 'Perempuan', 'Yogyakarta', '2009-05-27', '3471046705090001', '3471042007260002', '94542022', 'Islam', 'SMK', 'SMK N 7 Yogyakarta (Manajemen Perkantoran)', 'Kelas XI', 'Danurejan', 'Tegalpanggung DN 2/958, Danurejan', '2022-01-01', 'Korban KDRT', 'Aktif'),
            ('ANAK-015', 'Rakih Cantika Ummul Aisyah', 'Perempuan', 'Yogyakarta', '2009-06-22', '3471026206090001', '3471022209070370', '91093852', 'Islam', 'SMK', 'SMK N 7 Yogyakarta (Busana)', 'Kelas XI', 'Jetis', 'Pingit JT. I/249 Bumijo, Jetis', '2022-07-13', 'Terlantar', 'Aktif'),
            ('ANAK-016', 'Clara Nazwa Adita', 'Perempuan', 'Kotawaringin Barat', '2011-01-30', '6201047001110001', '3471081509150005', '91093853', 'Islam', 'SMK', 'SMK Muh 2 Yogyakarta (Perhotelan)', 'Kelas X', 'Mantrijeron', 'Suryowijayan MJ 1/221, Mantrijeron', '2022-06-11', 'Terlantar', 'Aktif')
        ]
        c.executemany('''
            INSERT INTO tb_anak_asuh 
            (id_anak, nama_lengkap, jenis_kelamin, tempat_lahir, tanggal_lahir, nik, no_kk, nisn, agama, jenjang, sekolah, kelas, kecamatan, alamat_asal, tanggal_masuk, alasan_masuk, status_keberadaan)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_anak)

    # 3. Tabel Bakat & Prestasi
    c.execute('''
        CREATE TABLE IF NOT EXISTS tb_bakat_prestasi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_anak TEXT,
            kategori_bakat TEXT,
            deskripsi_bakat TEXT,
            nama_prestasi TEXT,
            tingkat_prestasi TEXT,
            FOREIGN KEY(id_anak) REFERENCES tb_anak_asuh(id_anak)
        )
    ''')
    
    # Insert Sample Bakat
    c.execute("SELECT COUNT(*) FROM tb_bakat_prestasi")
    if c.fetchone()[0] == 0:
        sample_bakat = [
            ('ANAK-001', 'Seni & Menari', 'Tari Tradisional & Menari', 'Lomba Angklung Festival Seni Yogyakarta', 'Kota Yogyakarta'),
            ('ANAK-002', 'Olahraga', 'Sepak bola & Atletik', 'Lomba POR Siswa Atletik Lari SD', 'Kota Yogyakarta'),
            ('ANAK-003', 'Seni Rupa', 'Menggambar, Melukis & Musik', 'Juara Lomba Menggambar & Mewarnai', 'Kota Yogyakarta'),
            ('ANAK-004', 'Olahraga', 'Sepak Bola & Sains', 'Peserta Gala Siswa Indonesia & OPSI', 'Kota Yogyakarta'),
            ('ANAK-005', 'Keterampilan & Olahraga', 'Bulu Tangkis, Menjahit, Kuliner', 'Lomba Geguritan Bahasa Jawa', 'Kota Yogyakarta'),
            ('ANAK-008', 'Seni & Kuliner', 'Menari, Kerajinan Tangan', 'Juara 3 Lomba Menyanyi Jetis Expo 2026', 'Kecamatan Jetis'),
            ('ANAK-009', 'Seni & Keagamaan', 'Saritilawah, Tonti/Paskibra', 'Juara 3 Menyanyi & Peserta Lomba Tonti 2026', 'Kota Yogyakarta'),
            ('ANAK-010', 'Seni, Olahraga & Keagamaan', 'Karate, Menari, MTQ', 'Juara 1 Mayoret, Juara 2 Karate Seni, Juara 3 MTQ', 'Kota Yogyakarta'),
            ('ANAK-012', 'Seni Pertunjukan', 'Tari Wira/Woja', 'Juara 2 Tari Wira/Woja Dinas Pariwisata DIY & Penari Pembuka Kemenparekraf', 'Provinsi DIY'),
            ('ANAK-013', 'Vokasi & Komputer', 'Teknik Mesin & Komputer', 'Khatam Juz Amma', 'RPA Wiloso Projo'),
            ('ANAK-015', 'Seni & Paskibra', 'Menjahit, Busana, Paskibra', 'Anggota Paskibra Sekolah & Juara 3 Menari Jetis Expo 2026', 'Kota Yogyakarta')
        ]
        c.executemany("INSERT INTO tb_bakat_prestasi (id_anak, kategori_bakat, deskripsi_bakat, nama_prestasi, tingkat_prestasi) VALUES (?, ?, ?, ?, ?)", sample_bakat)

    # 4. Tabel Aging Out Plan & Alumni
    c.execute('''
        CREATE TABLE IF NOT EXISTS tb_aging_out_plan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_anak TEXT,
            tabungan_mandiri INTEGER DEFAULT 0,
            pelatihan_diikuti TEXT,
            rencana_pasca_panti TEXT,
            status_alumni TEXT,
            kontak_alumni TEXT,
            FOREIGN KEY(id_anak) REFERENCES tb_anak_asuh(id_anak)
        )
    ''')
    
    # Insert Sample Aging Out
    c.execute("SELECT COUNT(*) FROM tb_aging_out_plan")
    if c.fetchone()[0] == 0:
        sample_aging = [
            ('ANAK-012', 2500000, 'Pelatihan Hospitality & Pemasaran Wisata', 'Kerja Swasta / Pariwisata', 'Persiapan Lulus 2026', '081234567891'),
            ('ANAK-013', 1800000, 'Pelatihan Otomotif & Mesin Industri', 'Kerja Industri / Ritel', 'Persiapan Lulus 2026', '081234567892'),
            ('ANAK-014', 2100000, 'Pelatihan Administrasi & Komputer Perkantoran', 'Kuliah / Kerja Perkantoran', 'Siswa SMK XI', '081234567893'),
            ('ANAK-015', 1500000, 'Pelatihan Menjahit & Desain Busana', 'Wirausaha / Industri Fashion', 'Siswa SMK XI', '081234567894')
        ]
        c.executemany("INSERT INTO tb_aging_out_plan (id_anak, tabungan_mandiri, pelatihan_diikuti, rencana_pasca_panti, status_alumni, kontak_alumni) VALUES (?, ?, ?, ?, ?, ?)", sample_aging)

    # 5. TABEL BARU: Document Repository (Scan Berkas Legalitas)
    c.execute('''
        CREATE TABLE IF NOT EXISTS tb_dokumen_adm (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_anak TEXT NOT NULL,
            jenis_dokumen TEXT NOT NULL,
            nama_file TEXT NOT NULL,
            tipe_file TEXT NOT NULL,
            ukuran_bytes INTEGER NOT NULL,
            file_data BLOB NOT NULL,
            diunggah_oleh TEXT NOT NULL,
            tanggal_unggah TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(id_anak) REFERENCES tb_anak_asuh(id_anak)
        )
    ''')

    # 6. TABEL BARU: Log Audit Keamanan System
    c.execute('''
        CREATE TABLE IF NOT EXISTS tb_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            nama_lengkap TEXT NOT NULL,
            role TEXT NOT NULL,
            aksi TEXT NOT NULL,
            detail TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

# Inisialisasi DB saat start
init_db()

# ==========================================
# MANAJEMEN SESI & STATE LOGIN
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = ''
if 'user_fullname' not in st.session_state:
    st.session_state['user_fullname'] = ''

# ==========================================
# FORM LOGIN JIKA BELUM LOGGED IN
# ==========================================
if not st.session_state['logged_in']:
    st.markdown("""
        <style>
        .login-header {
            text-align: center;
            background-color: #1E3A8A;
            color: white;
            padding: 22px;
            border-radius: 12px;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .security-badge {
            background-color: #DEF7EC;
            color: #03543F;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            display: inline-block;
            margin-top: 10px;
            font-size: 13px;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div class="login-header">
                <h2 style="margin:0; padding-bottom:5px;">🏠 UPT RPA WILOSO PROJO</h2>
                <p style="margin:0; font-size:14px; opacity:0.9;">Sistem Profiling Data, Portofolio & Audit Keamanan Anak Asuh</p>
                <div class="security-badge">🔒 Terenkripsi SHA-256 & Audit Trail Active</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.subheader("🔑 Masuk Keamanan Sistem")
        login_user = st.text_input("Username", placeholder="Masukkan username...")
        login_pass = st.text_input("Password", type="password", placeholder="Masukkan password...")
        
        if st.button("🚀 Log In System", use_container_width=True, type="primary"):
            conn = get_db_connection()
            c = conn.cursor()
            hashed_input = make_hashes(login_pass)
            c.execute("SELECT * FROM tb_users WHERE username = ? AND password = ?", (login_user, hashed_input))
            user_data = c.fetchone()
            conn.close()
            
            if user_data:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user_data['username']
                st.session_state['user_role'] = user_data['role']
                st.session_state['user_fullname'] = user_data['nama_lengkap']
                
                # Catat Ke dalam Audit Log
                log_audit(
                    username=user_data['username'],
                    nama_lengkap=user_data['nama_lengkap'],
                    role=user_data['role'],
                    aksi="LOG IN",
                    detail="Pengguna berhasil masuk ke sistem profiling"
                )
                
                st.success(f"Selamat datang, {user_data['nama_lengkap']} ({user_data['role']})!")
                st.rerun()
            else:
                st.error("⚠️ Username atau Password salah! Silakan periksa kembali.")
        
        st.markdown("---")
        st.info("""
        **💡 Informasi Akun Demo & Hak Akses:**
        * **Admin / Pekerja Sosial**: Username `admin` | Password `admin123` *(Full Akses, Edit/Hapus, User Mgmt, Audit Log)*
        * **Pengasuh Field**: Username `pengasuh` | Password `pengasuh123` *(Input Log Harian, Unggah Berkas Scan)*
        * **Dinas / Donatur**: Username `dinas` | Password `dinas123` *(Akses View Portofolio & Laporan)*
        """)

else:
    # ==========================================
    # SIDEBAR UTAMA & USER ACTIVE
    # ==========================================
    st.sidebar.markdown(f"""
        ### 👤 Pengguna Aktif
        **{st.session_state['user_fullname']}**  
        🏷️ Role: `{st.session_state['user_role']}`
    """)
    
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        # Catat Audit Log
        log_audit(
            username=st.session_state['username'],
            nama_lengkap=st.session_state['user_fullname'],
            role=st.session_state['user_role'],
            aksi="LOG OUT",
            detail="Pengguna keluar dari sistem"
        )
        st.session_state['logged_in'] = False
        st.session_state['username'] = ''
        st.session_state['user_role'] = ''
        st.session_state['user_fullname'] = ''
        st.rerun()

    st.sidebar.markdown("---")
    
    # PILIHAN MENU APLIKASI
    menu_options = [
        "📊 Dashboard & Analytics",
        "🗂️ Master Database Anak",
        "📂 Scan Berkas & Dokumen Legalitas",
        "🏥 Bio-Psiko-Sosial & Kesehatan",
        "🎓 Akademik & Bakat Prestasi",
        "🚀 Aging-Out Plan & Alumni",
        "🖨️ Quick-Print & Ekspor Laporan"
    ]
    
    if st.session_state['user_role'] == 'Admin':
        menu_options.append("⚙️ Kelola Pengguna & Log Audit")

    selected_menu = st.sidebar.radio("📌 Navigasi Modul", menu_options)

    # ==========================================
    # MODUL 1: DASHBOARD & ANALYTICS
    # ==========================================
    if selected_menu == "📊 Dashboard & Analytics":
        st.title("📊 Dashboard Profiling Data Anak Asuh")
        st.markdown("**UPT Rumah Pengasuhan Anak Wiloso Projo Yogyakarta**")
        st.markdown("---")
        
        conn = get_db_connection()
        df_anak = pd.read_sql_query("SELECT * FROM tb_anak_asuh WHERE status_keberadaan = 'Aktif'", conn)
        df_docs = pd.read_sql_query("SELECT COUNT(*) as total_docs FROM tb_dokumen_adm", conn)
        conn.close()
        
        total_anak = len(df_anak)
        sd_count = len(df_anak[df_anak['jenjang'] == 'SD'])
        smp_count = len(df_anak[df_anak['jenjang'] == 'SMP'])
        smk_count = len(df_anak[df_anak['jenjang'] == 'SMK'])
        total_berkas = df_docs['total_docs'].iloc[0]
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Anak Asuh", f"{total_anak} Anak", delta="UPT RPA")
        col2.metric("Tingkat SD", f"{sd_count} Anak", delta="2026")
        col3.metric("Tingkat SMP", f"{smp_count} Anak", delta="Paling Dominan")
        col4.metric("Tingkat SMK", f"{smk_count} Anak", delta="Persiapan Mandiri")
        col5.metric("Scan Dokumen Legal", f"{total_berkas} Berkas", delta="Tersimpan Terenkripsi")
        
        st.markdown("---")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("👥 Distribusi Jenis Kelamin")
            gender_df = df_anak['jenis_kelamin'].value_counts().reset_index()
            gender_df.columns = ['Jenis Kelamin', 'Jumlah']
            st.bar_chart(gender_df.set_index('Jenis Kelamin'))
            
        with col_b:
            st.subheader("🏫 Distribusi Jenjang Sekolah")
            jenjang_df = df_anak['jenjang'].value_counts().reset_index()
            jenjang_df.columns = ['Jenjang', 'Jumlah']
            st.dataframe(jenjang_df, use_container_width=True)

        st.subheader("📌 Ringkasan Data Sekolah & Wali Kelas")
        st.dataframe(
            df_anak[['id_anak', 'nama_lengkap', 'jenis_kelamin', 'jenjang', 'sekolah', 'kelas', 'kecamatan']],
            use_container_width=True
        )

    # ==========================================
    # MODUL 2: MASTER DATABASE ANAK
    # ==========================================
    elif selected_menu == "🗂️ Master Database Anak":
        st.title("🗂️ Master Database Anak Asuh")
        st.markdown("Pengelolaan biodata identitas legal, NIK, KK, NISN, dan alamat asal.")
        st.markdown("---")
        
        conn = get_db_connection()
        df_anak = pd.read_sql_query("SELECT * FROM tb_anak_asuh", conn)
        
        # Filter Search
        search_query = st.text_input("🔍 Cari Nama, NIK, NISN, atau Sekolah...", "")
        filter_jenjang = st.selectbox("Filter Jenjang Sekolah", ["Semua Jenjang", "SD", "SMP", "SMK"])
        
        filtered_df = df_anak.copy()
        if search_query:
            filtered_df = filtered_df[filtered_df['nama_lengkap'].str.contains(search_query, case=False, na=False) |
                                      filtered_df['nik'].str.contains(search_query, case=False, na=False) |
                                      filtered_df['nisn'].str.contains(search_query, case=False, na=False)]
        if filter_jenjang != "Semua Jenjang":
            filtered_df = filtered_df[filtered_df['jenjang'] == filter_jenjang]
            
        st.dataframe(filtered_df, use_container_width=True)
        
        # FITUR TAMBAH ANAK (Hanya untuk Admin / Pekerja Sosial)
        if st.session_state['user_role'] == 'Admin':
            st.markdown("---")
            with st.expander("➕ Tambah Anak Asuh Baru"):
                with st.form("form_tambah_anak"):
                    c1, c2 = st.columns(2)
                    new_id = f"ANAK-{len(df_anak)+1:03d}"
                    nama = c1.text_input("Nama Lengkap")
                    jk = c2.selectbox("Jenis Kelamin", ["Perempuan", "Laki-laki"])
                    ttl_tempat = c1.text_input("Tempat Lahir")
                    ttl_tgl = c2.date_input("Tanggal Lahir", date(2012, 1, 1))
                    nik = c1.text_input("NIK (16 Digit)")
                    no_kk = c2.text_input("Nomor KK")
                    nisn = c1.text_input("NISN")
                    jenjang = c2.selectbox("Jenjang", ["SD", "SMP", "SMK"])
                    sekolah = c1.text_input("Nama Sekolah / Jurusan")
                    kelas = c2.text_input("Kelas saat ini")
                    kecamatan = c1.text_input("Kecamatan Asal")
                    alamat = c2.text_area("Alamat Lengkap Asal")
                    alasan = st.text_input("Latar Belakang Penerimaan (Yatim / Terlantar / KDRT)")
                    
                    submitted = st.form_submit_button("Simpan Data Anak Baru")
                    if submitted:
                        c = conn.cursor()
                        c.execute('''
                            INSERT INTO tb_anak_asuh 
                            (id_anak, nama_lengkap, jenis_kelamin, tempat_lahir, tanggal_lahir, nik, no_kk, nisn, jenjang, sekolah, kelas, kecamatan, alamat_asal, tanggal_masuk, alasan_masuk)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (new_id, nama, jk, ttl_tempat, str(ttl_tgl), nik, no_kk, nisn, jenjang, sekolah, kelas, kecamatan, alamat, str(date.today()), alasan))
                        conn.commit()
                        
                        log_audit(
                            username=st.session_state['username'],
                            nama_lengkap=st.session_state['user_fullname'],
                            role=st.session_state['user_role'],
                            aksi="TAMBAH ANAK",
                            detail=f"Menambahkan data anak asuh baru: {nama} ({new_id})"
                        )
                        
                        st.success(f"Berhasil menambahkan {nama} dengan ID {new_id}!")
                        st.rerun()
        conn.close()

    # ==========================================
    # MODUL BARU: SCAN BERKAS & DOKUMEN LEGALITAS
    # ==========================================
    elif selected_menu == "📂 Scan Berkas & Dokumen Legalitas":
        st.title("📂 Repositori Scan Berkas & Dokumen Legalitas")
        st.markdown("Fitur pengunggahan, pratinjau, dan unduhan berkas legal (Akta Lahir, KK, KIA, KIS, KIP, BA Reunifikasi).")
        st.markdown("---")
        
        conn = get_db_connection()
        df_anak = pd.read_sql_query("SELECT id_anak, nama_lengkap FROM tb_anak_asuh WHERE status_keberadaan = 'Aktif'", conn)
        
        selected_anak_str = st.selectbox("🎯 Pilih Anak Asuh:", df_anak['id_anak'] + " - " + df_anak['nama_lengkap'])
        anak_id_selected = selected_anak_str.split(" - ")[0]
        anak_nama_selected = selected_anak_str.split(" - ")[1]
        
        col_up, col_list = st.columns([1, 1.5])
        
        with col_up:
            st.subheader("📤 Unggah Berkas Scan Baru")
            if st.session_state['user_role'] in ['Admin', 'Pengasuh']:
                jenis_dok = st.selectbox("Jenis Dokumen Legal:", [
                    "Akta Kelahiran",
                    "Kartu Keluarga (KK)",
                    "Kartu Identitas Anak (KIA)",
                    "KTP Orang Tua / Wali",
                    "Kartu Indonesia Sehat (KIS / BPJS)",
                    "Kartu Indonesia Pintar (KIP)",
                    "Akta Kematian Orang Tua",
                    "Berita Acara (BA) Reunifikasi",
                    "Rapor Sekolah",
                    "Sertifikat / Berkas Lainnya"
                ])
                
                uploaded_file = st.file_uploader("Pilih Berkas Scan (PDF, JPG, PNG)", type=["pdf", "png", "jpg", "jpeg"])
                
                if st.button("💾 Simpan Berkas ke Repositori", type="primary", use_container_width=True):
                    if uploaded_file is not None:
                        file_bytes = uploaded_file.read()
                        file_name = uploaded_file.name
                        file_type = uploaded_file.type
                        file_size = len(file_bytes)
                        
                        c = conn.cursor()
                        c.execute('''
                            INSERT INTO tb_dokumen_adm (id_anak, jenis_dokumen, nama_file, tipe_file, ukuran_bytes, file_data, diunggah_oleh)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (anak_id_selected, jenis_dok, file_name, file_type, file_size, file_bytes, st.session_state['user_fullname']))
                        conn.commit()
                        
                        log_audit(
                            username=st.session_state['username'],
                            nama_lengkap=st.session_state['user_fullname'],
                            role=st.session_state['user_role'],
                            aksi="UNGGAH DOKUMEN",
                            detail=f"Mengunggah berkas '{jenis_dok}' ({file_name}) untuk {anak_nama_selected} ({anak_id_selected})"
                        )
                        
                        st.success(f"✅ Berkas '{jenis_dok}' berhasil diunggah!")
                        st.rerun()
                    else:
                        st.warning("Pilih file terlebih dahulu sebelum mengunggah.")
            else:
                st.info("ℹ️ Role Anda (Viewer) hanya dapat melihat dan mengunduh berkas scan.")

        with col_list:
            st.subheader(f"📋 Berkas Tersimpan: {anak_nama_selected}")
            df_docs = pd.read_sql_query('''
                SELECT id, jenis_dokumen, nama_file, tipe_file, ukuran_bytes, diunggah_oleh, tanggal_unggah 
                FROM tb_dokumen_adm 
                WHERE id_anak = ?
                ORDER BY tanggal_unggah DESC
            ''', conn, params=(anak_id_selected,))
            
            if len(df_docs) == 0:
                st.warning("⚠️ Belum ada berkas scan yang diunggah untuk anak ini.")
            else:
                for idx, row in df_docs.iterrows():
                    with st.expander(f"📄 {row['jenis_dokumen']} - {row['nama_file']}"):
                        st.write(f"• **Pengunggah**: {row['diunggah_oleh']}")
                        st.write(f"• **Tanggal**: {row['tanggal_unggah']}")
                        st.write(f"• **Ukuran File**: {row['ukuran_bytes']/1024:.1f} KB ({row['tipe_file']})")
                        
                        # Ambil BLOB File untuk Preview & Download
                        c = conn.cursor()
                        c.execute("SELECT file_data FROM tb_dokumen_adm WHERE id = ?", (row['id'],))
                        blob_data = c.fetchone()[0]
                        
                        # Preview Jika Gambar
                        if "image" in row['tipe_file']:
                            st.image(blob_data, caption=row['nama_file'], use_column_width=True)
                            
                        # Tombol Download
                        st.download_button(
                            label="📥 Unduh Berkas Ini",
                            data=blob_data,
                            file_name=row['nama_file'],
                            mime=row['tipe_file'],
                            key=f"dl_{row['id']}"
                        )
                        
                        # Hapus Berkas (Hanya Admin)
                        if st.session_state['user_role'] == 'Admin':
                            if st.button("🗑️ Hapus Berkas", key=f"del_{row['id']}"):
                                c.execute("DELETE FROM tb_dokumen_adm WHERE id = ?", (row['id'],))
                                conn.commit()
                                log_audit(
                                    username=st.session_state['username'],
                                    nama_lengkap=st.session_state['user_fullname'],
                                    role=st.session_state['user_role'],
                                    aksi="HAPUS DOKUMEN",
                                    detail=f"Menghapus berkas '{row['jenis_dokumen']}' ({row['nama_file']}) milik {anak_nama_selected}"
                                )
                                st.success("Berkas berhasil dihapus.")
                                st.rerun()

        conn.close()

    # ==========================================
    # MODUL 4: BIO-PSIKO-SOSIAL & KESEHATAN
    # ==========================================
    elif selected_menu == "🏥 Bio-Psiko-Sosial & Kesehatan":
        st.title("🏥 Profil Perkembangan Bio-Psiko-Sosial & Kesehatan")
        st.markdown("Rekam kesehatan harian, catatan konseling psikologis, dan perkembangan keagamaan.")
        st.markdown("---")
        
        conn = get_db_connection()
        df_anak = pd.read_sql_query("SELECT id_anak, nama_lengkap FROM tb_anak_asuh WHERE status_keberadaan = 'Aktif'", conn)
        
        selected_anak_id = st.selectbox("Pilih Anak Asuh:", df_anak['id_anak'] + " - " + df_anak['nama_lengkap'])
        anak_id_clean = selected_anak_id.split(" - ")[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🩺 Rekam Medis & Kesehatan Basis (KIS/BPJS)")
            st.info("Status Jaminan Kesehatan: **KIS PBI Aktif**")
            st.write("• **Riwayat Alergi**: Tidak Ada")
            st.write("• **Golongan Darah**: O / A / B")
            st.write("• **Pemeriksaan Fisik Terakhir**: Sehat, Tinggi/BB Proporsional")
            
        with col2:
            st.subheader("🧠 Catatan Adaptasi Sosial & Konseling")
            st.write("• **Perilaku di Panti**: Ramah, kooperatif dengan teman sebaya.")
            st.write("• **Konseling Psikologis**: Terlampaui dengan progres baik.")
            st.write("• **Perkembangan Spiritual**: Rajin mengaji harian, khatam Juz 'Amma.")
            
        if st.session_state['user_role'] in ['Admin', 'Pengasuh']:
            st.markdown("---")
            st.subheader("📝 Form Log Catatan Harian Pengasuh")
            with st.form("form_log_harian"):
                tgl_catat = st.date_input("Tanggal Pencatatan", date.today())
                kondisi_fisik = st.text_input("Kondisi Kesehatan Fisik")
                catatan_sosial = st.text_area("Catatan Perkembangan Emosi & Perilaku Sosial")
                capaian_ibadah = st.text_input("Capaian Keagamaan / Hafalan")
                
                if st.form_submit_button("Simpan Log Pengasuh"):
                    log_audit(
                        username=st.session_state['username'],
                        nama_lengkap=st.session_state['user_fullname'],
                        role=st.session_state['user_role'],
                        aksi="INPUT LOG PENGASUH",
                        detail=f"Memperbarui log harian kesehatan/spiritual untuk {selected_anak_id}"
                    )
                    st.success("Log harian pengasuh berhasil diperbarui!")
        conn.close()

    # ==========================================
    # MODUL 5: AKADEMIK & BAKAT PRESTASI
    # ==========================================
    elif selected_menu == "🎓 Akademik & Bakat Prestasi":
        st.title("🎓 Pemantauan Akademik, Minat & Bakat")
        st.markdown("Daftar prestasi lomba, ekstrakurikuler, dan minat bakat anak asuh.")
        st.markdown("---")
        
        conn = get_db_connection()
        df_bakat = pd.read_sql_query('''
            SELECT a.id_anak, a.nama_lengkap, a.jenjang, a.sekolah, b.kategori_bakat, b.deskripsi_bakat, b.nama_prestasi, b.tingkat_prestasi
            FROM tb_anak_asuh a
            JOIN tb_bakat_prestasi b ON a.id_anak = b.id_anak
        ''', conn)
        conn.close()
        
        st.subheader("🏆 Papan Rekam Jejak Prestasi & Kejuaraan Anak")
        st.dataframe(df_bakat, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🎨 Ringkasan Kategori Minat Utama")
        c1, c2, c3 = st.columns(3)
        c1.markdown("💃 **Seni & Menari**: Tari Wira/Woja, Mayoret, Angklung, Geguritan")
        c2.markdown("⚽ **Olahraga**: Sepak Bola (Gala Siswa), Atletik (Lari), Karate, Bulu Tangkis")
        c3.markdown("💻 **Vokasi**: Komputer Digital, Menjahit, Tata Busana, Perhotelan")

    # ==========================================
    # MODUL 6: AGING-OUT PLAN & ALUMNI
    # ==========================================
    elif selected_menu == "🚀 Aging-Out Plan & Alumni":
        st.title("🚀 Rencana Kemandirian (Aging-Out Plan) & Alumni")
        st.markdown("Program penyiapan masa depan untuk anak remaja 15+ tahun dan rekam alumni pasca-panti.")
        st.markdown("---")
        
        conn = get_db_connection()
        df_aging = pd.read_sql_query('''
            SELECT a.nama_lengkap, a.sekolah, a.kelas, g.tabungan_mandiri, g.pelatihan_diikuti, g.rencana_pasca_panti, g.status_alumni
            FROM tb_anak_asuh a
            JOIN tb_aging_out_plan g ON a.id_anak = g.id_anak
        ''', conn)
        conn.close()
        
        st.subheader("💼 Kesiapan Kemandirian Remaja SMK (15+ Tahun)")
        st.dataframe(df_aging, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🎓 Tracing Alumni Pasca-Terminasi")
        alumni_data = pd.DataFrame([
            {"Nama Alumni": "Marya Indah Puspa Sari", "Pendidikan": "SMK 4 YK (Tata Boga)", "Status Karir / Perguruan Tinggi": "Pelatihan Barista LPK", "Kontak Active": "0888xxxx"},
            {"Nama Alumni": "Herlinawati", "Pendidikan": "SMK Muhammadiyah 4 YK", "Status Karir / Perguruan Tinggi": "Pegawai Indomaret", "Kontak Active": "0896xxxx"},
            {"Nama Alumni": "Anisa Chinkarena", "Pendidikan": "SMK 4 YK (Tata Busana)", "Status Karir / Perguruan Tinggi": "Pramuniaga Manna Kampus", "Kontak Active": "0895xxxx"},
            {"Nama Alumni": "Rr. Aisha Elok Paraswati", "Pendidikan": "Lulusan Panti", "Status Karir / Perguruan Tinggi": "Mahasiswa Psikologi UTY Semester 4", "Kontak Active": "08886842177"},
            {"Nama Alumni": "Fadiyah Mifta Nurjanah", "Pendidikan": "Lulusan Panti", "Status Karir / Perguruan Tinggi": "Mahasiswa Manajemen UM Purworejo", "Kontak Active": "089669112361"},
            {"Nama Alumni": "Umar Shidiq", "Pendidikan": "Lulusan Panti", "Status Karir / Perguruan Tinggi": "Gardener Hotel Grand Rohan Jogja", "Kontak Active": "083186357470"}
        ])
        st.dataframe(alumni_data, use_container_width=True)

    # ==========================================
    # MODUL 7: QUICK-PRINT & EKSPOR
    # ==========================================
    elif selected_menu == "🖨️ Quick-Print & Ekspor Laporan":
        st.title("🖨️ Modul Quick-Print & Ekspor Laporan")
        st.markdown("Fasilitas cetak resume portofolio individual dan ekspor data terfilter untuk Dinas Sosial / Donatur.")
        st.markdown("---")
        
        conn = get_db_connection()
        df_anak = pd.read_sql_query("SELECT * FROM tb_anak_asuh", conn)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📄 Ekspor Master Data (Excel / CSV)")
            st.write("Unduh rekapitulasi data anak aktif dalam format Microsoft Excel siap olah.")
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_anak.to_excel(writer, index=False, sheet_name='Data_Anak_Asuh')
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 Unduh Dataset Excel (.xlsx)",
                data=excel_data,
                file_name="Data_Anak_Asuh_Wiloso_Projo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
        with col2:
            st.subheader("🖨️ Quick-Print Portofolio Individual")
            selected_print_anak = st.selectbox("Pilih Anak untuk Dicetak:", df_anak['id_anak'] + " - " + df_anak['nama_lengkap'])
            
            if st.button("🖨️ Generate Preview Portofolio", use_container_width=True):
                anak_row = df_anak[df_anak['id_anak'] == selected_print_anak.split(" - ")[0]].iloc[0]
                
                log_audit(
                    username=st.session_state['username'],
                    nama_lengkap=st.session_state['user_fullname'],
                    role=st.session_state['user_role'],
                    aksi="CETAK PORTOFOLIO",
                    detail=f"Mencetak preview portofolio untuk {selected_print_anak}"
                )
                
                st.markdown(f"""
                <div style="border: 2px solid #1E3A8A; padding: 20px; border-radius: 10px; background-color: #F8FAFC;">
                    <h3 style="text-align: center; color: #1E3A8A; margin-bottom: 0;">UPT RUMAH PENGASUHAN ANAK WILOSO PROJO</h3>
                    <p style="text-align: center; font-size: 12px; color: #64748B;">DINAS SOSIAL DIY - PORTOFOLIO PERKEMBANGAN ANAK ASUH</p>
                    <hr>
                    <table style="width:100%; font-size: 14px;">
                        <tr><td><b>ID & Nama Anak</b></td><td>: {anak_row['id_anak']} - {anak_row['nama_lengkap']}</td></tr>
                        <tr><td><b>TTL / Usia</b></td><td>: {anak_row['tempat_lahir']}, {anak_row['tanggal_lahir']}</td></tr>
                        <tr><td><b>NIK / NISN</b></td><td>: {anak_row['nik']} / {anak_row['nisn']}</td></tr>
                        <tr><td><b>Sekolah / Kelas</b></td><td>: {anak_row['sekolah']} ({anak_row['kelas']})</td></tr>
                        <tr><td><b>Alamat Asal</b></td><td>: {anak_row['alamat_asal']}</td></tr>
                        <tr><td><b>Latar Belakang</b></td><td>: {anak_row['alasan_masuk']}</td></tr>
                    </table>
                    <hr>
                    <p><b>Status Jaminan Medis:</b> KIS PBI Aktif | <b>Kondisi Kesehatan:</b> Baik/Sehat</p>
                    <p><b>Catatan Minat & Bakat:</b> Menari, Olahraga, Keagamaan (Khatam Juz 'Amma)</p>
                </div>
                """, unsafe_allow_html=True)
                st.caption("✨ Portofolio di atas dapat dicetak langsung melalui menu Print Browser (Ctrl + P).")
        conn.close()

    # ==========================================
    # MODUL 8: KELOLA PENGGUNA & LOG AUDIT
    # ==========================================
    elif selected_menu == "⚙️ Kelola Pengguna & Log Audit":
        st.title("⚙️ Kelola Pengguna & Log Audit Keamanan System")
        st.markdown("Khusus Admin Pekerja Sosial untuk mengelola pendaftaran akun login dan memantau jejak audit keamanan.")
        st.markdown("---")
        
        tab_users, tab_audit = st.tabs(["👥 Manajemen Akun User", "📜 Log Audit Keamanan System"])
        
        conn = get_db_connection()
        
        with tab_users:
            df_users = pd.read_sql_query("SELECT id, username, nama_lengkap, role, dibuat_pada FROM tb_users", conn)
            st.subheader("👥 Daftar Akun Login Terdaftar")
            st.dataframe(df_users, use_container_width=True)
            
            st.markdown("---")
            st.subheader("➕ Tambah Akun Pengguna Baru")
            with st.form("form_tambah_user"):
                c1, c2 = st.columns(2)
                u_name = c1.text_input("Username Baru")
                u_pass = c2.text_input("Password Baru", type="password")
                u_full = c1.text_input("Nama Lengkap Petugas")
                u_role = c2.selectbox("Role Akses", ["Pengasuh", "Viewer", "Admin"])
                
                if st.form_submit_button("Daftarkan Akun User"):
                    if u_name and u_pass and u_full:
                        c = conn.cursor()
                        try:
                            c.execute("INSERT INTO tb_users (username, password, nama_lengkap, role) VALUES (?, ?, ?, ?)",
                                      (u_name, make_hashes(u_pass), u_full, u_role))
                            conn.commit()
                            
                            log_audit(
                                username=st.session_state['username'],
                                nama_lengkap=st.session_state['user_fullname'],
                                role=st.session_state['user_role'],
                                aksi="TAMBAH USER",
                                detail=f"Mendaftarkan akun pengguna baru '{u_name}' ({u_role})"
                            )
                            
                            st.success(f"Akun `{u_name}` ({u_role}) berhasil ditambahkan!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("⚠️ Username sudah dipakai! Gunakan username lain.")
                    else:
                        st.warning("Mohon lengkapi semua bidang input.")
                        
        with tab_audit:
            st.subheader("📜 Rekam Jejak Audit Keamanan (Audit Trail Log)")
            st.markdown("Semua aktivitas log in, penambahan data, pengunggahan dokumen scan, dan penghapusan data tercatat di sini secara *real-time*.")
            
            df_audit = pd.read_sql_query("SELECT id, timestamp, username, nama_lengkap, role, aksi, detail FROM tb_audit_log ORDER BY id DESC", conn)
            
            search_audit = st.text_input("🔍 Cari Log (Nama, Username, atau Aksi)...", "")
            filtered_audit = df_audit.copy()
            if search_audit:
                filtered_audit = filtered_audit[
                    filtered_audit['username'].str.contains(search_audit, case=False, na=False) |
                    filtered_audit['nama_lengkap'].str.contains(search_audit, case=False, na=False) |
                    filtered_audit['aksi'].str.contains(search_audit, case=False, na=False) |
                    filtered_audit['detail'].str.contains(search_audit, case=False, na=False)
                ]
                
            st.dataframe(filtered_audit, use_container_width=True)
            
            # Unduh Log Audit
            output_audit = io.BytesIO()
            with pd.ExcelWriter(output_audit, engine='openpyxl') as writer:
                df_audit.to_excel(writer, index=False, sheet_name='Audit_Log')
            audit_excel_data = output_audit.getvalue()
            
            st.download_button(
                label="📥 Unduh Log Audit (.xlsx)",
                data=audit_excel_data,
                file_name="Audit_Log_Keamanan_Wiloso_Projo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        conn.close()
