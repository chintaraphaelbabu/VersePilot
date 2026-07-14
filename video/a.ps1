# Folder where Shotcut exports the MP4s
$folder = "C:\Users\Raphael\Documents\verses\video"

# How many seconds the file must remain unchanged
$stableSeconds = 5

# Remember file sizes and when they last changed
$files = @{}

Write-Host "Watching $folder..."
Write-Host ""

while ($true) {

    Get-ChildItem $folder -Filter *.mp4 | ForEach-Object {

        $file = $_.FullName
        $mp3 = [System.IO.Path]::ChangeExtension($file, ".mp3")

        # Already converted
        if (Test-Path $mp3) {
            return
        }

        $size = $_.Length

        if (-not $files.ContainsKey($file)) {
            $files[$file] = @{
                Size = $size
                LastChanged = Get-Date
            }
            return
        }

        if ($files[$file].Size -ne $size) {
            $files[$file].Size = $size
            $files[$file].LastChanged = Get-Date
            return
        }

        $elapsed = (Get-Date) - $files[$file].LastChanged

        if ($elapsed.TotalSeconds -ge $stableSeconds) {

            # Make sure Shotcut has released the file
            try {
                $stream = [System.IO.File]::Open($file, 'Open', 'ReadWrite', 'None')
                $stream.Close()
            }
            catch {
                return
            }

            Write-Host "Converting $($_.Name)..."

            ffmpeg -y -i "$file" "$mp3"

            if ($LASTEXITCODE -eq 0) {
                Write-Host "Done: $($_.Name)"
                $files.Remove($file)
            }
        }
    }

    Start-Sleep 2
}