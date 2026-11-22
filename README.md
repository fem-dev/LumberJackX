# LumberJackX

Automatic screen-based player for the **LumberJack Telegram Mini App** on Windows.

## اجرا در ویندوز

Python 3.11+ و Git باید نصب باشند. PowerShell را باز کن و فقط این دستورها را اجرا کن:

```powershell
git clone https://github.com/fem-dev/LumberJackX.git
cd LumberJackX
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

بازی LumberJack را در Telegram Desktop باز و پنجره‌اش را قابل مشاهده نگه دار. برای توقف بات کلید `Esc` را بزن.

نیازی به فایل EXE، نصب OCR یا Tesseract نیست. برای دفعات بعد، داخل پوشه پروژه فقط محیط را فعال کن و `python main.py` را اجرا کن؛ برای دریافت آخرین تغییرات، قبلش `git pull` بزن.

## نکات

- بات پنجره تلگرام را با عنوان LumberJack پیدا می‌کند و از تصویر برای تشخیص بازی استفاده می‌کند.
- تشخیص تصویری هنوز روی همه ظاهرها و اندازه‌های Mini App آزمایش نشده و ممکن است به تنظیم نیاز داشته باشد.
- اگر PowerShell اجازه فعال‌سازی محیط را نداد، این دستور را در همان پنجره اجرا کن و سپس فعال‌سازی را دوباره انجام بده: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.
