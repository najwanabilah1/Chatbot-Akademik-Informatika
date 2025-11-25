# 🤖 Chatbot Bimbingan Akademik

Sistem chatbot berbasis AI untuk memberikan bimbingan akademik kepada mahasiswa dengan fitur real-time learning dan semantic search.

---

## 📋 Daftar Isi
- [Persyaratan Sistem](#persyaratan-sistem)
- [Setup & Instalasi](#setup--instalasi)
- [Konfigurasi Database](#konfigurasi-database)
- [Menjalankan Aplikasi](#menjalankan-aplikasi)
- [Hosting di PythonAnywhere](#-hosting-di-pythonanywhere)
- [Struktur Project](#struktur-project)
- [Fitur Utama](#fitur-utama)
- [Troubleshooting](#troubleshooting)

---

## 🛠️ Persyaratan Sistem

### Software yang Diperlukan:
- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **MySQL Server** ([Download](https://www.mysql.com/downloads/mysql/))
- **Git** (Opsional, untuk clone repository)

### Hardware Minimum:
- RAM: 4GB
- Storage: 2GB (untuk model dan dataset)
- Processor: Dual Core

---

## 📥 Setup & Instalasi

### 1. **Clone atau Download Project**
```bash
# Jika menggunakan git
git clone <repository-url>
cd "Chatbot Bimbingan Akademik"

# Atau ekstrak zip file jika sudah didownload
```

### 2. **Buat Virtual Environment (Recommended)**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

**⚠️ Catatan:** Instalasi TensorFlow mungkin memakan waktu 5-10 menit tergantung koneksi internet.

---

## 🗄️ Konfigurasi Database

### 1. **Buat Database di MySQL**
```bash
# Buka MySQL Command Line atau MySQL Workbench
mysql -u root -p

# Jalankan perintah berikut:
CREATE DATABASE chatbot_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### 2. **Update Konfigurasi Database** (Jika Diperlukan)
Edit file `backend/config.py`:
```python
DB_USER = "root"        # Username MySQL Anda
DB_PASS = ""            # Password MySQL (kosong jika tidak ada)
DB_HOST = "localhost"   # Host database
DB_NAME = "chatbot_db"  # Nama database
```

### 3. **Inisialisasi Database Tables**
```bash
cd backend
python -c "from config import app, db; app.app_context().push(); db.create_all(); print('✅ Database initialized!')"
```

---

## 🚀 Menjalankan Aplikasi

### 1. **Memastikan Virtual Environment Aktif**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. **Mulai Backend Server (Flask)**
```bash
cd backend
python app.py
```

Output yang benar:
```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

### 3. **Buka Frontend di Browser**
Di terminal baru (jangan tutup terminal backend):
```bash
# Navigasi ke folder frontend
cd frontend

# Buka file HTML dengan browser
# Windows
start index.html

# Linux
xdg-open index.html

# Mac
open index.html
```

Atau buka browser dan akses: **http://localhost:5000** atau buka file `frontend/index.html` secara langsung.

---

## 🌐 Hosting di PythonAnywhere

### Langkah 1: Daftar PythonAnywhere

1. Buka https://www.pythonanywhere.com
2. Klik **Sign Up** → pilih paket Free (gratis)
3. Isi email dan password
4. Verifikasi email Anda

### Langkah 2: Upload Project

#### Via Git (Recommended):
```bash
# Di terminal PythonAnywhere bash console
cd /home/username
git clone <repository-url> chatbot
cd chatbot
```

#### Via Upload Manual:
1. Buka **Files** di dashboard PythonAnywhere
2. Upload file project secara manual atau zip kemudian extract

### Langkah 3: Setup Virtual Environment

```bash
# Di Bash console PythonAnywhere
cd /home/username/chatbot
mkvirtualenv --python=/usr/bin/python3.10 chatbot_env
pip install -r requirements.txt
```

**⚠️ Catatan:** 
- Proses install bisa 10-15 menit (ada TensorFlow)
- PythonAnywhere free hanya dapat CPU (tidak ada GPU)

### Langkah 4: Konfigurasi Database MySQL

#### Option A: Gunakan MySQL PythonAnywhere (Recommended)

1. Di dashboard → **Databases** → **MySQL**
2. Klik **Create Database**
3. Catat credentials yang diberikan
4. Update `backend/config.py`:
```python
DB_USER = "username"                    # Username dari PythonAnywhere
DB_PASS = "password"                    # Password dari PythonAnywhere
DB_HOST = "username.mysql.pythonanywhere.com"  # Host yang diberikan
DB_NAME = "username$chatbot_db"         # Format: username$dbname
```

#### Option B: Gunakan Database Lokal (untuk testing saja)

Jika tidak mau pakai MySQL PythonAnywhere, bisa pake SQLite:
```python
# Ubah di backend/config.py
SQLALCHEMY_DATABASE_URI = 'sqlite:///chatbot.db'
```

### Langkah 5: Inisialisasi Database

```bash
# Di Bash console PythonAnywhere
cd /home/username/chatbot/backend
source /home/username/.virtualenvs/chatbot_env/bin/activate
python -c "from config import app, db; app.app_context().push(); db.create_all(); print('✅ Database initialized!')"
```

### Langkah 6: Konfigurasi Web App

1. Di dashboard PythonAnywhere → **Web**
2. Klik **Add a new web app**
3. Pilih **Manual configuration** → **Python 3.10**
4. Edit **WSGI configuration file** dengan kode berikut:

```python
# /var/www/username_pythonanywhere_com_wsgi.py
import sys
import os

# Tambahkan project path
path = '/home/username/chatbot'
if path not in sys.path:
    sys.path.append(path)

# Setup virtualenv
activate_this = '/home/username/.virtualenvs/chatbot_env/bin/activate_this.py'
exec(open(activate_this).read())

# Import Flask app
os.chdir(path)
from backend.app import app as application
```

5. **Static files** → Tambah mapping:
   - URL: `/static/`
   - Directory: `/home/username/chatbot/frontend/assets/`

6. **Static files** → Tambah mapping lagi:
   - URL: `/frontend/`
   - Directory: `/home/username/chatbot/frontend/`

### Langkah 7: Setup Frontend

Karena PythonAnywhere Flask akan serve backend, kita perlu modify frontend untuk akses API:

Edit `frontend/assets/js/api.js` (atau file JS yang handle API):
```javascript
// Ubah dari localhost ke PythonAnywhere domain
const API_BASE = 'https://username.pythonanywhere.com/api';
// Bukan: const API_BASE = 'http://localhost:5000/api';
```

Atau di setiap AJAX/Fetch call:
```javascript
fetch('https://username.pythonanywhere.com/api/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({email: email, password: password})
})
```

### Langkah 8: Enable CORS di Backend

Edit `backend/app.py` - pastikan CORS enabled:
```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS untuk semua routes
```

### Langkah 9: Reload Web App

1. Di dashboard **Web** → Tombol **Reload** (warna hijau)
2. Tunggu sampai status berubah hijau ✅

### Langkah 10: Test Aplikasi

1. Buka `https://username.pythonanywhere.com`
2. Coba register & login
3. Chat dengan bot

### ⚠️ Limitasi PythonAnywhere Free:
- Storage: 512 MB
- CPU: Shared (lambat untuk training model)
- Uptime: 3 jam/day
- MySQL: 50 MB storage
- File uploads: Terbatas

### 💡 Tips Optimization:

**1. Jika model training lambat:**
```python
# Gunakan model yang sudah pre-trained
# Atau train offline di laptop, upload .h5 file saja
```

**2. Jika database penuh:**
```python
# Pindahkan old chat history ke backup
# Query untuk delete old records:
DELETE FROM chat_history WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

**3. Monitoring Performance:**
- Dashboard → **Files** → Check file sizes
- Dashboard → **Databases** → Check storage usage
- Dashboard → **Web** → Check error logs

### 🔄 Update Kode di PythonAnywhere

Setiap kali update kode:
```bash
# Di Bash console
cd /home/username/chatbot
git pull origin main  # Jika pakai git
# Atau upload file baru manual

# Reload web app di dashboard
```

### ❌ Troubleshooting PythonAnywhere

**Error: ModuleNotFoundError**
```bash
source /home/username/.virtualenvs/chatbot_env/bin/activate
pip install [module-name]
```

**Error: Database connection failed**
- Check MySQL credentials di config.py
- Verify database dibuat di Databases menu
- Test connection di Bash console

**Error: CORS issue / 403 Forbidden**
```python
# Di backend/app.py
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://username.pythonanywhere.com"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})
```

**Error: Static files not loading**
- Check URL mapping di Web → Static files
- Path harus absolute: `/home/username/chatbot/frontend/...`

---

## 📁 Struktur Project

```
Chatbot Bimbingan Akademik/
├── backend/
│   ├── app.py                 # Flask main app
│   ├── config.py              # Database config
│   ├── create_admin.py        # Script buat admin
│   ├── db/
│   │   ├── init_db.py
│   │   └── models.py          # Database models
│   ├── routes/
│   │   ├── admin_routes.py    # Admin endpoints
│   │   ├── chatbot_routes.py  # Chat endpoints
│   │   └── user_routes.py     # User endpoints
│   ├── model/                 # Folder model AI
│   │   └── main_model.h5
│   ├── uploads/               # Folder upload dataset
│   └── utils/
│       ├── load_data.py       # Dataset loader
│       ├── pdf_parser.py      # PDF processor
│       └── retrain_model.py   # Model retraining
│
├── frontend/
│   ├── index.html             # Home page
│   ├── login.html
│   ├── signup.html
│   ├── chatbot.html           # Chat interface
│   ├── edit_profil.html
│   ├── admin/                 # Admin pages
│   │   ├── dashboard.html
│   │   ├── data.html
│   │   ├── user.html
│   │   └── index.html
│   └── assets/
│       ├── css/               # Styling
│       └── img/               # Images
│
└── requirements.txt           # Python dependencies
```

---

## ✨ Fitur Utama

### 👥 User Features
- ✅ Register & Login
- ✅ Chat dengan Chatbot
- ✅ Edit Profile
- ✅ Lihat History Chat

### 👨‍💼 Admin Features
- ✅ Dashboard dengan Statistics
- ✅ Manage Users
- ✅ Upload Dataset (CSV)
- ✅ Upload Peraturan (PDF/DOCX)
- ✅ Retrain Model secara otomatis
- ✅ View Dataset & Peraturan

### 🤖 AI Features
- ✅ LSTM Neural Network untuk Q&A
- ✅ TF-IDF Semantic Search Fallback
- ✅ Auto-retrain setelah upload dataset
- ✅ Real-time learning dari dataset baru

---

## 🔧 Command Penting

### Buat Admin User
```bash
cd backend
python create_admin.py
```

### Retrain Model Manual
```bash
cd backend
python -m utils.retrain_model
```

### Reset Database (⚠️ Hati-hati - akan menghapus semua data)
```bash
cd backend
python -c "from config import app, db; app.app_context().push(); db.drop_all(); db.create_all(); print('✅ Database reset!')"
```

---

## 🐛 Troubleshooting

### ❌ Error: "ModuleNotFoundError: No module named 'flask'"
**Solusi:**
```bash
pip install -r requirements.txt
```

### ❌ Error: "Access denied for user 'root'@'localhost'"
**Solusi:**
- Update password di `backend/config.py`
- Atau reset MySQL password Anda

### ❌ Error: "Database 'chatbot_db' doesn't exist"
**Solusi:**
Buat database terlebih dahulu:
```bash
mysql -u root -p -e "CREATE DATABASE chatbot_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### ❌ Error: "Port 5000 already in use"
**Solusi:**
```bash
# Windows - cari process yang menggunakan port 5000
netstat -ano | findstr :5000

# Kill process (ganti PID dengan nomor process)
taskkill /PID <PID> /F

# Atau jalankan di port lain
# Edit app.py: app.run(debug=True, port=5001)
```

### ❌ TensorFlow Installation Slow/Error
**Solusi:**
```bash
# Install versi CPU yang lebih ringan
pip install tensorflow-cpu
```

### ❌ Frontend tidak bisa connect ke Backend
**Solusi:**
- Pastikan backend sudah running di http://127.0.0.1:5000
- Check console browser (F12) untuk error messages
- Pastikan CORS sudah enabled di app.py

---

## 📝 Setup Admin Pertama Kali

1. **Jalankan script create_admin:**
```bash
cd backend
python create_admin.py
```

2. **Masukkan data admin:**
```
Masukkan NPM: 00000
Masukkan Nama: Administrator
Masukkan Password: admin123
```

3. **Login ke admin panel:**
- URL: `http://localhost/admin/index.html` (atau sesuaikan path)
- Username: Administrator
- Password: admin123

---

## 📊 Upload Dataset Pertama Kali

1. **Login sebagai Admin**
2. **Ke menu "Data Management"**
3. **Upload Dataset CSV** dengan format:
```csv
pertanyaan,jawaban
"Apa itu bimbingan akademik?","Bimbingan akademik adalah..."
"Bagaimana cara mendaftar?","Untuk mendaftar silakan..."
```

4. **Klik "Upload CSV"** - Model akan auto-retrain
5. **Upload Peraturan (PDF/DOCX)** untuk semantic search fallback

---

## 🌐 API Endpoints

### Authentication
- `POST /api/register` - Register user baru
- `POST /api/login` - Login user
- `POST /api/admin/login` - Login admin

### Chat
- `POST /api/chat` - Send message ke chatbot

### Admin
- `GET /api/admin/dashboard_stats` - Get dashboard statistics
- `GET /api/admin/users` - List all users
- `POST /api/admin/upload_dataset` - Upload CSV dataset
- `POST /api/admin/upload_pdf` - Upload PDF peraturan
- `POST /api/admin/retrain` - Manual retrain model

---

## ✅ Checklist Setup

- [ ] Python 3.8+ installed
- [ ] MySQL Server running
- [ ] Virtual environment created & activated
- [ ] `pip install -r requirements.txt` completed
- [ ] Database `chatbot_db` created
- [ ] Backend config updated (jika perlu)
- [ ] Database initialized
- [ ] Admin user created
- [ ] Backend running di port 5000
- [ ] Frontend accessible di browser
- [ ] Dapat login & chat dengan bot

**Jika semua checklist ✅ maka setup berhasil!**

---

**Terakhir Update:** November 25, 2025
