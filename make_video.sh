#!/bin/bash
# Create a slideshow video from images + audio
# Usage: ./make_video.sh <topic_dir> <audio_file> <output_file>

TOPIC_DIR="$1"
AUDIO="$2"
OUTPUT="$3"

if [ -z "$TOPIC_DIR" ] || [ -z "$AUDIO" ] || [ -z "$OUTPUT" ]; then
    echo "Usage: $0 <topic_dir> <audio_file> <output_file>"
    exit 1
fi

# Get audio duration
DURATION=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$AUDIO" | cut -d. -f1)
NUM_IMAGES=$(ls "$TOPIC_DIR"/img*.jpg 2>/dev/null | wc -l | tr -d ' ')

if [ "$NUM_IMAGES" -eq 0 ]; then
    echo "No images found in $TOPIC_DIR"
    exit 1
fi

# Duration per image
IMG_DUR=$(( (DURATION + NUM_IMAGES - 1) / NUM_IMAGES ))
FADE=1

echo "Audio: ${DURATION}s, Images: ${NUM_IMAGES}, Per image: ${IMG_DUR}s"

# Build inputs and filter
INPUTS=""
FILTER=""
i=0
for img in $(ls "$TOPIC_DIR"/img*.jpg | sort); do
    INPUTS="$INPUTS -loop 1 -t $IMG_DUR -i $img"
    FILTER="${FILTER}[$i:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,setsar=1,fade=t=in:st=0:d=${FADE},fade=t=out:st=$((IMG_DUR - FADE)):d=${FADE}[v${i}];"
    i=$((i + 1))
done

# Concat
CONCAT=""
for j in $(seq 0 $((i - 1))); do
    CONCAT="${CONCAT}[v${j}]"
done
FILTER="${FILTER}${CONCAT}concat=n=${i}:v=1:a=0,format=yuv420p[outv]"

ffmpeg -y $INPUTS -i "$AUDIO" \
    -filter_complex "$FILTER" \
    -map "[outv]" -map "${i}:a" \
    -c:v libx264 -preset fast -crf 23 \
    -c:a aac -b:a 128k \
    -shortest -movflags +faststart \
    "$OUTPUT" 2>&1 | tail -3

if [ -f "$OUTPUT" ] && [ $(stat -f%z "$OUTPUT") -gt 1000 ]; then
    echo "OK: $OUTPUT ($(du -h "$OUTPUT" | cut -f1))"
else
    echo "FAILED: $OUTPUT"
fi
