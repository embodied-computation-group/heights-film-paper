#!/usr/bin/env bash
# Re-encode the stimulus for web delivery (used from the main run on: media/towerClimb_crf29.mp4).
# Same 1280x720, 25 fps, all 20,222 frames with original timestamps (-fps_mode passthrough);
# audio dropped (the film is played muted, as in the fMRI session); H.264 High, CRF 29, faststart.
# Result 2026-10-04: 146,877,793 bytes (288 MB -> 147 MB), SSIM 0.979 vs original, duration 13:28.88.
# ffmpeg: any build with libx264 (e.g. pip install imageio-ffmpeg; python -c "import imageio_ffmpeg as f; print(f.get_ffmpeg_exe())").
set -euo pipefail
FF="${FFMPEG:-ffmpeg}"
cd "$(dirname "$0")/.."
"$FF" -hide_banner -y -i media/towerClimb.mp4 -map 0:v:0 -c:v libx264 -preset slow -crf 29 -pix_fmt yuv420p \
  -profile:v high -fps_mode passthrough -an -movflags +faststart media/towerClimb_crf29.mp4
# Verify: frame count and SSIM against the original
"$FF" -hide_banner -i media/towerClimb_crf29.mp4 -map 0:v:0 -c copy -f null - 2>&1 | grep -oE "frame= *[0-9]+" | tail -1
"$FF" -hide_banner -i media/towerClimb_crf29.mp4 -i media/towerClimb.mp4 -lavfi "[0:v][1:v]ssim" -f null - 2>&1 | grep -oE "All:[0-9.]+"
