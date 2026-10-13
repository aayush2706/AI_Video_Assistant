
import os
import yt_dlp
from pydub import AudioSegment

# ─── Configuration ──────────────────────────────────────────────
DOWNLOAD_DIR = "downloades"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ─── YouTube Audio Download ─────────────────────────────────────
def download_youtube_audio(url: str) -> str:
    """
    Download audio from a YouTube URL and convert it to WAV.
    Requires FFmpeg to be installed and accessible.
    """
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "noplaylist": True,
        "retries": 3,
        "extractor_retries": 3,
        "socket_timeout": 30,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],
        "quiet": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # Obtain the final output filename reliably.
            filename = ydl.prepare_filename(info)
            filename = os.path.splitext(filename)[0] + ".wav"

        if not os.path.isfile(filename):
            raise FileNotFoundError(
                f"Converted WAV file was not found: {filename}"
            )

        return filename

    except Exception as exc:
        raise RuntimeError(
            f"Could not download YouTube audio: {exc}"
        ) from exc


# ─── Convert Local Audio / Video to WAV ─────────────────────────
def convert_to_wav(input_path: str) -> str:
    """
    Convert a local audio/video file to mono, 16 kHz WAV.
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(
            f"Input file does not exist: {input_path}"
        )

    output_path = os.path.splitext(input_path)[0] + "_converted.wav"

    try:
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_channels(1).set_frame_rate(16000)
        audio.export(output_path, format="wav")
        return output_path

    except Exception as exc:
        raise RuntimeError(
            f"Could not convert input file to WAV: {exc}"
        ) from exc


# ─── Split WAV into Chunks ───────────────────────────────────────
def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list[str]:
    """
    Split a WAV file into chunks of the specified duration.
    Returns a list of chunk file paths.
    """
    if not os.path.isfile(wav_path):
        raise FileNotFoundError(
            f"WAV file does not exist: {wav_path}"
        )

    if chunk_minutes <= 0:
        raise ValueError("chunk_minutes must be greater than zero.")

    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000
    chunks = []

    for index, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start:start + chunk_ms]

        chunk_path = (
            f"{os.path.splitext(wav_path)[0]}_chunk_{index}.wav"
        )

        chunk.export(chunk_path, format="wav")
        chunks.append(chunk_path)

    return chunks


# ─── Main Input Processing ──────────────────────────────────────
def process_input(source: str) -> list[str]:
    """
    Accept a YouTube URL or local audio/video file.
    Convert it to WAV, split it into chunks, and return their paths.
    """
    if not source or not source.strip():
        raise ValueError("Please provide a YouTube URL or file path.")

    source = source.strip()

    if source.startswith(("http://", "https://")):
        print("Detected URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)

    if not chunks:
        raise RuntimeError("No audio chunks were created.")

    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks
