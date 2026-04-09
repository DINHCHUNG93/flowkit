# gla:brand-logo — Apply Channel Brand Logo to Video & Thumbnails

Overlay a channel brand logo on final video and thumbnails to cover the Veo watermark.

Usage: `/gla:brand-logo <channel_name> <video_path> [--size 220] [--thumbnails]`

## Step 1: Locate channel icon

Channel icons are stored at:
```
youtube/channels/<channel_name>/<channel_name>_icon.png
```

Example: `youtube/channels/chiensudachieu/chiensudachieu_icon.png`

**This directory is local-only (gitignored).** Each machine has its own channel assets.

If icon file doesn't exist, ABORT with:
```
Icon not found: youtube/channels/<channel_name>/<channel_name>_icon.png
Please place your channel icon PNG there first.
```

## Step 2: Determine icon size and position

The icon must cover the **Veo watermark** ("V" text) at the bottom-right corner of videos.

| Resolution | Icon Size | Position | Notes |
|-----------|-----------|----------|-------|
| 3840x2160 (4K) | 220x220 | `overlay=W-w-40:H-h-40` | Covers Veo "V" watermark fully |
| 1920x1080 (1080p) | 130x130 | `overlay=W-w-24:H-h-24` | Scaled proportionally |
| 1280x720 (origin) | 110x110 | `overlay=W-w-16:H-h-16` | Veo origin video — watermark ~40px, 110px icon covers it |

User can override with `--size N` (NxN pixels).

**Auto-detect resolution** from input video:
```bash
RES=$(ffprobe -v quiet -show_entries stream=width -of csv=p=0 "$VIDEO")
if [ "$RES" -ge 3840 ]; then SIZE=220; PAD=40
elif [ "$RES" -ge 1920 ]; then SIZE=130; PAD=24
else SIZE=110; PAD=16; fi
```

## Step 3: Apply to video

```bash
ffmpeg -y -i "$VIDEO" -i "$ICON" \
  -filter_complex "[1:v]scale=${SIZE}:${SIZE},format=rgba[icon];[0:v][icon]overlay=W-w-${PAD}:H-h-${PAD}" \
  -c:v libx264 -preset fast -crf 18 -r 24 -pix_fmt yuv420p \
  -c:a copy -movflags +faststart \
  "${VIDEO%.mp4}_branded.mp4"
```

**IMPORTANT: Never downscale. Output resolution = input resolution.**

## Step 4: Apply to thumbnails (if --thumbnails)

```bash
# Get project output directory
PROJ_OUT=$(curl -s http://127.0.0.1:8100/api/projects/<PID>/output-dir)
OUTDIR=$(echo "$PROJ_OUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['path'])")

for thumb in "${OUTDIR}/thumbnails/thumbnail_v"*_yt.png; do
  ffmpeg -y -i "$thumb" -i "$ICON" \
    -filter_complex "[1:v]scale=72:72[icon];[0:v][icon]overlay=W-w-16:H-h-16" \
    "${thumb%_yt.png}_final.png" 2>/dev/null
done
```

Thumbnail icon is always 72x72 (1280x720 images).

## Step 4b: Apply 4K icon (if exists)

Check for a 4K badge icon at:
```
youtube/channels/<channel_name>/4k_icon.png
```

**If file exists AND source video is 4K (width >= 3840):** overlay the 4K icon at the **top-right** corner.

| Resolution | Icon Size | Position | Notes |
|-----------|-----------|----------|-------|
| 3840x2160 (4K) | 180px height (auto-width) | `overlay=W-w-40:40` | Top-right, 40px pad |
| 1920x1080 (1080p) | 100px height (auto-width) | `overlay=W-w-24:24` | Scaled proportionally |

**Skip if:** no `4k_icon.png` found, or source video is not 4K.

```bash
ICON_4K="youtube/channels/<channel_name>/4k_icon.png"
if [ -f "$ICON_4K" ] && [ "$RES" -ge 3840 ]; then
  ffmpeg -y -i "${VIDEO%.mp4}_branded.mp4" -i "$ICON_4K" \
    -filter_complex "[1:v]scale=-1:180,format=rgba[icon4k];[0:v][icon4k]overlay=W-w-40:40" \
    -c:v libx264 -preset fast -crf 18 -r 24 -pix_fmt yuv420p \
    -c:a copy -movflags +faststart \
    "${VIDEO%.mp4}_branded_4k.mp4"
fi
```

Output: `*_branded_4k.mp4` (with both brand logo bottom-right + 4K badge top-right).

## Step 5: Verify

```bash
# Check video is valid
ffprobe -v quiet -show_entries format=duration -of csv=p=0 "${VIDEO%.mp4}_branded.mp4"
ffprobe -v quiet -show_entries stream=width,height -of csv=p=0 "${VIDEO%.mp4}_branded.mp4"
ls -lh "${VIDEO%.mp4}_branded.mp4"
```

Print:
```
Brand icon applied: <channel_name>
  Video: <output_path>
  Duration: X:XX
  Resolution: WxH
  Brand logo: <size>x<size> at bottom-right
  4K badge: 180px at top-right (if applied)
  Size: XXX MB
```

## Channel Directory Structure

```
youtube/
  channels/
    chiensudachieu/
      chiensudachieu_icon.png    # Channel brand logo (square, transparent bg recommended)
      4k_icon.png                # Optional 4K badge (auto-applied to top-right for 4K videos)
    another_channel/
      another_channel_icon.png
```

- Directory `youtube/channels/` is **gitignored** — local only per machine
- Icon should be **square PNG** with transparent background for best overlay
- Minimum 220x220 source resolution (scaled down for smaller videos)
