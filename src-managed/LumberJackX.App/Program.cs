using LumberJackX.Core;
using System.Runtime.InteropServices;

namespace LumberJackX.App;

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        ConfigureDpiAwareness();
        ApplicationConfiguration.Initialize();

        var localData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        var appDataDirectory = Path.Combine(localData, "LumberJackX");
        var configPath = Path.Combine(appDataDirectory, "lumberjackx.json");

        var legacyCandidates = new[]
        {
            Path.Combine(AppContext.BaseDirectory, "lumberjackx.yml"),
            Path.Combine(Environment.CurrentDirectory, "lumberjackx.yml")
        };
        var legacyPath = legacyCandidates.FirstOrDefault(File.Exists);

        var loaded = AppConfigStore.LoadOrDefault(configPath, legacyPath);
        Application.Run(new MainForm(loaded.Config, configPath, loaded.Warning));
    }

    private static void ConfigureDpiAwareness()
    {
        try
        {
            _ = SetProcessDpiAwarenessContext(new IntPtr(-4));
        }
        catch (EntryPointNotFoundException)
        {
            _ = SetProcessDPIAware();
        }
    }

    [DllImport("user32.dll")]
    private static extern bool SetProcessDpiAwarenessContext(IntPtr value);

    [DllImport("user32.dll")]
    private static extern bool SetProcessDPIAware();
}
