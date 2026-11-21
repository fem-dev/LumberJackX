using System.Runtime.InteropServices;

namespace LumberJackX.App;

internal enum DetectedBranchSide
{
    Unknown = 0,
    Left = 1,
    Right = 2,
    None = 3
}

internal sealed record DetectionResult(
    DetectedBranchSide Side,
    double Confidence,
    string? Error)
{
    public bool IsAvailable => Error is null;
}

internal static class NativeVision
{
    private const string LibraryName = "LumberJackVision.dll";
    private static string? _unavailableError;

    [DllImport(
        LibraryName,
        EntryPoint = "LJX_DetectBranch",
        CallingConvention = CallingConvention.Cdecl,
        ExactSpelling = true)]
    private static extern int DetectBranch(
        IntPtr bgra,
        int width,
        int height,
        int stride,
        out double confidence);

    public static DetectionResult Detect(ImageFrame frame)
    {
        if (_unavailableError is not null)
        {
            return new DetectionResult(DetectedBranchSide.Unknown, 0.0, _unavailableError);
        }

        var pin = GCHandle.Alloc(frame.Pixels, GCHandleType.Pinned);
        try
        {
            var code = DetectBranch(
                pin.AddrOfPinnedObject(),
                frame.Width,
                frame.Height,
                frame.Stride,
                out var confidence);

            var side = Enum.IsDefined(typeof(DetectedBranchSide), code)
                ? (DetectedBranchSide)code
                : DetectedBranchSide.Unknown;

            return new DetectionResult(side, confidence, null);
        }
        catch (Exception exception) when (
            exception is DllNotFoundException or
                EntryPointNotFoundException or
                BadImageFormatException)
        {
            _unavailableError = exception.Message;
            return new DetectionResult(
                DetectedBranchSide.Unknown,
                0.0,
                _unavailableError);
        }
        finally
        {
            pin.Free();
        }
    }
}
