using System.ComponentModel;
using System.Drawing;
using LumberJackX.Core;

namespace LumberJackX.App;

internal sealed class MainForm : Form
{
    private readonly AppConfig _config;
    private readonly string _configPath;
    private readonly SessionCountdown _session = new();
    private readonly PreviewSurface _preview = new();
    private readonly System.Windows.Forms.Timer _captureTimer = new() { Interval = 50 };
    private readonly StatusStrip _statusStrip = new();
    private readonly ToolStripStatusLabel _statusLabel = new() { Spring = true, TextAlign = ContentAlignment.MiddleLeft };

    private readonly NumericUpDown _xInput = CreateNumeric(-32768, 32767, 100, 70);
    private readonly NumericUpDown _yInput = CreateNumeric(-32768, 32767, 100, 70);
    private readonly NumericUpDown _widthInput = CreateNumeric(100, 16384, 400, 70);
    private readonly NumericUpDown _heightInput = CreateNumeric(100, 16384, 600, 70);
    private readonly NumericUpDown _secondsInput = CreateNumeric(1, 86400, 3600, 84);

    private readonly Button _addButton = CreateButton("افزودن دایره", 112);
    private readonly Button _leftButton = CreateButton("چپ", 60);
    private readonly Button _rightButton = CreateButton("راست", 60);
    private readonly Button _startButton = CreateButton("شروع", 86);
    private readonly Button _saveButton = CreateButton("ذخیره", 78);
    private readonly Button _applyButton = CreateButton("اعمال محدوده", 110);

    private readonly ToolTip _toolTip = new();
    private int _selectedMarkerIndex = -1;
    private bool _addCircleMode;
    private bool _nativeWarningShown;
    private DateTime _statusExpiresUtc = DateTime.MinValue;

    public MainForm(AppConfig config, string configPath, string? startupWarning)
    {
        _config = config;
        _configPath = configPath;

        Text = "LumberJackX | پیش‌نمایش و تنظیم کنترل‌ها";
        StartPosition = FormStartPosition.CenterScreen;
        MinimumSize = new Size(820, 620);
        Size = new Size(1100, 850);
        KeyPreview = true;

        BuildLayout();
        PopulateInputs();
        RefreshMarkers();

        _preview.ImagePointClicked += OnImagePointClicked;
        _addButton.Click += (_, _) => EnterAddCircleMode();
        _leftButton.Click += (_, _) => AssignSelectedMarker(ControlSide.Left);
        _rightButton.Click += (_, _) => AssignSelectedMarker(ControlSide.Right);
        _startButton.Click += (_, _) => ToggleSession();
        _saveButton.Click += (_, _) => SaveSettings(showMessage: true);
        _applyButton.Click += (_, _) => ApplyCaptureSettings();
        KeyDown += OnFormKeyDown;

        _captureTimer.Tick += (_, _) => CaptureTick();
        Shown += (_, _) => _captureTimer.Start();
        FormClosing += (_, _) =>
        {
            _captureTimer.Stop();
            SaveSettings(showMessage: false);
            _session.Stop();
        };

        if (!string.IsNullOrWhiteSpace(startupWarning))
        {
            SetStatus(startupWarning, TimeSpan.FromSeconds(10));
        }
    }

    private void BuildLayout()
    {
        var root = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            ColumnCount = 1,
            RowCount = 3,
            Margin = Padding.Empty,
            Padding = Padding.Empty
        };
        root.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        root.RowStyles.Add(new RowStyle(SizeType.Absolute, 104));
        root.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        root.RowStyles.Add(new RowStyle(SizeType.Absolute, 25));

        var toolbar = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            ColumnCount = 1,
            RowCount = 2,
            Padding = new Padding(5),
            BackColor = Color.FromArgb(38, 43, 51)
        };
        toolbar.RowStyles.Add(new RowStyle(SizeType.Absolute, 43));
        toolbar.RowStyles.Add(new RowStyle(SizeType.Percent, 100));

        var actions = new FlowLayoutPanel
        {
            Dock = DockStyle.Fill,
            FlowDirection = FlowDirection.LeftToRight,
            WrapContents = false,
            AutoScroll = true,
            Margin = Padding.Empty
        };
        actions.Controls.AddRange([
            _addButton, _leftButton, _rightButton, _startButton, _saveButton
        ]);

        var settings = new FlowLayoutPanel
        {
            Dock = DockStyle.Fill,
            FlowDirection = FlowDirection.LeftToRight,
            WrapContents = false,
            AutoScroll = true,
            Margin = Padding.Empty,
            Padding = new Padding(0, 2, 0, 0)
        };
        settings.Controls.Add(CreateNumericField("X", _xInput));
        settings.Controls.Add(CreateNumericField("Y", _yInput));
        settings.Controls.Add(CreateNumericField("عرض", _widthInput));
        settings.Controls.Add(CreateNumericField("ارتفاع", _heightInput));
        settings.Controls.Add(CreateNumericField("مدت (ثانیه)", _secondsInput, 116));
        settings.Controls.Add(_applyButton);

        toolbar.Controls.Add(actions, 0, 0);
        toolbar.Controls.Add(settings, 0, 1);

        _statusStrip.SizingGrip = false;
        _statusStrip.Items.Add(_statusLabel);
        _statusLabel.Text = "در حال آماده‌سازی پیش‌نمایش...";

        root.Controls.Add(toolbar, 0, 0);
        root.Controls.Add(_preview, 0, 1);
        root.Controls.Add(_statusStrip, 0, 2);
        Controls.Add(root);

        _toolTip.SetToolTip(_addButton, "A: افزودن دایره؛ سپس روی محل دکمه در تصویر کلیک کنید.");
        _toolTip.SetToolTip(_leftButton, "L: نقش دکمه چپ را به دایره انتخاب‌شده بدهید.");
        _toolTip.SetToolTip(_rightButton, "R: نقش دکمه راست را به دایره انتخاب‌شده بدهید.");
        _toolTip.SetToolTip(_startButton, "S: فقط زمان‌سنج نشست را شروع یا متوقف می‌کند.");
        _toolTip.SetToolTip(_saveButton, "ذخیره تنظیمات در پوشه محلی کاربر.");
        _toolTip.SetToolTip(_applyButton, "اعمال مختصات و اندازه جدید محدوده تصویربرداری.");
    }

    private static NumericUpDown CreateNumeric(
        decimal minimum, decimal maximum, decimal initial, int width)
    {
        return new NumericUpDown
        {
            Minimum = minimum,
            Maximum = maximum,
            Value = Math.Clamp(initial, minimum, maximum),
            Width = width,
            DecimalPlaces = 0,
            ThousandsSeparator = false,
            TextAlign = HorizontalAlignment.Center,
            Margin = new Padding(2, 3, 2, 2)
        };
    }

    private static Button CreateButton(string text, int width)
    {
        return new Button
        {
            Text = text,
            Width = width,
            Height = 34,
            Margin = new Padding(3, 2, 3, 2),
            UseVisualStyleBackColor = true
        };
    }

    private static Control CreateNumericField(
        string title, NumericUpDown numeric, int panelWidth = 100)
    {
        var panel = new FlowLayoutPanel
        {
            Width = panelWidth,
            Height = 34,
            FlowDirection = FlowDirection.LeftToRight,
            WrapContents = false,
            Margin = new Padding(3, 0, 3, 0),
            Padding = Padding.Empty
        };
        panel.Controls.Add(new Label
        {
            Text = title,
            AutoSize = true,
            Margin = new Padding(0, 8, 4, 0)
        });
        panel.Controls.Add(numeric);
        return panel;
    }

    private void PopulateInputs()
    {
        _xInput.Value = _config.CaptureRegion.X;
        _yInput.Value = _config.CaptureRegion.Y;
        _widthInput.Value = _config.CaptureRegion.Width;
        _heightInput.Value = _config.CaptureRegion.Height;
        _secondsInput.Value = _config.SessionSeconds;
    }

    private void CaptureTick()
    {
        if (WindowState == FormWindowState.Minimized)
        {
            return;
        }

        try
        {
            var frame = Win32ScreenCapture.Capture(_config.CaptureRegion);
            _preview.SetFrame(frame);

            var detection = NativeVision.Detect(frame);
            if (!detection.IsAvailable && !_nativeWarningShown)
            {
                _nativeWarningShown = true;
                SetStatus(
                    $"کتابخانه تشخیص بارگذاری نشد: {detection.Error}",
                    timeout: TimeSpan.FromDays(365));
            }

            if (_session.IsRunning && _session.IsExpired)
            {
                StopSession("زمان نشست تمام شد؛ اجرا متوقف شد.");
            }

            if (_session.IsRunning && DateTime.UtcNow >= _statusExpiresUtc)
            {
                SetStatus(
                    $"نشست فعال است | زمان باقی‌مانده: {_session.RemainingSeconds} ثانیه | تشخیص شاخه: نامشخص");
            }
            else if (!_session.IsRunning &&
                     detection.IsAvailable &&
                     DateTime.UtcNow >= _statusExpiresUtc)
            {
                SetStatus("پیش‌نمایش فعال است | تشخیص شاخه: نامشخص (نسخه موقت)");
            }
        }
        catch (Exception exception) when (
            exception is Win32Exception or
                ArgumentException or
                OutOfMemoryException)
        {
            if (DateTime.UtcNow >= _statusExpiresUtc)
            {
                SetStatus($"دریافت تصویر ناموفق بود: {exception.Message}");
            }
        }
    }

    private void EnterAddCircleMode()
    {
        _addCircleMode = true;
        SetStatus("حالت افزودن فعال شد؛ روی مرکز یکی از دکمه‌های بازی در تصویر کلیک کنید.");
    }

    private void OnImagePointClicked(PixelPoint point)
    {
        if (_addCircleMode)
        {
            _config.Controls.Add(new ControlMarker
            {
                X = point.X,
                Y = point.Y,
                Side = ControlSide.Unassigned
            });
            _selectedMarkerIndex = _config.Controls.Count - 1;
            _addCircleMode = false;
            RefreshMarkers();
            SaveSettings(showMessage: false);
            SetStatus("دایره اضافه شد؛ آن را انتخاب کنید و نقش چپ یا راست را تعیین کنید.");
            return;
        }

        var nearestIndex = -1;
        var nearestDistanceSquared = 36 * 36;
        for (var index = 0; index < _config.Controls.Count; index++)
        {
            var marker = _config.Controls[index];
            var dx = marker.X - point.X;
            var dy = marker.Y - point.Y;
            var distanceSquared = dx * dx + dy * dy;
            if (distanceSquared <= nearestDistanceSquared)
            {
                nearestDistanceSquared = distanceSquared;
                nearestIndex = index;
            }
        }

        _selectedMarkerIndex = nearestIndex;
        RefreshMarkers();
        SetStatus(nearestIndex >= 0
            ? "دایره انتخاب شد؛ نقش چپ یا راست را تعیین کنید."
            : "برای انتخاب، نزدیک مرکز یکی از دایره‌ها کلیک کنید.");
    }

    private void AssignSelectedMarker(ControlSide side)
    {
        if (_selectedMarkerIndex < 0 || _selectedMarkerIndex >= _config.Controls.Count)
        {
            SetStatus("ابتدا یک دایره را در پیش‌نمایش انتخاب کنید.");
            return;
        }

        foreach (var marker in _config.Controls)
        {
            if (marker.Side == side)
            {
                marker.Side = ControlSide.Unassigned;
            }
        }

        _config.Controls[_selectedMarkerIndex].Side = side;
        RefreshMarkers();
        SaveSettings(showMessage: false);
        SetStatus(side == ControlSide.Left
            ? "دایره انتخاب‌شده به‌عنوان کنترل چپ ثبت شد."
            : "دایره انتخاب‌شده به‌عنوان کنترل راست ثبت شد.");
    }

    private void ToggleSession()
    {
        if (_session.IsRunning)
        {
            StopSession("نشست متوقف شد.");
            return;
        }

        var hasLeft = _config.Controls.Any(marker => marker.Side == ControlSide.Left);
        var hasRight = _config.Controls.Any(marker => marker.Side == ControlSide.Right);
        if (!hasLeft || !hasRight)
        {
            SetStatus("برای شروع، ابتدا یک دایره چپ و یک دایره راست مشخص کنید.");
            return;
        }

        _config.SessionSeconds = decimal.ToInt32(_secondsInput.Value);
        _session.Start(_config.SessionSeconds);
        _startButton.Text = "توقف";
        SetStatus("نشست شروع شد؛ این نسخه فقط زمان‌سنج را اجرا می‌کند و ورودی بازی نمی‌فرستد.");
        SaveSettings(showMessage: false);
    }

    private void StopSession(string message)
    {
        _session.Stop();
        _startButton.Text = "شروع";
        SetStatus(message);
    }

    private void ApplyCaptureSettings()
    {
        var region = new CaptureRegion
        {
            X = decimal.ToInt32(_xInput.Value),
            Y = decimal.ToInt32(_yInput.Value),
            Width = decimal.ToInt32(_widthInput.Value),
            Height = decimal.ToInt32(_heightInput.Value)
        };

        try
        {
            region.Validate();
            _session.Stop();
            _startButton.Text = "شروع";
            _config.CaptureRegion = region;
            _config.SessionSeconds = decimal.ToInt32(_secondsInput.Value);
            _config.Normalize();
            _selectedMarkerIndex = -1;
            RefreshMarkers();
            SaveSettings(showMessage: false);
            SetStatus("محدوده تصویربرداری اعمال شد.");
        }
        catch (ArgumentOutOfRangeException exception)
        {
            SetStatus($"محدوده نامعتبر است: {exception.Message}");
        }
    }

    private void RefreshMarkers()
    {
        _preview.SelectedMarkerIndex = _selectedMarkerIndex;
        _preview.SetMarkers(_config.Controls);
    }

    private void SaveSettings(bool showMessage)
    {
        try
        {
            _config.SessionSeconds = decimal.ToInt32(_secondsInput.Value);
            AppConfigStore.Save(_config, _configPath);
            if (showMessage)
            {
                SetStatus("تنظیمات ذخیره شد.");
            }
        }
        catch (Exception exception) when (
            exception is IOException or UnauthorizedAccessException or ArgumentException)
        {
            SetStatus($"ذخیره تنظیمات ناموفق بود: {exception.Message}");
        }
    }

    private void OnFormKeyDown(object? sender, KeyEventArgs e)
    {
        switch (e.KeyCode)
        {
            case Keys.A:
                EnterAddCircleMode();
                e.SuppressKeyPress = true;
                break;
            case Keys.L:
                AssignSelectedMarker(ControlSide.Left);
                e.SuppressKeyPress = true;
                break;
            case Keys.R:
                AssignSelectedMarker(ControlSide.Right);
                e.SuppressKeyPress = true;
                break;
            case Keys.S:
                ToggleSession();
                e.SuppressKeyPress = true;
                break;
            case Keys.Delete:
                RemoveSelectedMarker();
                e.SuppressKeyPress = true;
                break;
            case Keys.Escape:
            case Keys.Q:
                Close();
                e.SuppressKeyPress = true;
                break;
        }
    }

    private void RemoveSelectedMarker()
    {
        if (_selectedMarkerIndex < 0 || _selectedMarkerIndex >= _config.Controls.Count)
        {
            return;
        }

        _config.Controls.RemoveAt(_selectedMarkerIndex);
        _selectedMarkerIndex = -1;
        RefreshMarkers();
        SaveSettings(showMessage: false);
        SetStatus("دایره انتخاب‌شده حذف شد.");
    }

    private void SetStatus(string message, TimeSpan? timeout = null)
    {
        _statusLabel.Text = message;
        _statusExpiresUtc = DateTime.UtcNow + (timeout ?? TimeSpan.FromSeconds(3));
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            _captureTimer.Dispose();
            _toolTip.Dispose();
        }

        base.Dispose(disposing);
    }
}
