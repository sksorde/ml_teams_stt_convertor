# app.py
import streamlit as st
from faster_whisper import WhisperModel
from moviepy.editor import VideoFileClip
import tempfile, os

# ---------------- Page Setup ----------------
st.set_page_config(page_title="Teams Audio/Video to Text", layout="wide")
st.title("🎥 Microsoft Teams Speech-to-Text Converter")

# ---------------- Sidebar Controls ----------------
st.sidebar.header("⚙️ Settings")
model_size = st.sidebar.selectbox(
    "Choose Whisper Model Size",
    ["tiny", "small", "medium", "large-v2"],
    index=1  # default: small
)
device = st.sidebar.radio("Device", ["cpu", "cuda"], index=0)
st.sidebar.caption("💡 'cuda' needs an NVIDIA GPU")

# ---------------- Load Whisper Model (cached) ----------------
@st.cache_resource
def load_model(size, device):
    return WhisperModel(size, device=device, compute_type="int8")

model = load_model(model_size, device)

# ---------------- File Upload ----------------
uploaded_file = st.file_uploader(
    "Upload Teams recording (mp4, mkv, mov, avi, mp3, wav)",
    type=["mp4", "mkv", "mov", "avi", "mp3", "wav"]
)

# ---------------- Process File ----------------
if uploaded_file:
    # Check file size
    if uploaded_file.size > 200 * 1024 * 1024:  # 200 MB
        st.error("⚠️ File too large! Please upload a file under 200 MB.")
    else:
        suffix = uploaded_file.name.split(".")[-1]
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}")
        temp_input.write(uploaded_file.read())
        temp_input.flush()
        temp_input.close()

        audio_path = None
        try:
            # Extract audio if it's a video
            if suffix in ["mp4", "mkv", "mov", "avi"]:
                st.info("🎬 Extracting audio from video...")
                audio_path = temp_input.name + ".wav"
                with VideoFileClip(temp_input.name) as video:
                    video.audio.write_audiofile(audio_path, verbose=False, logger=None)
                os.remove(temp_input.name)
            else:
                audio_path = temp_input.name

            st.info("⏳ Transcribing... please wait.")
            transcript_box = st.empty()

            transcript_text = ""
            srt_content = ""
            vtt_content = "WEBVTT\n\n"

            # Run transcription
            segments, info = model.transcribe(audio_path, language="en")
            st.write(f"🔊 Detected language: {info.language} (prob {info.language_probability:.2f})")

            # Build transcripts & subtitles
            for i, seg in enumerate(segments, start=1):
                start = f"{int(seg.start//3600):02}:{int((seg.start%3600)//60):02}:{int(seg.start%60):02},{int((seg.start%1)*1000):03}"
                end   = f"{int(seg.end//3600):02}:{int((seg.end%3600)//60):02}:{int(seg.end%60):02},{int((seg.end%1)*1000):03}"
                vtt_start = start.replace(",", ".")
                vtt_end   = end.replace(",", ".")

                transcript_text += f"[{seg.start:.2f} - {seg.end:.2f}] {seg.text}\n"
                srt_content += f"{i}\n{start} --> {end}\n{seg.text}\n\n"
                vtt_content += f"{i}\n{vtt_start} --> {vtt_end}\n{seg.text}\n\n"

                transcript_box.text_area("Transcript (live)", transcript_text, height=300)

            st.success("✅ Transcription finished!")

            if transcript_text.strip() == "":
                st.error("⚠️ No speech detected. Try another file or check if audio is clear.")

            # Downloads
            st.download_button("📄 Download TXT", transcript_text, "transcript.txt", "text/plain")
            st.download_button("🎬 Download SRT", srt_content, "transcript.srt", "text/plain")
            st.download_button("🌐 Download VTT", vtt_content, "transcript.vtt", "text/vtt")

        finally:
            # Cleanup temp files
            if os.path.exists(temp_input.name):
                os.remove(temp_input.name)
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
