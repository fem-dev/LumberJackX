using System.Diagnostics;

namespace LumberJackX.Core;

public sealed class SessionCountdown
{
    private Stopwatch? _stopwatch;
    private TimeSpan _duration;

    public bool IsRunning => _stopwatch?.IsRunning == true;

    public int RemainingSeconds
    {
        get
        {
            if (_stopwatch is null)
            {
                return 0;
            }

            var remaining = _duration - _stopwatch.Elapsed;
            return remaining <= TimeSpan.Zero
                ? 0
                : (int)Math.Ceiling(remaining.TotalSeconds);
        }
    }

    public bool IsExpired => _stopwatch is not null && RemainingSeconds == 0;

    public void Start(int seconds)
    {
        if (seconds <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(seconds));
        }

        _duration = TimeSpan.FromSeconds(seconds);
        _stopwatch = Stopwatch.StartNew();
    }

    public void Stop()
    {
        _stopwatch?.Stop();
        _stopwatch = null;
        _duration = TimeSpan.Zero;
    }
}
