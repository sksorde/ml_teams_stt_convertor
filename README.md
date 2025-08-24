# Teams Audio/Video Speech-to-Text Converter

Convert Microsoft Teams (or any) meeting recordings (video/audio) to text + subtitles.

## Features
- Upload MP4, MKV, MOV, AVI, MP3, WAV
- Extracts audio automatically
- Transcribes with `faster-whisper` (local, free)
- Export:
  - TXT transcript
  - SRT subtitles
  - VTT subtitles

## Setup

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Notes
- Requires [FFmpeg](https://ffmpeg.org/download.html) installed & on PATH (needed by moviepy).
- Choose model size in `app.py` (default: `small` int8 for laptops).
