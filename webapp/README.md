# NutriCook - Sistem Rekomendasi Resep Sadar Nutrisi

NutriCook adalah platform web resep kuliner sadar nutrisi yang menggunakan sistem rekomendasi hibrida berbasis **Collaborative Filtering (NCF)**, **Content-Based Filtering (TF-IDF)**, dan **Cascade Filtering Nutrisi**.

---

## 🛠️ Prasyarat
Pastikan komputer Anda sudah terpasang:
*   [Docker](https://www.docker.com/)
*   [Docker Compose](https://docs.docker.com/compose/)

---

## 🚀 Langkah Menjalankan Aplikasi

### 1. Salin Konfigurasi Lingkungan (`.env`)
Di dalam folder `webapp`, salin berkas `.env.example` menjadi `.env`:
```bash
cp .env.example .env
```

### 2. Bangun dan Jalankan Docker Container
Jalankan perintah berikut untuk membangun (*build*) citra (*image*) docker dan menjalankan layanan backend, database, serta frontend Nginx di latar belakang:
```bash
docker compose up --build -d
```

Setelah berjalan, Anda akan memiliki 3 container aktif:
*   `webapp_db` (PostgreSQL) pada port host `5433`
*   `webapp_api` (FastAPI) pada port host `8000`
*   `webapp_frontend` (Nginx) pada port host `3000`

---

## 💾 Langkah Seeding Database
Untuk mengisi database PostgreSQL dengan dataset resep dari `food.com` (20.000 data resep bawaan), gunakan perintah berikut di terminal:

```bash
docker compose exec api python webapp/backend/scripts/seed.py --reset
```

*   `--reset`: Menghapus data tabel lama (jika ada) sebelum mengisi data baru.
*   `--limit-recipes`: Secara bawaan bernilai `20000`. Jika ingin membatasi jumlah data resep yang disemai, Anda bisa menyetel parameternih, contoh: `--limit-recipes 5000`.

---

## 🌐 Membuka dan Menggunakan Web App

### 1. Akses Aplikasi
Buka peramban (*browser*) Anda dan akses tautan berikut:
👉 **[http://localhost:3000](http://localhost:3000)**

### 2. Log In dengan Akun Demo
Sistem tidak menggunakan registrasi rumit karena dirancang untuk kebutuhan demo personalisasi. Anda dapat masuk dengan cara:
*   **Masuk Cepat (Rekomendasi)**: Klik salah satu dari **4 Akun Demo** yang terdaftar di halaman login. Form User ID dan Password akan terisi secara otomatis dan melakukan login langsung.
*   **Masuk Manual**:
    *   **User ID**: Masukkan ID numerik (contoh: `1533` untuk akun Budi Santoso).
    *   **Password**: Gunakan password universal: `nutricook`
    *   *Catatan: Anda juga bisa memasukkan User ID acak apa saja untuk mensimulasikan pengguna baru (Cold Start).*

### 3. Fitur Utama yang Tersedia
*   **Dashboard Dua Baris**:
    *   **Rekomendasi Untukmu (Baris 1)**: Resep hasil pencampuran model CF + CBF + analisis gizi khusus akun Anda, lengkap dengan keterangan sinyal dominan pembentuk rekomendasi (*CF / CBF / Nutrition*).
    *   **Sedang Populer (Baris 2)**: Resep terpopuler berdasarkan tingkat interaksi di database.
*   **Filter Nutrisi Interaktif (Filter-First)**:
    *   Klik tombol **Filter Nutrisi** di pojok kanan atas Baris 1.
    *   Atur rentang **Kalori Maksimum** dan **Skor Kesehatan Minimum** sesuai target diet Anda.
    *   Klik **Terapkan**. Sistem backend akan langsung melakukan pemotongan dan penghitungan ulang rekomendasi secara real-time.
*   **Halaman Detail Resep**:
    *   Klik kartu resep mana saja untuk masuk ke detail resep secara penuh.
    *   Menampilkan rincian bahan dengan checkbox, bagan profil gizi lengkap, dan **seluruh langkah instruksi memasak langsung terbuka** (tidak menggunakan akordeon) agar mudah dibaca.
    *   Gunakan widget bintang untuk **mengirimkan rating baru** guna melatih preferensi Collaborative Filtering akun Anda secara dinamis.
*   **Navbar Search**:
    *   Gunakan kolom pencarian di bagian atas untuk menyaring resep berdasarkan kecocokan kata kunci nama resep secara cepat.
