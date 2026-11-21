namespace LumberJackX.Core;

public enum ControlSide
{
    Unassigned = 0,
    Left = 1,
    Right = 2
}

public sealed class ControlMarker
{
    public int X { get; set; }
    public int Y { get; set; }
    public ControlSide Side { get; set; } = ControlSide.Unassigned;
}

public sealed class CaptureRegion
{
    public int X { get; set; } = 100;
    public int Y { get; set; } = 100;
    public int Width { get; set; } = 400;
    public int Height { get; set; } = 600;

    public void Validate()
    {
        if (Width is < 100 or > 16384 || Height is < 100 or > 16384)
        {
            throw new ArgumentOutOfRangeException(
                nameof(Width), "Capture size must be between 100 and 16384 pixels.");
        }

        if (X is < -32768 or > 32767 || Y is < -32768 or > 32767)
        {
            throw new ArgumentOutOfRangeException(
                nameof(X), "Capture origin is outside the supported desktop coordinate range.");
        }
    }
}

public sealed class AppConfig
{
    public int SchemaVersion { get; set; } = 1;
    public CaptureRegion CaptureRegion { get; set; } = new();
    public int SessionSeconds { get; set; } = 3600;
    public List<ControlMarker> Controls { get; set; } = [];

    public void Normalize()
    {
        if (CaptureRegion is null)
        {
            CaptureRegion = new CaptureRegion();
        }

        try
        {
            CaptureRegion.Validate();
        }
        catch (ArgumentOutOfRangeException)
        {
            CaptureRegion = new CaptureRegion();
        }

        SchemaVersion = 1;
        SessionSeconds = Math.Clamp(SessionSeconds, 1, 24 * 60 * 60);
        Controls ??= [];

        Controls.RemoveAll(marker =>
            marker is null ||
            marker.X < 0 ||
            marker.Y < 0 ||
            marker.X >= CaptureRegion.Width ||
            marker.Y >= CaptureRegion.Height);

        foreach (var marker in Controls)
        {
            if (!Enum.IsDefined(marker.Side))
            {
                marker.Side = ControlSide.Unassigned;
            }
        }
    }
}
