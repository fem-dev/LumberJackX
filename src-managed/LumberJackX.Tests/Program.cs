using LumberJackX.Core;

static void Check(bool condition, string name)
{
    if (!condition)
    {
        throw new InvalidOperationException($"Test failed: {name}");
    }

    Console.WriteLine($"PASS: {name}");
}

var defaults = new AppConfig();
Check(defaults.CaptureRegion.Width == 400 && defaults.CaptureRegion.Height == 600,
    "default capture dimensions");
Check(defaults.SessionSeconds == 3600, "default session duration");

var configPath = Path.Combine(Path.GetTempPath(), $"lumberjackx-{Guid.NewGuid():N}.json");
try
{
    var original = new AppConfig
    {
        CaptureRegion = new CaptureRegion { X = -120, Y = 30, Width = 420, Height = 680 },
        SessionSeconds = 125,
        Controls =
        [
            new ControlMarker { X = 90, Y = 500, Side = ControlSide.Left },
            new ControlMarker { X = 320, Y = 500, Side = ControlSide.Right },
            new ControlMarker { X = 210, Y = 480, Side = ControlSide.Unassigned }
        ]
    };

    AppConfigStore.Save(original, configPath);
    var loaded = AppConfigStore.LoadOrDefault(configPath).Config;
    Check(loaded.CaptureRegion.X == -120 && loaded.CaptureRegion.Width == 420,
        "JSON capture-region round trip");
    Check(loaded.SessionSeconds == 125, "JSON session-duration round trip");
    Check(loaded.Controls.Count == 3 &&
          loaded.Controls[0].Side == ControlSide.Left &&
          loaded.Controls[1].Side == ControlSide.Right,
        "JSON marker round trip");
}
finally
{
    if (File.Exists(configPath))
    {
        File.Delete(configPath);
    }
}

var legacyPath = Path.Combine(Path.GetTempPath(), $"lumberjackx-{Guid.NewGuid():N}.yml");
var migratedPath = Path.Combine(Path.GetTempPath(), $"lumberjackx-{Guid.NewGuid():N}.json");
try
{
    File.WriteAllText(
        legacyPath,
        "%YAML:1.0\n---\ncapture_x: 15\ncapture_y: 25\ncapture_width: 420\ncapture_height: 680\nsession_seconds: 125\ncontrols:\n  - { x: 90, y: 500, side: left }\n  - { x: 320, y: 500, side: right }\n");

    var migration = AppConfigStore.LoadOrDefault(migratedPath, legacyPath);
    Check(migration.ImportedLegacyFile, "legacy YAML import flag");
    Check(migration.Config.CaptureRegion.X == 15 &&
          migration.Config.Controls.Count == 2 &&
          migration.Config.Controls[1].Side == ControlSide.Right,
        "legacy YAML values and control markers imported");
    Check(File.Exists(migratedPath), "legacy import writes JSON configuration");
}
finally
{
    if (File.Exists(legacyPath)) File.Delete(legacyPath);
    if (File.Exists(migratedPath)) File.Delete(migratedPath);
}

Check(
    PreviewGeometry.TryMapPoint(200, 0, 800, 600, 400, 600, out var topLeft) &&
    topLeft == new PixelPoint(0, 0),
    "preview maps top-left through letterboxing");
Check(
    PreviewGeometry.TryMapPoint(599.9, 599.9, 800, 600, 400, 600, out var bottomRight) &&
    bottomRight == new PixelPoint(399, 599),
    "preview maps bottom-right within image");
Check(
    !PreviewGeometry.TryMapPoint(199, 300, 800, 600, 400, 600, out _),
    "preview rejects clicks outside the image");

var countdown = new SessionCountdown();
countdown.Start(5);
Check(countdown.IsRunning && countdown.RemainingSeconds is >= 1 and <= 5,
    "session countdown starts");
countdown.Stop();
Check(!countdown.IsRunning && countdown.RemainingSeconds == 0,
    "session countdown stops");

Console.WriteLine("All managed tests passed.");
