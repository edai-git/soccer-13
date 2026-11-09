Add-Type -AssemblyName System.Drawing

function Resize-Image($srcPath, $dstPath, $targetW, $targetH, $format) {
    $src = [System.Drawing.Image]::FromFile($srcPath)
    $bmp = New-Object System.Drawing.Bitmap($targetW, $targetH)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
    $g.DrawImage($src, 0, 0, $targetW, $targetH)
    $bmp.Save($dstPath, $format)
    $g.Dispose()
    $bmp.Dispose()
    $src.Dispose()
    Write-Host "Resized $srcPath -> $dstPath ($targetW x $targetH)"
}

# 1. PS4 Home Screen icon0.png (512x512)
Resize-Image (Resolve-Path 'assets/logo.png').Path (Join-Path (Resolve-Path 'app/assets').Path 'icon0.png') 512 512 ([System.Drawing.Imaging.ImageFormat]::Png)

# 2. PS4 Home Screen pic0.png & pic1.png (1920x1080)
Resize-Image (Resolve-Path 'assets/bg.jpg').Path (Join-Path (Resolve-Path 'app/assets').Path 'pic0.png') 1920 1080 ([System.Drawing.Imaging.ImageFormat]::Png)
Resize-Image (Resolve-Path 'assets/bg.jpg').Path (Join-Path (Resolve-Path 'app/assets').Path 'pic1.png') 1920 1080 ([System.Drawing.Imaging.ImageFormat]::Png)

# 3. Generate raw 1920x1080 32-bit ARGB background with overlay darkening for the launcher
$srcBg = [System.Drawing.Image]::FromFile((Resolve-Path 'assets/bg.jpg').Path)
$rawBmp = New-Object System.Drawing.Bitmap(1920, 1080, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$g = [System.Drawing.Graphics]::FromImage($rawBmp)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.DrawImage($srcBg, 0, 0, 1920, 1080)

# Apply a dark semi-transparent tint/overlay over the whole background (65% black) so text/menu is crisp and readable
$darkBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(160, 10, 14, 23))
$g.FillRectangle($darkBrush, 0, 0, 1920, 1080)
$darkBrush.Dispose()
$g.Dispose()

# Save raw ARGB buffer
$rect = New-Object System.Drawing.Rectangle(0, 0, 1920, 1080)
$bmpData = $rawBmp.LockBits($rect, [System.Drawing.Imaging.ImageLockMode]::ReadOnly, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$totalBytes = 1920 * 1080 * 4
$bytes = New-Object byte[] $totalBytes
[System.Runtime.InteropServices.Marshal]::Copy($bmpData.Scan0, $bytes, 0, $totalBytes)
$rawBmp.UnlockBits($bmpData)
$rawBmp.Dispose()
$srcBg.Dispose()

$rawPath = Join-Path (Resolve-Path 'app/assets').Path 'bg.raw'
[System.IO.File]::WriteAllBytes($rawPath, $bytes)
Write-Host "Generated raw darkened background: $rawPath ($totalBytes bytes)"

