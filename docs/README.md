<file_path>
xyra/docs/README.md
</file_path>

<edit_description>
Buat README.md utama dengan pendahuluan dan navigasi
</edit_description>

# Dokumentasi Framework Xyra

Xyra adalah framework web Python yang ringan dan cepat, dibangun di atas socketify untuk performa tinggi. Framework ini menyediakan fitur-fitur modern seperti routing, templating, WebSocket, dan dokumentasi API otomatis.

## Fitur Utama

- 🚀 Performa tinggi dengan socketify
- 🛣️ Routing yang fleksibel
- 📝 Templating dengan Jinja2
- 🔌 Dukungan WebSocket
- 📚 Dokumentasi API otomatis dengan Swagger
- 🔄 Asynchronous support
- 🧩 Middleware support

## Daftar Isi

- [Instalasi](installation.md)
- [Memulai](getting-started.md)
- [Routing](routing.md)
- [Request & Response](request-response.md)
- [Templating](templating.md)
- [WebSocket](websocket.md)
- [Swagger Documentation](swagger.md)
- [Middleware](middleware.md)
- [Static Files](static-files.md)
- [Contoh Lengkap](examples.md)
- [API Reference](api-reference.md)

## Quick Start

```python
from xyra import App, Request, Response

app = App()

@app.get("/")
def home(req: Request, res: Response):
    res.json({"message": "Hello, Xyra!"})

if __name__ == "__main__":
    app.listen(8000)
```

Kunjungi `http://localhost:8000` untuk melihat hasilnya.

## Kontribusi

Kontribusi sangat diterima! Silakan buat issue atau pull request di repository GitHub.

## Lisensi

MIT License - lihat file LICENSE untuk detail.

---

Dibuat dengan ❤️ menggunakan Xyra Framework