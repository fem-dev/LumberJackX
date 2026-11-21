# LumberJackX

**Version 0.2.0 | Windows 10 x64 | C++20**

[English](#english) · [فارسی](#فارسی)

---

# English

LumberJackX is a Windows desktop prototype for capturing and previewing the Telegram Desktop LumberJack mini app locally. It uses Win32 for screen capture and OpenCV for image display and processing.

## Current features

- Live capture of a selected desktop region.
- OpenCV preview with an overlay toolbar.
- Add a circular marker by selecting **Add Circle** and clicking the corresponding game-control position.
- Select a marker and assign it to **Left** or **Right**.
- Unassigned markers are displayed in yellow.
- Starting is blocked until both Left and Right controls are configured.
- A single **Start / Stop** button, with the `S` keyboard shortcut.
- Session timer that stops the session when time expires.
- Save and restore calibration from `lumberjackx.yml`.
- Initial tests for decision mapping, safe unknown detection, and configuration persistence.

## Important limitation

The branch detector currently returns **Unknown** for every frame. This is an intentional fail-safe placeholder, not a completed vision model. The Start button currently starts the session timer and updates the status display; it does not make game moves or send mouse clicks. Branch recognition must be implemented and validated against varied real gameplay screenshots before any automatic input is enabled.

The Left and Right circles identify the on-screen game controls; they are not branch-detection regions.

## Requirements

- Windows 10 x64
- Visual Studio 2022 with **Desktop development with C++**
- CMake 3.20 or newer
- OpenCV 4.x with its CMake package configuration

## Build manually

Run these commands in Developer PowerShell. Adjust `OpenCV_DIR` to the location containing `OpenCVConfig.cmake`:

```powershell
cmake -S . -B build -A x64 -DOpenCV_DIR="C:/opencv/build"
cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure
```

## Run

Example for a 400x700 game window whose top-left desktop position is (100, 100):

```powershell
.\build\Release\LumberJackX.exe --x 100 --y 100 --width 400 --height 700 --seconds 3600
```

Adjust the capture rectangle to cover the LumberJack mini app in Telegram Desktop. The capture region and marker calibration are stored in `lumberjackx.yml`.

## Controls

- **Add Circle** or `A`: enter marker-placement mode, then click the desired control position in the preview.
- Click an existing circle: select it.
- **Left** or `L`: label the selected marker as the left game control.
- **Right** or `R`: label the selected marker as the right game control.
- **Start / Stop** or `S`: toggle the session.
- **Save**: save the current calibration.
- `Q` or `Esc`: exit.

## GitHub Actions: automated Windows build

The workflow is located at `.github/workflows/windows-build.yml`.

- Run it manually from the **Actions** tab to build the application and upload downloadable artifacts.
- Enable the release option and provide a version tag (for example, `v0.2.1`) to publish a GitHub Release.
- Pushing a tag such as `v0.2.1` also triggers the build and release workflow.
- The ZIP package is intended to contain the executable and its required OpenCV runtime DLLs.

## Project layout

- `include/`: public interfaces and data structures
- `src/`: screen capture, calibration, branch detector, decision engine, timer, and controller
- `tests/`: unit tests
- `.github/workflows/`: automated Windows build workflow

## Scope

Image processing is performed locally. The project does not modify Telegram accounts, rooms, game servers, or scores. Use the software in accordance with the game's and service's rules.

---

# فارسی

LumberJackX یک نمونه برنامه دسکتاپ برای ویندوز است که تصویر مینی‌اپ LumberJack را از Telegram Desktop دریافت و به‌صورت محلی نمایش می‌دهد. برای تصویربرداری از Win32 و برای نمایش و پردازش تصویر از OpenCV استفاده می‌شود.

## امکانات فعلی

- دریافت زنده تصویر از یک محدوده انتخاب‌شده از صفحه ویندوز.
- نمایش پیش‌نمایش بازی با نوار ابزار.
- ساخت نشانگر دایره‌ای با انتخاب **Add Circle** و کلیک روی محل دکمه بازی.
- انتخاب نشانگر و تعیین نقش **Left** یا **Right**.
- نمایش نشانگرهای تعیین‌نشده با رنگ زرد.
- جلوگیری از شروع تا زمان مشخص‌شدن هر دو دکمه چپ و راست.
- دکمه واحد **Start / Stop** و میانبر صفحه‌کلید `S`.
- زمان‌سنج نشست که با پایان زمان، اجرا را متوقف می‌کند.
- ذخیره و بازیابی کالیبراسیون در فایل `lumberjackx.yml`.
- تست‌های اولیه برای نگاشت تصمیم‌ها، تشخیص امن حالت نامشخص و ذخیره‌سازی تنظیمات.

## محدودیت مهم نسخه فعلی

تشخیص‌دهنده شاخه در حال حاضر برای تمام فریم‌ها نتیجه **Unknown (نامشخص)** برمی‌گرداند. این یک حالت ایمن موقت است و هنوز مدل تشخیص کامل نشده است. دکمه Start در حال حاضر فقط زمان‌سنج نشست و نمایش وضعیت را فعال می‌کند؛ هیچ حرکت خودکار یا کلیک موس در بازی انجام نمی‌شود. پیش از فعال‌کردن هرگونه ورودی خودکار، تشخیص شاخه باید روی تصاویر واقعی و متنوع بازی پیاده‌سازی و اعتبارسنجی شود.

دایره‌های Left و Right محل دکمه‌های کنترلی بازی را مشخص می‌کنند و ناحیه تشخیص شاخه نیستند.

## پیش‌نیازها

- ویندوز ۱۰ نسخه ۶۴ بیتی
- Visual Studio 2022 همراه با گزینه **Desktop development with C++**
- CMake نسخه ۳٫۲۰ یا جدیدتر
- OpenCV 4.x همراه با فایل پیکربندی CMake

## ساخت دستی

دستورهای زیر را در Developer PowerShell اجرا کنید. مسیر `OpenCV_DIR` را به پوشه‌ای تغییر دهید که فایل `OpenCVConfig.cmake` در آن قرار دارد:

```powershell
cmake -S . -B build -A x64 -DOpenCV_DIR="C:/opencv/build"
cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure
```

## اجرای برنامه

نمونه زیر برای پنجره بازی با ابعاد ۴۰۰ در ۷۰۰ پیکسل و مختصات گوشه بالا-چپ ۱۰۰ و ۱۰۰ است:

```powershell
.\build\Release\LumberJackX.exe --x 100 --y 100 --width 400 --height 700 --seconds 3600
```

محدوده تصویربرداری را طوری تنظیم کنید که مینی‌اپ LumberJack در Telegram Desktop را پوشش دهد. محدوده تصویربرداری و نشانگرها در فایل `lumberjackx.yml` ذخیره می‌شوند.

## راهنمای کنترل‌ها

- **Add Circle** یا کلید `A`: ورود به حالت افزودن نشانگر؛ سپس روی محل دکمه در پیش‌نمایش کلیک کنید.
- کلیک روی یک دایره: انتخاب نشانگر.
- **Left** یا کلید `L`: ثبت نشانگر انتخاب‌شده به‌عنوان دکمه چپ.
- **Right** یا کلید `R`: ثبت نشانگر انتخاب‌شده به‌عنوان دکمه راست.
- **Start / Stop** یا کلید `S`: شروع یا توقف نشست.
- **Save**: ذخیره کالیبراسیون فعلی.
- کلیدهای `Q` یا `Esc`: خروج از برنامه.

## ساخت خودکار ویندوز با GitHub Actions

فایل گردش‌کار در مسیر `.github/workflows/windows-build.yml` قرار دارد.

- با اجرای دستی آن از زبانه **Actions**، برنامه ساخته می‌شود و خروجی‌ها به‌صورت Artifact برای دریافت قرار می‌گیرند.
- برای انتشار در GitHub Releases، گزینه انتشار را فعال و یک برچسب نسخه مانند `v0.2.1` وارد کنید.
- با Push کردن یک Tag مانند `v0.2.1` نیز گردش‌کار ساخت و انتشار اجرا می‌شود.
- بسته ZIP برای شامل‌بودن فایل اجرایی و DLLهای زمان اجرای موردنیاز OpenCV آماده شده است.

## ساختار پروژه

- `include/`: رابط‌های عمومی و ساختارهای داده
- `src/`: تصویربرداری، کالیبراسیون، تشخیص شاخه، موتور تصمیم، زمان‌سنج و کنترل‌گر
- `tests/`: تست‌های واحد
- `.github/workflows/`: گردش‌کار ساخت خودکار ویندوز

## محدوده عملکرد

پردازش تصویر به‌صورت محلی انجام می‌شود. این پروژه حساب‌های تلگرام، اتاق‌ها، سرور بازی یا امتیازها را دست‌کاری نمی‌کند. استفاده از نرم‌افزار باید مطابق قوانین بازی و سرویس باشد.
