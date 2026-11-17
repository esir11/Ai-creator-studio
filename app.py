import streamlit as st
from google import genai
from google.genai import types
import edge_tts
import asyncio
import tempfile
import os

# PAGE CONFIG
st.set_page_config(
    page_title="AI Creator Studio",
    page_icon="🎬",
    layout="wide"
)

# VOICE LIBRARY
VOICE_LIBRARY = {
    "English": {
        "🇺🇸 American": {
            "Female": ("Aria", "en-US-AriaNeural"),
            "Male": ("Guy", "en-US-GuyNeural")
        },
        "🇬🇧 British": {
            "Female": ("Sonia", "en-GB-SoniaNeural"),
            "Male": ("Ryan", "en-GB-RyanNeural")
        }
    },
    "Bahasa Indonesia": {
        "Default": {
            "Female": ("Gadis", "id-ID-GadisNeural"),
            "Male": ("Ardi", "id-ID-ArdiNeural")
        }
    },
    "Japanese": {
        "Default": {
            "Female": ("Nanami", "ja-JP-NanamiNeural"),
            "Male": ("Keita", "ja-JP-KeitaNeural")
        }
    },
    "German": {
        "Default": {
            "Female": ("Katja", "de-DE-KatjaNeural"),
            "Male": ("Conrad", "de-DE-ConradNeural")
        }
    },
    "French": {
        "Default": {
            "Female": ("Denise", "fr-FR-DeniseNeural"),
            "Male": ("Henri", "fr-FR-HenriNeural")
        }
    },
    "Spanish": {
        "Default": {
            "Female": ("Elvira", "es-ES-ElviraNeural"),
            "Male": ("Alvaro", "es-ES-AlvaroNeural")
        }
    },
    "Portuguese": {
        "Default": {
            "Female": ("Francisca", "pt-BR-FranciscaNeural"),
            "Male": ("Antonio", "pt-BR-AntonioNeural")
        }
    },
    "Arabic": {
        "Default": {
            "Female": ("Salma", "ar-EG-SalmaNeural"),
            "Male": ("Shakir", "ar-EG-ShakirNeural")
        }
    },
    "Korean": {
        "Default": {
            "Female": ("SunHi", "ko-KR-SunHiNeural"),
            "Male": ("InJoon", "ko-KR-InJoonNeural")
        }
    },
    "Chinese": {
        "Default": {
            "Female": ("Xiaoxiao", "zh-CN-XiaoxiaoNeural"),
            "Male": ("Yunxi", "zh-CN-YunxiNeural")
        }
    }
}

# SESSION STATE
if "generated_script" not in st.session_state:
    st.session_state.generated_script = ""

if "audio_data" not in st.session_state:
    st.session_state.audio_data = None

# HEADER
st.title("🎬 AI Creator Studio")
st.caption("Your Personal AI YouTube Automation Platform")
st.divider()

# CONTENT SETTINGS
st.header("🌎 Content Settings")

countries = [
    "🇺🇸 United States — Rank 1",
    "🇬🇧 United Kingdom — Rank 2",
    "🇮🇩 Indonesia",
    "🇯🇵 Japan",
    "🇩🇪 Germany",
    "🇫🇷 France",
    "🇪🇸 Spain",
    "🇧🇷 Brazil"
]

languages = list(VOICE_LIBRARY.keys())

country = st.selectbox(
    "Target Negara",
    countries,
    index=0
)

content_language = st.selectbox(
    "Bahasa Konten",
    languages,
    index=0
)

text_language = st.selectbox(
    "Bahasa Teks Dalam Video",
    ["Same as Content Language"] + languages,
    index=0
)

category = st.selectbox(
    "Kategori Konten",
    [
        "Horror Stories",
        "Amazing Facts",
        "History",
        "Mystery & Discovery"
    ]
)

video_format = st.radio(
    "Format Video",
    ["YouTube Shorts (9:16)", "Long Form (16:9)"]
)

if video_format == "YouTube Shorts (9:16)":
    duration = st.selectbox(
        "Video Duration",
        ["30 Seconds", "60 Seconds", "90 Seconds"]
    )
else:
    duration = st.selectbox(
        "Video Duration",
        ["5 Minutes", "8 Minutes", "10 Minutes", "15 Minutes"]
    )

st.divider()

# AI SCRIPT GENERATOR
st.header("🚀 AI Script Generator")

topic = st.text_input(
    "Enter Your Video Topic",
    placeholder="Example: The mysterious hotel room 404"
)

if st.button(
    "✨ Generate AI Script",
    type="primary",
    use_container_width=True
):
    if not topic.strip():
        st.warning("Please enter a video topic first.")

    else:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
            client = genai.Client(api_key=api_key)

            selected_text = (
                content_language
                if text_language == "Same as Content Language"
                else text_language
            )

            prompt = f"""
You are a professional YouTube scriptwriter.

Create an engaging and original YouTube video script.

Target country: {country}
Content language: {content_language}
On-screen text language: {selected_text}
Category: {category}
Video format: {video_format}
Duration: {duration}
Topic: {topic}

INSTRUCTIONS:
1. Write narration in {content_language}.
2. Make content suitable for the target country.
3. Create a powerful opening hook.
4. Maintain audience retention.
5. Divide the script into clear scenes.
6. Include visual suggestions.
7. Include on-screen text in {selected_text}.
8. Add an ending and call to action.
9. Match the requested duration.
10. Do not invent historical or factual claims.
11. Make fictional horror stories original.

IMPORTANT:
At the end, include a separate section named
VOICEOVER SCRIPT.

This section must contain ONLY spoken narration.
Do not include visual suggestions, scene directions,
headings, subtitles, hashtags or production notes
inside the VOICEOVER SCRIPT section.

OUTPUT:
TITLE:
HOOK:
SCENES:
ENDING:
CALL TO ACTION:
YOUTUBE DESCRIPTION:
HASHTAGS:
VOICEOVER SCRIPT:
"""

            with st.spinner("Gemini is writing your script..."):
                response = client.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.8,
                        max_output_tokens=4096
                    )
                )

            if response.text:
                st.session_state.generated_script = response.text
                st.session_state.audio_data = None
                st.success("AI script generated!")

        except KeyError:
            st.error("GEMINI_API_KEY is missing in Streamlit Secrets.")

        except Exception as e:
            st.error("Script generation failed.")
            st.caption(str(e))

# DISPLAY GENERATED SCRIPT
if st.session_state.generated_script:

    st.divider()
    st.header("📝 Generated Script")

    st.markdown(st.session_state.generated_script)

    st.download_button(
        "📥 Download Full Script",
        data=st.session_state.generated_script,
        file_name="ai_creator_script.txt",
        mime="text/plain"
    )

    # VOICE GENERATOR
    st.divider()
    st.header("🎙️ AI Voice Generator")

    st.caption(
        "Turn your AI script into natural-sounding narration."
    )

    voice_script = st.text_area(
        "Voiceover Text",
        value=st.session_state.generated_script,
        height=250,
        help="Edit this text to keep only the narration."
    )

    voice_settings = VOICE_LIBRARY[content_language]

    if content_language == "English":
        accent = st.selectbox(
            "Voice Accent",
            list(voice_settings.keys()),
            index=0
        )
    else:
        accent = "Default"

    gender = st.radio(
        "Voice Gender",
        ["Female", "Male"],
        horizontal=True
    )

    voice_name, voice_id = voice_settings[accent][gender]

    st.caption(f"Selected voice: {voice_name}")

    speed = st.slider(
        "Voice Speed",
        min_value=75,
        max_value=125,
        value=100,
        step=5,
        format="%d%%"
    )

    if st.button(
        "🎙️ Generate Voice MP3",
        type="primary",
        use_container_width=True
    ):

        if not voice_script.strip():
            st.warning("Please enter narration text.")

        else:
            try:
                async def create_voice():
                    communicate = edge_tts.Communicate(
                        voice_script,
                        voice_id,
                        rate=f"{speed - 100:+d}%"
                    )

                    with tempfile.NamedTemporaryFile(
                        suffix=".mp3",
                        delete=False
                    ) as audio_file:
                        audio_path = audio_file.name

                    try:
                        await communicate.save(audio_path)

                        with open(audio_path, "rb") as f:
                            return f.read()

                    finally:
                        if os.path.exists(audio_path):
                            os.remove(audio_path)

                with st.spinner(
                    "Creating your voice narration..."
                ):
                    st.session_state.audio_data = asyncio.run(
                        create_voice()
                    )

                st.success("Voice narration created successfully!")

            except Exception as e:
                st.session_state.audio_data = None
                st.error("Voice generation failed.")
                st.caption(str(e))

    if st.session_state.audio_data:
        st.subheader("🎧 Audio Preview")

        st.audio(
            st.session_state.audio_data,
            format="audio/mp3"
        )

        st.download_button(
            "📥 Download MP3",
            data=st.session_state.audio_data,
            file_name="ai_creator_voice.mp3",
            mime="audio/mpeg",
            use_container_width=True
        )

st.divider()
st.caption("AI Creator Studio | Version 0.3")
