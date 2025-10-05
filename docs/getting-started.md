<file_path>
xyra/docs/getting-started.md
</file_path>

<edit_description>
Buat file memulai
</edit_description>

# Memulai dengan Xyra

Selamat datang di Xyra! Bagian ini akan membantu Anda membuat aplikasi web pertama Anda dengan framework Xyra.

## Aplikasi Sederhana

Mari kita buat aplikasi web sederhana yang menampilkan pesan "Hello, Xyra!".

### 1. Buat File Aplikasi

Buat file baru bernama `app.py` dan tambahkan kode berikut:

```python
from xyra import App, Request, Response

# Inisialisasi aplikasi
app = App()

# Definisikan route untuk halaman utama
@app.get("/")
def home(req: Request, res: Response):
    res.json({"message": "Hello, Xyra!"})

# Jalankan server
if __name__ == "__main__":
    app.listen(8000)
```

### 2. Jalankan Aplikasi

Jalankan aplikasi dengan perintah:

```bash
python app.py
```

Anda akan melihat output seperti:

```
🚀 Xyra server running on http://0.0.0.0:8000
```

### 3. Akses Aplikasi

Buka browser dan kunjungi `http://localhost:8000`. Anda akan melihat respons JSON:

```json
{
  "message": "Hello, Xyra!"
}
```

## Penjelasan Kode

- `from xyra import App, Request, Response`: Import komponen utama dari Xyra
- `app = App()`: Membuat instance aplikasi
- `@app.get("/")`: Decorator untuk menangani request GET ke root path "/"
- `def home(req: Request, res: Response)`: Handler function yang menerima Request dan Response objects
- `res.json({"message": "Hello, Xyra!"})`: Mengirim respons JSON
- `app.listen(8000)`: Menjalankan server di port 8000

## Langkah Selanjutnya

- Pelajari [Routing](routing.md) untuk menambahkan lebih banyak endpoint
- Lihat [Request & Response](request-response.md) untuk memahami objek request dan response
- Coba [Templating](templating.md) untuk merender HTML

---

[Kembali ke Daftar Isi](../README.md)