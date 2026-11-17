import asyncio
import os
import re
import tempfile
from pathlib import Path

import requests
import streamlit as st
import edge_tts
from google import genai


# ---------------------------------------------------------
# KONFIGURASI HALAMAN
# ---------------------------------------------------------

st.set_page_config(
    page_title="AI Creator Studio",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 AI Creator Studio")
st.caption("Buat naskah video YouTube dan voiceover dengan bantuan AI.")

GEMINI_MODEL = "gemini-3.1-flash-lite"

COUNTRIES = [
    "United States",
    "Indonesia",
    "United Kingdom",
    "Canada",
    "Australia",
    "Japan",
    "Germany",
    "France",
    "Spain",
    "Brazil",
    "Mexico",
    "Saudi Arabia",
    "South Korea",
    "India",
]

LANGUAGES = [
    "English",
    "Bahasa Indonesia",
    "Japanese",
    "German",
    "French",
    "Spanish",
    "Portuguese",
    "Arabic",
    "Korean",
    "Chinese",
]

VOICE_LIBRARY = {
    "English (US) - Female": "en-US-AriaNeural",
    "English (US) - Male": "en-US-GuyNeural",
    "English (UK) - Female": "en-GB-SoniaNeural",
    "English (UK) - Male": "en-GB-RyanNeural",
    "Bahasa Indonesia - Female": "id-ID-GadisNeural",
    "Bahasa Indonesia - Male": "id-ID-ArdiNeural",
    "Japanese - Female": "ja-JP-NanamiNeural",
    "Japanese - Male": "ja-JP-KeitaNeural",
    "German - Female": "de-DE-KatjaNeural",
    "German - Male": "de-DE-ConradNeural",
    "French - Female": "fr-FR-DeniseNeural",
    "French - Male": "fr-FR-HenriNeural",
    "Spanish - Female": "es-ES-ElviraNeural",
    "Spanish - Male": "es-ES-AlvaroNeural",
    "Portuguese - Female": "pt-BR-FranciscaNeural",
    "Portuguese - Male": "pt-BR-AntonioNeural",
    "Arabic - Female": "ar-SA-ZariyahNeural",
    "Arabic - Male": "ar-SA-HamedNeural",
    "Korean - Female": "ko-KR-SunHiNeural",
    "Korean - Male": "ko-KR-InJoonNeural",
    "Chinese - Female": "zh-CN-XiaoxiaoNeural",
    "Chinese - Male": "zh-CN-YunxiNeural",
}


# ---------------------------------------------------------
# API KEY
# ---------------------------------------------------------

def get_secret(key_name: str):
    """Ambil API key dari Streamlit Secrets atau environment variable."""
    try:
        value = st.secrets.get(key_name, "")
        if value:
            return value
    except Exception:
        pass
    return os.getenv(key_name, "")


def get_gemini_client():
    api_key = get_secret("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

DEFAULTS = {
    "generated_script": "",
    "voiceover_editor": "",
    "audio_bytes": None,
    "audio_filename": "voiceover.mp3",
    "eleven_voices": [],
    "eleven_models": [],
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------------------------------------------------------
# PEMBUAT PROMPT DAN EKSTRAKSI VOICEOVER
# ---------------------------------------------------------

def build_script_prompt(
    topic,
    category,
    video_format,
    target_country,
    text_language,
    duration,
    tone,
    extra_instructions,
):
    if video_format == "YouTube Shorts":
        format_instruction = (
            "Buat naskah YouTube Shorts yang singkat, cepat, dan menarik. "
            "Gunakan hook kuat pada 1-3 detik pertama."
        )
    else:
        format_instruction = (
            "Buat naskah YouTube long-form dengan pembukaan, isi yang runtut, "
            "transisi antarbab, dan penutup yang kuat."
        )

    return f"""
Kamu adalah penulis naskah profesional untuk channel YouTube.

DETAIL KONTEN:
- Topik: {topic}
- Kategori: {category}
- Format: {video_format}
- Negara target penonton: {target_country}
- Bahasa teks di layar dan naskah: {text_language}
- Durasi target: {duration}
- Gaya penyampaian: {tone}
- Instruksi tambahan: {extra_instructions or "Tidak ada"}

INSTRUKSI:
{format_instruction}
Sesuaikan contoh, istilah, konteks budaya, dan gaya penyampaian dengan
penonton dari negara target. Jangan mengklaim fakta yang tidak pasti.
Buat naskah yang orisinal, enak didengar, dan tidak bertele-tele.

FORMAT OUTPUT WAJIB:

VIDEO TITLE:
Judul video yang menarik.

HOOK:
Kalimat pembuka yang membuat penonton penasaran.

FULL VIDEO SCRIPT:
Naskah lengkap. Sertakan arahan visual atau teks layar bila relevan.
Teks layar harus menggunakan bahasa yang dipilih.

VOICEOVER SCRIPT:
Tuliskan hanya kalimat yang akan dibacakan narator. Jangan masukkan
catatan visual, arahan editor, label adegan, atau instruksi dalam kurung.
Gunakan bahasa {text_language}.

VIDEO DESCRIPTION:
Deskripsi YouTube yang relevan.

HASHTAGS:
Hashtag yang relevan.
"""


def extract_voiceover(script: str) -> str:
    """Ambil bagian VOICEOVER SCRIPT dari hasil Gemini."""
    if not script:
        return ""

    match = re.search(
        r"VOICEOVER SCRIPT\s*:\s*(.*?)(?=\n\s*(?:VIDEO DESCRIPTION|HASHTAGS)\s*:|\Z)",
        script,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match:
        return match.group(1).strip()

    # Jika format heading tidak ditemukan, gunakan seluruh teks sebagai fallback.
    return script.strip()


# ---------------------------------------------------------
# GEMINI SCRIPT GENERATOR
# ---------------------------------------------------------

def generate_script(prompt: str) -> str:
    client = get_gemini_client()
    if client is None:
        raise ValueError(
            "GEMINI_API_KEY belum ditemukan. Masukkan API key di "
            ".streamlit/secrets.toml atau environment variable."
        )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    if not getattr(response, "text", None):
        raise RuntimeError("Gemini tidak mengembalikan teks. Coba lagi.")
    return response.text.strip()


# ---------------------------------------------------------
# EDGE TTS
# ---------------------------------------------------------

async def edge_tts_to_file(text: str, voice: str, rate: str, output_path: str):
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
    )
    await communicate.save(output_path)


def generate_edge_audio(text: str, voice: str, rate: str) -> bytes:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
        temp_path = temp_file.name

    try:
        asyncio.run(edge_tts_to_file(text, voice, rate, temp_path))
        return Path(temp_path).read_bytes()
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


# ---------------------------------------------------------
# ELEVENLABS API
# ---------------------------------------------------------

ELEVENLABS_BASE_URL = "https://api.elevenlabs.io"


def elevenlabs_headers():
    api_key = get_secret("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError(
            "ELEVENLABS_API_KEY belum ditemukan di .streamlit/secrets.toml."
        )
    return {"xi-api-key": api_key}


@st.cache_data(ttl=300, show_spinner=False)
def fetch_elevenlabs_voices(api_key: str):
    response = requests.get(
        f"{ELEVENLABS_BASE_URL}/v2/voices",
        headers={"xi-api-key": api_key},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("voices", [])


@st.cache_data(ttl=300, show_spinner=False)
def fetch_elevenlabs_models(api_key: str):
    response = requests.get(
        f"{ELEVENLABS_BASE_URL}/v1/models",
        headers={"xi-api-key": api_key},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def generate_elevenlabs_audio(
    text: str,
    voice_id: str,
    model_id: str,
    stability: float,
    similarity_boost: float,
    style: float,
    speed: float,
    speaker_boost: bool,
) -> bytes:
    headers = elevenlabs_headers()
    headers["Content-Type"] = "application/json"

    url = (
        f"{ELEVENLABS_BASE_URL}/v1/text-to-speech/"
        f"{voice_id}?output_format=mp3_44100_128"
    )

    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
            "use_speaker_boost": speaker_boost,
            "speed": speed,
        },
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=120,
    )
    if not response.ok:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise RuntimeError(f"ElevenLabs API error ({response.status_code}): {detail}")

    return response.content


# ---------------------------------------------------------
# SIDEBAR: PENGATURAN KONTEN
# ---------------------------------------------------------

with st.sidebar:
    st.header("⚙️ Pengaturan Konten")

    target_country = st.selectbox(
        "Target Negara",
        COUNTRIES,
        index=0,
        help="United States menjadi target default.",
    )

    text_language = st.selectbox(
        "Bahasa Teks & Naskah",
        LANGUAGES,
        index=0,
        help="Bahasa untuk naskah dan teks yang tampil di layar video.",
    )

    video_format = st.radio(
        "Format Video",
        ["YouTube Shorts", "YouTube Long-form"],
    )

    category = st.selectbox(
        "Kategori Konten",
        [
            "Horror Stories",
            "Facts",
            "History",
            "Mysteries",
            "Science",
            "Technology",
            "Education",
            "Motivation",
        ],
    )

    if video_format == "YouTube Shorts":
        duration = st.selectbox(
            "Durasi Target",
            ["30-45 detik", "45-60 detik", "60-90 detik"],
        )
    else:
        duration = st.selectbox(
            "Durasi Target",
            ["3-5 menit", "5-8 menit", "8-12 menit", "12-15 menit", "15-20 menit"],
        )

    tone = st.selectbox(
        "Gaya Penyampaian",
        [
            "Engaging dan cinematic",
            "Misterius dan menegangkan",
            "Informatif dan edukatif",
            "Santai dan storytelling",
            "Dokumenter profesional",
        ],
    )


# ---------------------------------------------------------
# TAB UTAMA
# ---------------------------------------------------------

tab_script, tab_voice = st.tabs(["📝 Script Generator", "🎙️ Voice Generator"])

with tab_script:
    st.subheader("Buat Naskah Video")

    topic = st.text_input(
        "Topik video",
        placeholder="Contoh: The most mysterious places on Earth",
    )

    extra_instructions = st.text_area(
        "Instruksi tambahan (opsional)",
        placeholder="Contoh: Buat opening yang sangat kuat dan hindari spoiler.",
        height=100,
    )

    if st.button("✨ Generate Script", type="primary", use_container_width=True):
        if not topic.strip():
            st.warning("Isi topik video terlebih dahulu.")
        else:
            prompt = build_script_prompt(
                topic=topic.strip(),
                category=category,
                video_format=video_format,
                target_country=target_country,
                text_language=text_language,
                duration=duration,
                tone=tone,
                extra_instructions=extra_instructions.strip(),
            )

            with st.spinner("Gemini sedang membuat naskah..."):
                try:
                    result = generate_script(prompt)
                    st.session_state.generated_script = result
                    st.session_state.voiceover_editor = extract_voiceover(result)
                    st.session_state.audio_bytes = None
                    st.success("Naskah berhasil dibuat!")
                except Exception as error:
                    st.error(f"Gagal membuat naskah: {error}")

    if st.session_state.generated_script:
        st.markdown("### Hasil Naskah")
        st.text_area(
            "Generated Script",
            key="generated_script",
            height=420,
        )
        st.download_button(
            "⬇️ Download Script (.txt)",
            data=st.session_state.generated_script,
            file_name="youtube_script.txt",
            mime="text/plain",
            use_container_width=True,
        )

with tab_voice:
    st.subheader("Buat Voiceover")
    st.caption("Pilih Edge TTS atau ElevenLabs untuk mengubah naskah menjadi audio.")

    if not st.session_state.voiceover_editor and st.session_state.generated_script:
        st.session_state.voiceover_editor = extract_voiceover(
            st.session_state.generated_script
        )

    voice_text = st.text_area(
        "Voiceover Text",
        key="voiceover_editor",
        height=260,
        placeholder="Generate script terlebih dahulu atau tempel teks voiceover di sini.",
    )

    tts_provider = st.radio(
        "Penyedia Voice",
        ["Edge TTS (Gratis)", "ElevenLabs"],
        horizontal=True,
    )

    if tts_provider == "Edge TTS (Gratis)":
        selected_voice_label = st.selectbox(
            "Pilih Suara",
            list(VOICE_LIBRARY.keys()),
        )
        selected_edge_voice = VOICE_LIBRARY[selected_voice_label]

        rate_percent = st.slider(
            "Kecepatan Suara",
            min_value=-30,
            max_value=30,
            value=0,
            step=5,
        )
        edge_rate = f"{rate_percent:+d}%"

        if st.button("🎧 Generate Voiceover (Edge TTS)", type="primary"):
            if not voice_text.strip():
                st.warning("Teks voiceover masih kosong.")
            else:
                with st.spinner("Sedang membuat audio dengan Edge TTS..."):
                    try:
                        audio = generate_edge_audio(
                            voice_text.strip(),
                            selected_edge_voice,
                            edge_rate,
                        )
                        st.session_state.audio_bytes = audio
                        st.session_state.audio_filename = "voiceover_edge_tts.mp3"
                        st.success("Voiceover berhasil dibuat!")
                    except Exception as error:
                        st.error(f"Gagal membuat voiceover: {error}")

    else:
        eleven_key = get_secret("ELEVENLABS_API_KEY")

        if not eleven_key:
            st.warning(
                "API key ElevenLabs belum dipasang. Tambahkan "
                "ELEVENLABS_API_KEY ke .streamlit/secrets.toml."
            )
        else:
            try:
                with st.spinner("Mengambil daftar voice dan model ElevenLabs..."):
                    voices = fetch_elevenlabs_voices(eleven_key)
                    models = fetch_elevenlabs_models(eleven_key)

                if not voices:
                    st.warning("Tidak ada voice yang ditemukan di akun ElevenLabs.")
                elif not models:
                    st.warning("Daftar model ElevenLabs tidak tersedia.")
                else:
                    voice_options = {
                        f"{voice.get('name', 'Unnamed')} — {voice.get('voice_id', '')}":
                        voice.get("voice_id")
                        for voice in voices
                        if voice.get("voice_id")
                    }

                    model_options = {
                        model.get("name", model.get("model_id", "Model")):
                        model.get("model_id")
                        for model in models
                        if model.get("model_id")
                    }

                    chosen_voice_label = st.selectbox(
                        "Pilih Voice ElevenLabs",
                        list(voice_options.keys()),
                    )
                    chosen_voice_id = voice_options[chosen_voice_label]

                    chosen_model_label = st.selectbox(
                        "Pilih Model ElevenLabs",
                        list(model_options.keys()),
                    )
                    chosen_model_id = model_options[chosen_model_label]

                    col1, col2 = st.columns(2)
                    with col1:
                        stability = st.slider(
                            "Stability",
                            0.0, 1.0, 0.50, 0.05,
                        )
                        similarity_boost = st.slider(
                            "Similarity Boost",
                            0.0, 1.0, 0.75, 0.05,
                        )
                    with col2:
                        style = st.slider(
                            "Style",
                            0.0, 1.0, 0.00, 0.05,
                        )
                        speed = st.slider(
                            "Speed",
                            0.70, 1.20, 1.00, 0.05,
                        )

                    speaker_boost = st.checkbox(
                        "Use Speaker Boost",
                        value=True,
                    )

                    if st.button("🎙️ Generate Voiceover (ElevenLabs)", type="primary"):
                        if not voice_text.strip():
                            st.warning("Teks voiceover masih kosong.")
                        else:
                            with st.spinner("ElevenLabs sedang membuat audio..."):
                                try:
                                    audio = generate_elevenlabs_audio(
                                        text=voice_text.strip(),
                                        voice_id=chosen_voice_id,
                                        model_id=chosen_model_id,
                                        stability=stability,
                                        similarity_boost=similarity_boost,
                                        style=style,
                                        speed=speed,
                                        speaker_boost=speaker_boost,
                                    )
                                    st.session_state.audio_bytes = audio
                                    st.session_state.audio_filename = "voiceover_elevenlabs.mp3"
                                    st.success("Voiceover berhasil dibuat!")
                                except Exception as error:
                                    st.error(f"Gagal membuat voiceover: {error}")

            except Exception as error:
                st.error(f"Tidak bisa mengambil data ElevenLabs: {error}")

    if st.session_state.audio_bytes:
        st.markdown("### Preview Audio")
        st.audio(st.session_state.audio_bytes, format="audio/mp3")
        st.download_button(
            "⬇️ Download Voiceover (MP3)",
            data=st.session_state.audio_bytes,
            file_name=st.session_state.audio_filename,
            mime="audio/mpeg",
            use_container_width=True,
        )


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()
st.caption(
    "AI Creator Studio v0.4 • Gemini Script Generator • Edge TTS • ElevenLabs"
)
