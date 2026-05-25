# Chat Terenkripsi - Aplikasi Web Chat Real-time

Aplikasi web chat terenkripsi untuk komunikasi aman antara dua orang dengan fitur online/offline status dan akses via link unik.

## 🔐 Fitur Keamanan

- **Enkripsi End-to-End**: Semua pesan dienkripsi menggunakan Fernet (AES-128)
- **Link Unik**: Setiap chat room memiliki link unik yang random dan aman
- **No Login Required**: Akses hanya dengan link, tidak perlu login
- **Session Management**: Session aman dengan HTTPS cookie protection
- **Database Encryption**: Pesan disimpan dalam bentuk terenkripsi

## ✨ Fitur Utama

- 💬 Chat real-time antara dua orang
- 🟢 Indikator online/offline dengan perubahan real-time
- 📱 Mobile responsive design (berjalan sempurna di smartphone)
- 🔗 Sharing link yang mudah (copy atau QR code)
- 💾 Histori pesan (tersimpan terenkripsi)
- 📲 WebSocket untuk komunikasi real-time
- 🎨 UI modern dan user-friendly

## 🛠️ Instalasi

### Prerequisites
- Python 3.8+
- pip

### Setup

1. **Clone/Download project**
   ```bash
   cd d:\Iwang\MASTERAN_WB\program\PY\App_chat
   ```

2. **Buat virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Aktifkan virtual environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Setup environment variables**
   ```bash
   copy .env.example .env
   ```
   Edit `.env` dan generate SECRET_KEY yang kuat (atau biarkan default)

6. **Jalankan aplikasi**
   ```bash
   python app.py
   ```

7. **Buka di browser**
   ```
   http://localhost:5000
   ```

## 📖 Cara Menggunakan

### Membuat Chat Room Baru

1. Buka http://localhost:5000
2. Masukkan nama Anda (minimal 2 karakter)
3. Klik "Buat Chat Room Baru"
4. Bagikan link atau QR code ke teman
5. Tunggu teman bergabung
6. Mulai chatting!

### Bergabung ke Chat Room

1. Teman memberikan link atau QR code
2. Klik link atau scan QR code
3. Masukkan nama Anda
4. Klik "Bergabung ke Chat"
5. Mulai berbincang!

## 🏗️ Struktur Folder

```
App_chat/
├── app.py                 # Flask aplikasi utama
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
├── README.md             # File ini
├── chat.db              # Database SQLite (auto-generated)
├── static/
│   ├── css/
│   │   └── style.css    # Styling utama
│   └── js/
│       └── index.js     # JavaScript untuk halaman utama
└── templates/
    ├── index.html       # Halaman membuat room
    ├── join.html        # Halaman bergabung room
    ├── chat.html        # Halaman chat utama
    └── error.html       # Halaman error
```

## 🔧 Teknologi yang Digunakan

### Backend
- **Flask**: Web framework
- **Flask-SQLAlchemy**: ORM untuk database
- **Flask-SocketIO**: Real-time communication
- **Cryptography (Fernet)**: Enkripsi pesan

### Frontend
- **HTML5**: Struktur halaman
- **CSS3**: Styling responsif
- **JavaScript**: Interaktivitas
- **Socket.IO Client**: Real-time communication
- **QRCode.js**: Generate QR code

### Database
- **SQLite**: Database lokal

## 🔐 Enkripsi Detail

Aplikasi menggunakan **Fernet (symmetric encryption)** dari library `cryptography`:
- Key: Generated secara random per chat room (256-bit)
- Cipher: AES-128 dalam mode CBC
- Padding: Standar PKCS7
- Hash: SHA256 untuk authenticity

Setiap pesan di-encrypt sebelum disimpan ke database dan di-decrypt saat ditampilkan.

## 📡 WebSocket Events

### Server → Client
- `new_message`: Pesan baru masuk
- `user_status_changed`: Status user berubah (online/offline)
- `online_status`: Respons cek status online
- `error`: Pesan error

### Client → Server
- `connect`: User terhubung
- `disconnect`: User disconnect
- `send_message`: Kirim pesan
- `check_online`: Check status user lain

## ⚙️ Konfigurasi

### Environment Variables
```env
SECRET_KEY=your-secret-key-here      # Session key (auto-generate jika kosong)
FLASK_ENV=development                 # development atau production
FLASK_DEBUG=True                       # Debug mode (false di production)
```

### Port
Default: `5000`
Ubah di line terakhir `app.py`:
```python
socketio.run(app, debug=True, host='0.0.0.0', port=5000)
```

## 🚀 Deployment

### Untuk Production

1. **Update environment**
   ```env
   FLASK_ENV=production
   FLASK_DEBUG=False
   SECRET_KEY=your-strong-secret-key
   ```

2. **Install production server**
   ```bash
   pip install gunicorn python-socketio python-engineio
   ```

3. **Jalankan dengan Gunicorn**
   ```bash
   gunicorn --worker-class eventlet -w 1 app:app
   ```

4. **Setup reverse proxy** (Nginx/Apache)
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:5000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
       }
   }
   ```

5. **Setup HTTPS** (Let's Encrypt)
   ```bash
   # Gunakan Certbot untuk auto-setup HTTPS
   ```

## 📝 API Endpoints

### REST API

- `GET /` - Halaman utama
- `POST /create-room` - Buat chat room baru
- `GET /join/<link>` - Halaman bergabung room
- `POST /join-room` - Bergabung ke room
- `GET /chat/<room_id>` - Halaman chat
- `GET /api/room-status/<room_id>` - Get room status

### WebSocket Events
- `connect` - Koneksi user
- `disconnect` - Disconnect user
- `send_message` - Kirim pesan
- `check_online` - Check status online

## 🐛 Troubleshooting

### Port 5000 sudah digunakan
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :5000
kill -9 <PID>
```

### Database error
```bash
# Delete database lama
rm chat.db

# atau Windows
del chat.db

# Aplikasi akan auto-create database baru
```

### WebSocket connection error
- Pastikan Flask-SocketIO terinstall: `pip install flask-socketio`
- Check firewall settings
- Restart aplikasi

## 📱 Testing di Mobile

1. Cari IP lokal komputer:
   ```bash
   ipconfig  # Windows
   ifconfig  # Linux/Mac
   ```

2. Akses di mobile via: `http://192.168.x.x:5000`

3. Atau gunakan ngrok untuk public URL:
   ```bash
   ngrok http 5000
   ```

## 🔒 Security Notes

- Secret key di-generate otomatis jika kosong (ganti dengan strong key di production)
- Gunakan HTTPS di production (dengan SSL certificate)
- Database SQLite hanya untuk development, gunakan PostgreSQL di production
- Implementasikan rate limiting untuk mencegah abuse
- Regular update dependencies untuk security patches

## 📄 Lisensi

MIT License - Bebas digunakan untuk keperluan apapun

## 🤝 Support

Jika ada pertanyaan atau issue, silakan buat issue atau diskusi.

---

**Dibuat dengan ❤️ untuk komunikasi aman dan privat**
