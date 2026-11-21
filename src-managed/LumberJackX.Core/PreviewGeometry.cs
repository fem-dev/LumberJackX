namespace LumberJackX.Core;

public readonly record struct PreviewBounds(
    double X,
    double Y,
    double Width,
    double Height,
    double Scale);

public readonly record struct PixelPoint(int X, int Y);

public static class PreviewGeometry
{
    public static PreviewBounds Calculate(
        double viewportWidth,
        double viewportHeight,
        int imageWidth,
        int imageHeight)
    {
        if (viewportWidth <= 0 || viewportHeight <= 0 || imageWidth <= 0 || imageHeight <= 0)
        {
            return new PreviewBounds(0, 0, 0, 0, 0);
        }

        var scale = Math.Min(viewportWidth / imageWidth, viewportHeight / imageHeight);
        var width = imageWidth * scale;
        var height = imageHeight * scale;

        return new PreviewBounds(
            (viewportWidth - width) / 2.0,
            (viewportHeight - height) / 2.0,
            width,
            height,
            scale);
    }

    public static bool TryMapPoint(
        double clientX,
        double clientY,
        double viewportWidth,
        double viewportHeight,
        int imageWidth,
        int imageHeight,
        out PixelPoint point)
    {
        point = default;
        var bounds = Calculate(viewportWidth, viewportHeight, imageWidth, imageHeight);
        if (bounds.Scale <= 0 ||
            clientX < bounds.X ||
            clientY < bounds.Y ||
            clientX >= bounds.X + bounds.Width ||
            clientY >= bounds.Y + bounds.Height)
        {
            return false;
        }

        var imageX = (int)Math.Floor((clientX - bounds.X) / bounds.Scale);
        var imageY = (int)Math.Floor((clientY - bounds.Y) / bounds.Scale);

        point = new PixelPoint(
            Math.Clamp(imageX, 0, imageWidth - 1),
            Math.Clamp(imageY, 0, imageHeight - 1));
        return true;
    }
}
