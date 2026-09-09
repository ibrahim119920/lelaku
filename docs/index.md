Kelompok Finished or not, submit!

1. Ketua Kelompok: Ahmad Maulana Ibrahim-24/539655/TK/59853
2. Anggota 1: BAYU RAHMAT KURNIA - 24/533736/TK/59139
3. Anggota 2: Sukmawati - 24/545512/TK/60686


"Project Senior Project TI”
Departemen Teknologi Elektro dan Teknologi Informasi
Fakultas Teknik, Universitas Gadjah Mada


## Nama Produk

**Lelaku**

---

## 3. Permasalahan yang Dipecahkan

### Latar Belakang

Banyak perjalanan menggunakan kendaraan pribadi dilakukan dengan tingkat okupansi yang rendah, sementara pada waktu yang sama terdapat pengguna lain yang memiliki asal, tujuan, serta waktu perjalanan yang serupa. Belum adanya mekanisme yang efektif untuk menemukan dan menghubungkan pengguna dengan pola perjalanan serupa menyebabkan peluang berbagi perjalanan tidak termanfaatkan.

### Rumusan Permasalahan

1. Bagaimana merancang aplikasi yang menghubungkan pengguna dengan rencana perjalanan serupa dengan aman?
2. Bagaimana menentukan kemiripan antar rencana perjalanan berdasarkan rute, moda transportasi, waktu, dan preferensi pengguna?
3. Bagaimana merancang sistem keamanan dan kepercayaan antar pengguna untuk mendukung kenyamanan dalam perjalanan?

### Daftar Pustaka

1. Masoud, N., & Jayakrishnan, R. (2017). *A matching algorithm for dynamic ridesharing*. Transportation Research Procedia.
2. Dastani, Z., Koosha, H., Karimi, H., & Mohammadzadeh Moghaddam, A. (2024). *User preferences in ride-sharing mathematical models for enhanced matching*. Scientific Reports, 14, 27338.
3. Hartl, B., Penz, E., & Schüßler, E. (2025). *Creating a trusting environment in the sharing economy: Unpacking mechanisms for trust-building used by peer-to-peer carpooling platforms*. Journal of Cleaner Production, 489, 144661.

---

## 4. Ide Solusi yang Diusulkan Beserta Rancangan Fitur

### Solusi

* **Pengguna dapat mempublikasikan rencana perjalanan** beserta origin, destination, waktu keberangkatan, kendaraan, jumlah kursi tersedia, serta toleransi perubahan rute atau waktu.
* **Sistem melakukan intelligent trip matching** untuk mencari, menilai, dan memberi peringkat perjalanan yang kompatibel berdasarkan kemiripan rute, waktu keberangkatan, estimasi detour, dan faktor relevan lainnya.
* **Sistem merekomendasikan titik pickup yang efisien** bagi pengguna yang telah mendapatkan kandidat perjalanan, dengan mempertimbangkan tambahan jarak/waktu bagi pemilik kendaraan dan aksesibilitas bagi penumpang.
* **Pengguna dapat mengirim dan menerima permintaan perjalanan bersama**, kemudian mengonfirmasi atau menolak calon teman seperjalanan.
* **Sistem membantu menjaga keamanan dan kepercayaan pengguna** melalui AI-assisted risk detection untuk mendeteksi aktivitas, akun, atau pola perjalanan yang mencurigakan dan memberikan flag untuk pemeriksaan lebih lanjut.

### Rancangan Fitur Solusi

| Fitur                              | Keterangan                                                                                                       |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| **Authentication**                 | Register dengan verifikasi identitas pengguna dan kendaraan, login, dan logout.                                  |
| **Create Trip**                    | Membuat trip dengan asal, tujuan, tanggal, waktu, dan kursi tersedia.                                            |
| **Find Trip**                      | Mencari perjalanan berdasarkan asal, tujuan, dan waktu.                                                          |
| **Trip Matching**                  | Sistem menggunakan algoritma untuk memberikan rekomendasi perjalanan yang rute dan waktunya mirip.               |
| **Request Join / Accept / Reject** | Pengguna mengajukan permintaan untuk ikut perjalanan. Pemilik perjalanan dapat menerima atau menolak permintaan. |
| **Trip History**                   | Menampilkan perjalanan yang sedang berlangsung dan sudah selesai.                                                |

---

## 5. Analisis Kompetitor

### Kompetitor 1 — Gojek / Grab / Maxim

| Aspek                                        | Keterangan                                                                                                                                                                                                                  |
| -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Nama**                                     | Gojek / Grab / Maxim                                                                                                                                                                                                        |
| **Jenis Kompetitor**                         | Indirect Competitors                                                                                                                                                                                                        |
| **Jenis Produk**                             | Ride Hailing                                                                                                                                                                                                                |
| **Target Customer**                          | Masyarakat yang membutuhkan transportasi praktis, terutama pengguna yang tidak menggunakan kendaraan pribadi untuk perjalanan tersebut.                                                                                     |
| **Kelebihan**                                | 1. Demand dan supply yang stabil.<br>2. Sistem yang matang.                                                                                                                                                                 |
| **Kekurangan**                               | 1. Relasi transaksional: seluruh biaya perjalanan ditanggung oleh penumpang.<br>2. Biaya dapat meningkat pada kondisi tertentu.<br>3. Tidak berfokus pada pemanfaatan perjalanan yang memang sudah akan dilakukan pengguna. |
| **Key Competitive Advantage & Unique Value** | Layanan transportasi **on-demand** dengan ketersediaan driver tinggi, proses pemesanan cepat, dan ekosistem layanan yang sudah matang.                                                                                      |

### Kompetitor 2 — BlaBlaCar / Sejalan

| Aspek                                        | Keterangan                                                                                                                                                                                                       |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Nama**                                     | BlaBlaCar / Sejalan                                                                                                                                                                                              |
| **Jenis Kompetitor**                         | Direct Competitors                                                                                                                                                                                               |
| **Jenis Produk**                             | Ride Sharing                                                                                                                                                                                                     |
| **Target Customer**                          | Pengguna yang ingin melakukan perjalanan antarkota atau rute tertentu dengan biaya lebih terjangkau melalui perjalanan bersama.                                                                                  |
| **Kelebihan**                                | 1. Model ride sharing sudah terbukti dan mudah dipahami pengguna.<br>2. Membantu membagi biaya perjalanan antar pengguna.<br>3. Memanfaatkan kursi kosong pada kendaraan yang memang sudah melakukan perjalanan. |
| **Kekurangan**                               | 1. Umumnya berfokus pada kendaraan roda empat.<br>2. Cenderung lebih cocok untuk perjalanan antarkota atau jarak menengah-panjang dibanding perjalanan harian jarak dekat.                                       |
| **Key Competitive Advantage & Unique Value** | Menghubungkan pengguna dengan pengendara yang memiliki **rute perjalanan searah**, sehingga biaya perjalanan dapat dibagi dan kapasitas kendaraan kosong dapat dimanfaatkan.                                     |

### Kompetitor 3 — Transportasi Publik

| Aspek                                        | Keterangan                                                                                                                       |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **Nama**                                     | Transportasi Publik                                                                                                              |
| **Jenis Kompetitor**                         | Tertiary Competitors                                                                                                             |
| **Jenis Produk**                             | Transportasi Publik / Shared Transportation                                                                                      |
| **Target Customer**                          | Masyarakat dengan rutinitas perjalanan yang tetap, seperti komuter harian.                                                       |
| **Kelebihan**                                | 1. Sangat ekonomis.<br>2. Efektif mengurangi volume kendaraan di jalan raya.<br>3. Membuka peluang networking dengan orang baru. |
| **Kekurangan**                               | 1. Waktu kurang fleksibel.<br>2. Jarang ada rute yang 100% sama dari titik awal ke tujuan akhir pengguna.                        |
| **Key Competitive Advantage & Unique Value** | Menawarkan **biaya perjalanan rendah dan kapasitas angkut besar** melalui rute serta jadwal yang telah ditentukan.               |
