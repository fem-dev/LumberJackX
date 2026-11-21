using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

namespace LumberJackX.Core;

public sealed record ConfigLoadResult(
    AppConfig Config,
    bool ImportedLegacyFile,
    string? Warning);

public static class AppConfigStore
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        WriteIndented = true,
        Converters = { new JsonStringEnumConverter(JsonNamingPolicy.CamelCase) }
    };

    public static ConfigLoadResult LoadOrDefault(string jsonPath, string? legacyYamlPath = null)
    {
        if (File.Exists(jsonPath))
        {
            try
            {
                var json = File.ReadAllText(jsonPath, Encoding.UTF8);
                var config = JsonSerializer.Deserialize<AppConfig>(json, JsonOptions);
                if (config is null)
                {
                    return new(new AppConfig(), false, "فایل تنظیمات خالی یا نامعتبر است؛ تنظیمات پیش‌فرض بارگذاری شد.");
                }

                config.Normalize();
                return new(config, false, null);
            }
            catch (Exception exception) when (
                exception is IOException or UnauthorizedAccessException or JsonException)
            {
                return new(
                    new AppConfig(),
                    false,
                    $"خواندن تنظیمات ناموفق بود؛ تنظیمات پیش‌فرض بارگذاری شد. {exception.Message}");
            }
        }

        if (!string.IsNullOrWhiteSpace(legacyYamlPath) &&
            File.Exists(legacyYamlPath) &&
            TryImportLegacyYaml(legacyYamlPath, out var imported))
        {
            try
            {
                Save(imported, jsonPath);
                return new(imported, true, "تنظیمات قدیمی YAML به قالب JSON منتقل شد.");
            }
            catch (Exception exception) when (
                exception is IOException or UnauthorizedAccessException)
            {
                return new(imported, true, $"تنظیمات قدیمی خوانده شد، اما ذخیره JSON ناموفق بود. {exception.Message}");
            }
        }

        return new(new AppConfig(), false, null);
    }

    public static void Save(AppConfig config, string path)
    {
        ArgumentNullException.ThrowIfNull(config);
        ArgumentException.ThrowIfNullOrWhiteSpace(path);

        config.Normalize();
        var fullPath = Path.GetFullPath(path);
        var directory = Path.GetDirectoryName(fullPath);
        if (!string.IsNullOrEmpty(directory))
        {
            Directory.CreateDirectory(directory);
        }

        var temporaryPath = fullPath + ".tmp";
        try
        {
            var json = JsonSerializer.Serialize(config, JsonOptions);
            File.WriteAllText(temporaryPath, json, new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
            File.Move(temporaryPath, fullPath, overwrite: true);
        }
        finally
        {
            if (File.Exists(temporaryPath))
            {
                File.Delete(temporaryPath);
            }
        }
    }

    private static bool TryImportLegacyYaml(string path, out AppConfig config)
    {
        config = new AppConfig();

        try
        {
            var text = File.ReadAllText(path);
            if (!text.Contains("capture_width", StringComparison.Ordinal) &&
                !text.Contains("capture_height", StringComparison.Ordinal))
            {
                return false;
            }

            config.CaptureRegion = new CaptureRegion
            {
                X = ReadScalar(text, "capture_x", 100),
                Y = ReadScalar(text, "capture_y", 100),
                Width = ReadScalar(text, "capture_width", 400),
                Height = ReadScalar(text, "capture_height", 600)
            };
            config.SessionSeconds = ReadScalar(text, "session_seconds", 3600);

            var markerPattern = new Regex(
                @"\{\s*x\s*:\s*(-?\d+)\s*,\s*y\s*:\s*(-?\d+)\s*,\s*side\s*:\s*([A-Za-z]+)\s*\}",
                RegexOptions.CultureInvariant);

            foreach (Match match in markerPattern.Matches(text))
            {
                var sideText = match.Groups[3].Value;
                var side = sideText.Equals("left", StringComparison.OrdinalIgnoreCase)
                    ? ControlSide.Left
                    : sideText.Equals("right", StringComparison.OrdinalIgnoreCase)
                        ? ControlSide.Right
                        : ControlSide.Unassigned;

                config.Controls.Add(new ControlMarker
                {
                    X = int.Parse(match.Groups[1].Value, System.Globalization.CultureInfo.InvariantCulture),
                    Y = int.Parse(match.Groups[2].Value, System.Globalization.CultureInfo.InvariantCulture),
                    Side = side
                });
            }

            config.Normalize();
            return true;
        }
        catch (Exception exception) when (
            exception is IOException or UnauthorizedAccessException or FormatException)
        {
            return false;
        }
    }

    private static int ReadScalar(string text, string key, int fallback)
    {
        var match = Regex.Match(
            text,
            @"(?m)^\s*" + Regex.Escape(key) + @"\s*:\s*(-?\d+)",
            RegexOptions.CultureInvariant);

        return match.Success
            ? int.Parse(match.Groups[1].Value, System.Globalization.CultureInfo.InvariantCulture)
            : fallback;
    }
}
