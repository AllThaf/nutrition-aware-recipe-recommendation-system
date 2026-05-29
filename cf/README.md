# Collaborative Filtering for Food.com Recipe Recommendation

Modul ini mengimplementasikan sistem rekomendasi resep makanan menggunakan pendekatan **Collaborative Filtering (CF)** dengan model berbasis implicit feedback. Modul ini bertugas sebagai tahap pertama (*Candidate Generation*) dalam arsitektur sistem rekomendasi hibrida yang direncanakan.

## 1. Latar Belakang & Motivasi

Dataset asli Food.com menyediakan interaksi antara pengguna (user) dan resep (item) yang mencakup rating (0-5) dan ulasan teks. Untuk tugas *Collaborative Filtering*, kita memformulasikan masalah ini sebagai **Implicit Feedback Recommendation**. 
- Semua rating positif (> 0) diperlakukan sebagai sinyal positif (1).
- Rating 0 diperlakukan sebagai "unobserved" karena maknanya ambigu (bisa berarti tidak suka, atau belum pernah mencoba).

### Masalah pada Data Split Bawaan (Dataset Paper Asli)
Dataset awal (`interactions_train.csv`, `interactions_test.csv`) tidak didesain untuk tugas CF, melainkan untuk tugas *recipe generation*. Data test memisahkan resep berdasarkan waktu rilisnya, sehingga **100% resep di set pengujian tidak pernah muncul di set pelatihan**. 
Hal ini mengakibatkan model CF—yang sangat bergantung pada matriks interaksi yang diketahui—mengalami *cold-start* ekstrem pada item, sehingga metrik performa mendekati nol (setara tebakan acak).

## 2. Metodologi Data (The Fix)

Untuk melatih dan mengevaluasi model CF dengan tepat, dilakukan pembuatan ulang skema pembagian data (*data split*) secara langsung dari `RAW_interactions.csv` (`cf/build_split.py`).

1. **Penyaringan (Co-filtering)**:
   - Pengguna dengan **kurang dari 5 interaksi** dihapus.
   - Resep dengan **kurang dari 3 interaksi** dihapus.
   - Proses ini dilakukan secara iteratif hingga konvergen untuk mengurangi *sparsity* berlebihan.
2. **Pembagian Temporal Leave-One-Out (LOO)**:
   - Data diurutkan berdasarkan waktu per pengguna.
   - **Test Set**: Interaksi paling terakhir dari setiap pengguna.
   - **Validation Set**: Interaksi kedua terakhir dari setiap pengguna.
   - **Train Set**: Sisa riwayat interaksi pengguna sebelumnya.

Melalui desain ini, 99.9% resep yang muncul di Validation/Test set sudah dipelajari (*observed*) di Train set.

## 3. Algoritma Model

Modul ini mengevaluasi dua algoritma Matrix Factorization unggulan untuk data *implicit feedback*:
1. **Alternating Least Squares (ALS)**: 
   - Meminimalkan *confidence-weighted squared error*.
   - Menggunakan parameter `alpha` untuk mengontrol bobot item yang berinteraksi berbanding non-interaksi.
   - Sangat optimal untuk matriks yang sangat jarang (*extremely sparse*).
2. **Bayesian Personalized Ranking (BPR)**:
   - Menggunakan pendekatan *pairwise ranking*. 
   - Model belajar untuk memberikan skor lebih tinggi pada item yang diinteraksikan dibandingkan sampel negatif acak.

*(Implementasi model dibungkus dari library C++ `implicit` yang dimodifikasi khusus untuk mencegah masalah bottleneck performa threading akibat OpenBLAS).*

## 4. Evaluasi & Metrik

Pengujian dilakukan menggunakan protokol standar Leave-One-Out:
- **Kandidat Test**: 1 item positif (ground truth) dicampur dengan 99 item negatif (sampel acak yang tidak ada di riwayat pengguna).
- **Metrik Utama**: Hit Rate pada K (HR@5, HR@10, HR@20) dan Mean Reciprocal Rank (MRR).

## 5. Hasil Eksperimen (Full Grid Search)

*Hyperparameter Tuning* skala penuh dilakukan untuk membandingkan ALS dan BPR di berbagai konfigurasi (`factors`, `regularization`, `alpha`, `iterations`, `learning rate`).

### Ringkasan Perbandingan Performa Akhir di Test Set

| Model | HR@5 | HR@10 | HR@20 | MRR | Best Configuration |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **ALS** ⭐ | **0.3851** | **0.4653** | **0.5603** | **0.2947** | `factors=32`, `reg=0.01`, `iter=50`, `alpha=40.0` |
| BPR | 0.2510 | 0.3629 | 0.5207 | 0.1857 | `factors=128`, `lr=0.05`, `reg=0.01`, `iter=200` |

### Analisis Hasil
1. **Keunggulan Mutlak ALS**: ALS terbukti secara signifikan lebih baik dibandingkan BPR untuk dataset ini. Kemampuan ALS dalam memodelkan intensitas ketertarikan (via nilai `alpha`) bekerja sangat baik pada sparsity dataset yang mencapai ~99.96%.
2. **Latent Factors Kecil = Lebih Baik (ALS)**: Konfigurasi ALS terbaik menggunakan dimensi faktor (`factors`) yang relatif kecil yaitu 32. Ukuran laten yang terlalu besar (`factors=128`) justru menyebabkan *overfitting* karena jumlah interaksi di training data yang terbatas.
3. **Konvergensi BPR Lambat**: BPR membutuhkan dimensi sangat besar (`factors=128`) dan epoch tinggi (`iterations=200`) untuk bisa menangkap sinyal dari pasangan *positive-negative*.

Model terbaik (ALS) diekspor dan disimpan untuk digunakan pada sistem *Hybrid Recommendation*.

## 6. Struktur Folder dan Penggunaan

- `cf/build_split.py`: Skrip untuk mengeksekusi LOO splitting mentah dari CSV awal.
- `cf/data_prep.py`: Pemrosesan memori, pembuatan *sparse matrix* dan batching sampel negatif.
- `cf/evaluator.py`: Skrip yang menghitung performa (HR@K & MRR).
- `cf/train.py`: Otomatisasi Grid-Search, Training, dan Evaluasi.
- `cf/evaluate.py`: Skrip evaluasi *standalone* untuk me-load model yang telah dilatih `.pkl` dan memvalidasi ke data set *test*.
- `cf/models/`: Struktur modular kelas `ALSModel` dan `BPRModel`.
- `cf/outputs/`: Lokasi penyimpanan matriks *split*, metrik `.csv`, dan bobot model akhir (`best_cf_model.pkl`).
