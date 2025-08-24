# app.py
import streamlit as st
from faster_whisper import WhisperModel
from moviepy.editor import VideoFileClip
import tempfile, os

st.set_page_config(page_title="Teams Audio/Video to Text", layout="wide")
st.title("🎥 Microsoft Teams Speech-to-Text Converter")

@st.cache_resource
def load_model():
    return WhisperModel("small", compute_type="int8")

model = load_model()

uploaded_file = st.file_uploader(
    "Upload Teams recording (mp4, mkv, mov, avi, mp3, wav)",
    type=["mp4", "mkv", "mov", "avi", "mp3", "wav"]
)

if uploaded_file:
    suffix = uploaded_file.name.split(".")[-1]
    temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}")
    temp_input.write(uploaded_file.read())
    temp_input.flush()
    temp_input.close()

    # Extract audio if needed
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

    # ✅ Correct API usage
    segments, info = model.transcribe(audio_path, language="en")

    st.write(f"🔊 Detected language: {info.language} (prob {info.language_probability:.2f})")

    for i, seg in enumerate(segments, start=1):
        start = f"{int(seg.start//3600):02}:{int((seg.start%3600)//60):02}:{int(seg.start%60):02},{int((seg.start%1)*1000):03}"
        end = f"{int(seg.end//3600):02}:{int((seg.end%3600)//60):02}:{int(seg.end%60):02},{int((seg.end%1)*1000):03}"
        vtt_start = start.replace(",", ".")
        vtt_end = end.replace(",", ".")

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

    os.remove(audio_path)
