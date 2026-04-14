# FlowerHub — MIS3010_04 Nhóm 4 Chủ đề 2

Nền tảng đặt hoa trực tuyến gồm 3 vai trò: **Khách hàng**, **Tiệm hoa (Shop)**, **Admin hệ thống**.

Stack: Django 6.0.3, SQLite, Pillow, Tailwind CDN.

---

## 1. Yêu cầu

- Python **3.11+** (đã test trên 3.13)
- `pip` và `venv` đi kèm Python
- Git

## 2. Clone repo

```bash
git clone <repo-url>
cd MIS3010_Nhom4_ChuDe2
```

## 3. Tạo & kích hoạt virtualenv

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Sau khi kích hoạt, prompt sẽ có tiền tố `(.venv)`.

## 4. Cài dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Khởi tạo database

Chạy migrations để tạo schema SQLite (`db.sqlite3`):

```bash
python manage.py migrate
```

(Tuỳ chọn) Tạo dữ liệu mẫu — admin + vài tiệm hoa demo:

```bash
python seed.py
```

Sau khi chạy `seed.py` sẽ có:
- Admin: `admin` / `admin123`
- Các shop demo: `lavender_studio`, `moon_studio`, `coco_studio`, ... mật khẩu `demo1234`

Hoặc tự tạo superuser:

```bash
python manage.py createsuperuser
```

## 6. Chạy server

```bash
python manage.py runserver
```

Mặc định mở tại http://127.0.0.1:8000

## 7. Đường dẫn theo vai trò

| Vai trò | URL đăng nhập | URL sau khi vào |
|---|---|---|
| Khách hàng | `/customer/login/` | `/customer/after-login/` |
| Tiệm hoa | `/shop/vendor/login_shop/` | `/shop/vendor/dashboard/` |
| Admin | `/admin-sys/login/` | `/admin-sys/dashboard/` |

> 3 vai trò dùng cookie session riêng biệt (`sid_kh`, `sid_shop`, `sid_admin`), có thể đăng nhập đồng thời trong cùng 1 trình duyệt mà không đá văng nhau.

## 8. Cấu trúc thư mục chính

```
Nhom4_ChuDe2/        # settings, urls, wsgi
dv_dathoa/           # app chính
  ├── models.py
  ├── middleware.py  # NamespacedSessionMiddleware
  ├── views/         # views_khach.py, views_tiem.py, views_admin.py
  ├── urls/          # urls_khach.py, urls_tiem.py, urls_admin.py
  ├── services/      # business logic
  ├── forms/
  └── migrations/
templates/           # khach/, tiem/, admin/
static/              # css, js, images
media/               # file upload (logo, gallery, QR, biên lai)
seed.py              # script seed dữ liệu mẫu
```

## 9. Chia sẻ ra ngoài (ngrok / cloudflare tunnel)

`settings.py` đã bật `SECURE_PROXY_SSL_HEADER` và `CSRF_TRUSTED_ORIGINS` cho `*.ngrok-free.app` và `*.trycloudflare.com`. Chỉ cần:

```bash
ngrok http 8000
# hoặc
cloudflared tunnel --url http://localhost:8000
```

## 10. Reset toàn bộ DB

```bash
rm db.sqlite3
python manage.py migrate
python seed.py
```

> File ảnh upload nằm trong `media/`, xoá thủ công nếu cần.

## 11. Lỗi thường gặp

- **`admin.E410`**: bỏ qua, do dùng `NamespacedSessionMiddleware` (subclass hợp lệ của `SessionMiddleware`), đã `SILENCED_SYSTEM_CHECKS`.
- **CSRF 403 khi mở bằng tunnel**: kiểm tra domain đã nằm trong `CSRF_TRUSTED_ORIGINS`.
- **Logo / ảnh không hiện**: chắc chắn `DEBUG=True` (settings dev) và đã `python manage.py runserver` (Django dev server tự serve `MEDIA_URL`).
