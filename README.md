# LumberJackX

**Version 0.3.0 | Windows x64 | C# WinForms + Win32 + C++**

[English](#english) · [فارسی](#فارسی)

---

# English

LumberJackX is a Windows desktop preview and control-marker configuration tool for the LumberJack mini app in Telegram Desktop.

The application now uses a hybrid architecture:
- **C# WinForms** provides the desktop interface, marker editing, settings, and session timer.
- **Win32 GDI** captures the selected screen rectangle without OpenCV.
- **A small native C++ DLL** provides the image-detection boundary. It currently returns `Unknown` for every frame until a real classifier is implemented and validated.

## Current features

- Live capture of a configurable desktop rectangle.
- Resizable preview with correct image-to-screen coordinate mapping.
- Add circular markers by choosing **Add Circle** and clicking a game-control position.
- Select a marker and assign it to **Left** or **Right**.
- A marker can be removed with the **Delete** key.
- Save and restore capture settings, markers, and session duration as JSON.
- Import existing `lumberjackx.yml` settings once, when that file is beside the executable or in the current directory.
- One **Start / Stop** button and a session countdown.
- Keyboard shortcuts: `A` add marker, `L` assign Left, `R` assign Right, `S` start/stop, `Delete` remove selected marker, `Q` or `Esc` exit.
- Native C++ and managed C# test suites run in GitHub Actions.

## Important limitations

The branch detector is deliberately fail-closed and currently returns **Unknown** for all frames. This is a placeholder, not a completed vision model.

The **Start** button currently starts or stops the session timer only. It does not make game moves, move the mouse, or send mouse clicks. Branch recognition must be implemented and validated using varied real gameplay frames before any future action logic is considered.

The Left and Right circles mark the game's on-screen controls. They are not branch-detection regions.

## Requirements

- Windows 10/11 x64.
- **.NET 10 Desktop Runtime (x64)**. The published package is framework-dependent to keep its download size smaller; the runtime is installed separately.
- No OpenCV, vcpkg, or Visual Studio installation is required on the target PC.

Install the .NET 10 Desktop Runtime from the official [.NET download page](https://dotnet.microsoft.com/download/dotnet/10.0).

## Build from source

Development prerequisites:
- .NET 10 SDK
- Visual Studio 2022 C++ build tools
- CMake 3.20 or newer

Run these commands from the repository root in Developer PowerShell:

```powershell
cmake -S . -B build -A x64
cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure

dotnet restore src-managed/LumberJackX.App/LumberJackX.App.csproj --runtime win-x64
dotnet build src-managed/LumberJackX.App/LumberJackX.App.csproj -c Release -r win-x64 --no-restore

dotnet restore src-managed/LumberJackX.Tests/LumberJackX.Tests.csproj
dotnet run --project src-managed/LumberJackX.Tests/LumberJackX.Tests.csproj -c Release
```

To create a framework-dependent release package:

```powershell
dotnet publish src-managed/LumberJackX.App/LumberJackX.App.csproj -c Release -r win-x64 --self-contained false
```

Copy the built `LumberJackVision.dll` next to `LumberJackX.exe` in the publish directory.

## Run

Start `LumberJackX.exe`. Use the X/Y fields to set the desktop origin and Width/Height to set the capture rectangle. Select **Apply Region** to recapture the new area.

The default capture rectangle is `100, 100, 400, 600`. Change it to cover the Telegram Desktop game window.

## Configuration

Settings are stored at:

```text
%LocalAppData%\LumberJackX\lumberjackx.json
```

The JSON file stores the capture rectangle, session duration, and marker coordinates relative to the captured image. If an older `lumberjackx.yml` file is found beside the executable or in the current working directory, the application attempts a one-time import and saves the result in JSON.

## GitHub Actions

The workflow is `.github/workflows/windows-build.yml`. It runs on pushes to `main`, version tags such as `v0.3.0`, and manual dispatch. It builds and tests the native C++ library, builds and tests the C# projects, publishes the Windows x64 app, and uploads `LumberJackX-windows-x64.zip`.

The package is framework-dependent: install the .NET 10 Desktop Runtime x64 on the target PC before running it.

## Project layout

- `src-managed/LumberJackX.App/`: C# WinForms user interface, GDI capture, preview, and native interop.
- `src-managed/LumberJackX.Core/`: portable configuration, coordinate mapping, and session timer logic.
- `src-managed/LumberJackX.Tests/`: managed test harness.
- `native/`: native C++ image-detection DLL and tests.
- `.github/workflows/`: Windows build and test workflow.

## Scope

Image capture and processing run locally. The project does not modify Telegram accounts, rooms, game servers, or scores. Use the software in accordance with the game's and service's rules.

---

# فارسی

LumberJackX یک برنامه دسکتاپ ویندوز برای پیش‌نمایش تصویر مینی‌اپ LumberJack در Telegram Desktop و تنظیم دایره‌های کنترلی روی تصویر است.

ساختار پروژه به‌صورت ترکیبی تغییر کرده است:
- **C# WinForms** رابط گرافیکی، مدیریت دایره‌ها، تنظیمات و زمان‌سنج را اجرا می‌کند.
- **Win32 GDI** تصویر محدوده انتخاب‌شده از دسکتاپ را بدون OpenCV دریافت می‌کند.
- **یک DLL کوچک با C++** مرز ارتباطی بخش تشخیص تصویر را فراهم می‌کند. این بخش فعلاً برای تمام تصاویر نتیجه `Unknown` برمی‌گرداند تا زمانی که تشخیص‌دهنده واقعی پیاده‌سازی و آزمایش شود.

## امکانات فعلی

- دریافت زنده تصویر از محدوده دلخواه صفحه ویندوز.
- پیش‌نمایش قابل تغییر اندازه با نگاشت درست مختصات تصویر به صفحه.
- افزودن دایره با انتخاب **افزودن دایره** و کلیک روی محل دکمه بازی.
- انتخاب دایره و تعیین نقش **چپ** یا **راست**.
- حذف دایره انتخاب‌شده با کلید `Delete`.
- ذخیره و بازیابی محدوده تصویربرداری، دایره‌ها و مدت نشست در فایل JSON.
- واردکردن یک‌باره تنظیمات قدیمی `lumberjackx.yml`، در صورت وجود فایل کنار برنامه یا در پوشه جاری.
- یک دکمه **شروع / توقف** همراه با زمان‌سنج نشست.
- میانبرها: `A` افزودن دایره، `L` تعیین چپ، `R` تعیین راست، `S` شروع/توقف، `Delete` حذف دایره و `Q` یا `Esc` خروج.
- اجرای تست‌های C++ و C# در GitHub Actions.

## محدودیت مهم نسخه فعلی

تشخیص‌دهنده شاخه عمداً در وضعیت ایمن قرار دارد و برای تمام فریم‌ها نتیجه **Unknown (نامشخص)** می‌دهد. این بخش هنوز مدل تشخیص کامل نیست.

دکمه **Start** فقط زمان‌سنج نشست را شروع یا متوقف می‌کند. در این نسخه هیچ حرکت خودکار، جابه‌جایی موس یا کلیک در بازی انجام نمی‌شود. تشخیص شاخه باید ابتدا روی تصاویر واقعی و متنوع بازی پیاده‌سازی و اعتبارسنجی شود.

دایره‌های Left و Right محل دکمه‌های کنترلی بازی را مشخص می‌کنند و ناحیه تشخیص شاخه نیستند.

## پیش‌نیاز اجرا

- ویندوز ۱۰ یا ۱۱ نسخه ۶۴ بیتی.
- **.NET 10 Desktop Runtime نسخه x64**. برای کوچک‌تر ماندن بسته، برنامه به‌صورت وابسته به Runtime منتشر می‌شود و Runtime باید جداگانه روی ویندوز نصب باشد.
- روی کامپیوتر مقصد نیازی به نصب OpenCV، vcpkg یا Visual Studio نیست.

Runtime رسمی را از صفحه [دانلود .NET 10](https://dotnet.microsoft.com/download/dotnet/10.0) دریافت کنید.

## ساخت پروژه از سورس

ابزارهای موردنیاز برای توسعه:
- .NET 10 SDK
- ابزارهای کامپایل C++ در Visual Studio 2022
- CMake نسخه ۳٫۲۰ یا جدیدتر

دستورها را از پوشه اصلی مخزن در Developer PowerShell اجرا کنید:

```powershell
cmake -S . -B build -A x64
cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure

dotnet restore src-managed/LumberJackX.App/LumberJackX.App.csproj --runtime win-x64
dotnet build src-managed/LumberJackX.App/LumberJackX.App.csproj -c Release -r win-x64 --no-restore

dotnet restore src-managed/LumberJackX.Tests/LumberJackX.Tests.csproj
dotnet run --project src-managed/LumberJackX.Tests/LumberJackX.Tests.csproj -c Release
```

برای ساخت بسته قابل انتشار که Runtime را همراه خود ندارد:

```powershell
dotnet publish src-managed/LumberJackX.App/LumberJackX.App.csproj -c Release -r win-x64 --self-contained false
```

فایل ساخته‌شده `LumberJackVision.dll` را کنار `LumberJackX.exe` در پوشه انتشار قرار دهید.

## اجرای برنامه

فایل `LumberJackX.exe` را اجرا کنید. با فیلدهای X و Y مختصات شروع محدوده و با Width و Height اندازه محدوده تصویربرداری را مشخص کنید. سپس **اعمال محدوده** را بزنید.

محدوده پیش‌فرض برابر `100, 100, 400, 600` است. آن را طوری تغییر دهید که پنجره بازی در Telegram Desktop داخل محدوده قرار گیرد.

## تنظیمات

تنظیمات در مسیر زیر ذخیره می‌شوند:

```text
%LocalAppData%\LumberJackX\lumberjackx.json
```

فایل JSON مختصات محدوده تصویربرداری، مدت نشست و مختصات دایره‌ها را نسبت به تصویر دریافت‌شده نگه می‌دارد. اگر فایل قدیمی `lumberjackx.yml` کنار برنامه یا در پوشه جاری پیدا شود، برنامه تلاش می‌کند تنظیمات را یک‌بار به JSON منتقل کند.

## GitHub Actions

گردش‌کار در مسیر `.github/workflows/windows-build.yml` است. با هر Push به شاخه `main`، ثبت Tag نسخه مانند `v0.3.0` یا اجرای دستی فعال می‌شود. این گردش‌کار کتابخانه C++ را می‌سازد و تست می‌کند، پروژه‌های C# را می‌سازد و آزمایش می‌کند، نسخه ویندوز x64 را منتشر می‌کند و فایل `LumberJackX-windows-x64.zip` را به‌عنوان Artifact قرار می‌دهد.

پیش از اجرای برنامه روی کامپیوتر مقصد، .NET 10 Desktop Runtime نسخه x64 را نصب کنید.

## ساختار پروژه

- `src-managed/LumberJackX.App/`: رابط WinForms، تصویربرداری GDI، پیش‌نمایش و اتصال به DLL بومی.
- `src-managed/LumberJackX.Core/`: تنظیمات، نگاشت مختصات و منطق زمان‌سنج.
- `src-managed/LumberJackX.Tests/`: تست‌های بخش مدیریت‌شده.
- `native/`: کتابخانه تشخیص تصویر C++ و تست‌های آن.
- `.github/workflows/`: ساخت و تست خودکار ویندوز.

## محدوده عملکرد

تصویربرداری و پردازش تصویر به‌صورت محلی انجام می‌شود. این پروژه حساب‌های تلگرام، اتاق‌ها، سرور بازی یا امتیازها را دست‌کاری نمی‌کند. استفاده از نرم‌افزار باید مطابق قوانین بازی و سرویس باشد.
