using System.ComponentModel;
using System.Drawing.Drawing2D;
using LumberJackX.Core;

namespace LumberJackX.App;

internal sealed class PreviewSurface : Control
{
    private Bitmap? _image;
    private IReadOnlyList<ControlMarker> _markers = Array.Empty<ControlMarker>();

    public PreviewSurface()
    {
        DoubleBuffered = true;
        BackColor = Color.FromArgb(25, 29, 35);
        ForeColor = Color.White;
        Dock = DockStyle.Fill;
        SetStyle(
            ControlStyles.AllPaintingInWmPaint |
            ControlStyles.UserPaint |
            ControlStyles.OptimizedDoubleBuffer |
            ControlStyles.ResizeRedraw,
            true);
    }

    [Browsable(false)]
    [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
    public int SelectedMarkerIndex { get; set; } = -1;

    public event Action<PixelPoint>? ImagePointClicked;

    public void SetFrame(ImageFrame frame)
    {
        var replacement = CreateBitmap(frame);
        var old = _image;
        _image = replacement;
        old?.Dispose();
        Invalidate();
    }

    public void SetMarkers(IReadOnlyList<ControlMarker> markers)
    {
        _markers = markers;
        Invalidate();
    }

    protected override void OnMouseClick(MouseEventArgs e)
    {
        base.OnMouseClick(e);

        if (e.Button != MouseButtons.Left || _image is null)
        {
            return;
        }

        if (PreviewGeometry.TryMapPoint(
                e.X, e.Y, ClientSize.Width, ClientSize.Height,
                _image.Width, _image.Height, out var point))
        {
            ImagePointClicked?.Invoke(point);
        }
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        e.Graphics.Clear(BackColor);

        if (_image is null)
        {
            using var messageFont = new Font(Font.FontFamily, 12, FontStyle.Regular);
            const string message = "تصویر هنوز دریافت نشده است؛ محدوده تصویربرداری را بررسی کنید.";
            var measured = e.Graphics.MeasureString(message, messageFont);
            e.Graphics.DrawString(
                message, messageFont, Brushes.Gainsboro,
                Math.Max(8, (ClientSize.Width - measured.Width) / 2),
                Math.Max(8, (ClientSize.Height - measured.Height) / 2));
            return;
        }

        var bounds = PreviewGeometry.Calculate(
            ClientSize.Width, ClientSize.Height, _image.Width, _image.Height);
        if (bounds.Scale <= 0)
        {
            return;
        }

        var destination = new RectangleF(
            (float)bounds.X, (float)bounds.Y,
            (float)bounds.Width, (float)bounds.Height);

        e.Graphics.InterpolationMode = InterpolationMode.HighQualityBicubic;
        e.Graphics.PixelOffsetMode = PixelOffsetMode.HighQuality;
        e.Graphics.DrawImage(_image, destination);

        var radius = Math.Max(10f, (float)(22.0 * bounds.Scale));
        using var labelFont = new Font(
            Font.FontFamily,
            Math.Clamp(11f * (float)bounds.Scale, 8f, 14f),
            FontStyle.Bold,
            GraphicsUnit.Point);

        for (var index = 0; index < _markers.Count; index++)
        {
            var marker = _markers[index];
            var centerX = (float)(bounds.X + marker.X * bounds.Scale);
            var centerY = (float)(bounds.Y + marker.Y * bounds.Scale);
            var color = marker.Side switch
            {
                ControlSide.Left => Color.LimeGreen,
                ControlSide.Right => Color.DodgerBlue,
                _ => Color.Gold
            };

            using var markerPen = new Pen(color, 2f);
            e.Graphics.DrawEllipse(
                markerPen, centerX - radius, centerY - radius, radius * 2, radius * 2);

            if (index == SelectedMarkerIndex)
            {
                using var selectionPen = new Pen(Color.White, 1.5f);
                e.Graphics.DrawEllipse(
                    selectionPen,
                    centerX - radius - 5, centerY - radius - 5,
                    (radius + 5) * 2, (radius + 5) * 2);
            }

            var label = marker.Side switch
            {
                ControlSide.Left => "L",
                ControlSide.Right => "R",
                _ => "?"
            };
            var labelSize = e.Graphics.MeasureString(label, labelFont);
            e.Graphics.DrawString(
                label, labelFont, Brushes.White,
                centerX - labelSize.Width / 2,
                centerY - labelSize.Height / 2);
        }
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            _image?.Dispose();
            _image = null;
        }

        base.Dispose(disposing);
    }

    private static Bitmap CreateBitmap(ImageFrame frame)
    {
        var bitmap = new Bitmap(
            frame.Width, frame.Height, System.Drawing.Imaging.PixelFormat.Format32bppArgb);
        var rectangle = new Rectangle(0, 0, frame.Width, frame.Height);
        var data = bitmap.LockBits(
            rectangle,
            System.Drawing.Imaging.ImageLockMode.WriteOnly,
            System.Drawing.Imaging.PixelFormat.Format32bppArgb);

        try
        {
            for (var row = 0; row < frame.Height; row++)
            {
                var sourceOffset = row * frame.Stride;
                var destination = IntPtr.Add(data.Scan0, checked(row * data.Stride));
                System.Runtime.InteropServices.Marshal.Copy(
                    frame.Pixels, sourceOffset, destination, frame.Stride);
            }
        }
        finally
        {
            bitmap.UnlockBits(data);
        }

        return bitmap;
    }
}
