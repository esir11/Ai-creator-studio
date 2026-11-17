import streamlit as st
from google import genai
from google.genai import types

# PAGE CONFIG
st.set_page_config(
    page_title="AI Creator Studio",
    page_icon="🎬",
    layout="wide"
)

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

languages = [
    "English",
    "Bahasa Indonesia",
    "Japanese",
    "German",
    "French",
    "Spanish",
    "Portuguese",
    "Arabic",
    "Korean",
    "Chinese"
]

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
    placeholder="Example: The mysterious hotel room  room 404"
)

generate = st.button(
    "✨ Generate AI Script",
    type="primary",
    use_container_width=True
)

if generate:

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

VIDEO SETTINGS:

Target country: {country}
Content language: {content_language}
On-screen text language: {selected_text}
Category: {category}
Video format: {video_format}
Duration: {duration}
Topic: {topic}

INSTRUCTIONS:

1. Write the entire narration in {content_language}.
2. Make the content suitable for audiences in the target country.
3. Create a powerful opening hook.
4. Make the story engaging and maintain audience retention.
5. Divide the script into clear scenes.
6. Include visual suggestions for every scene.
7. Include on-screen subtitle suggestions in {selected_text}.
8. Add a natural ending and call to action.
9. Match the requested video duration.
10. Avoid unnecessary introductions.

For history and factual content, do not invent facts.
For fictional horror stories, create original fictional stories.

OUTPUT FORMAT:

TITLE:
Create an attractive YouTube title.

HOOK:
Write a powerful opening.

SCENE 1:
Narration:
Visual suggestion:
On-screen text:

SCENE 2:
Narration:
Visual suggestion:
On-screen text:

Continue scenes as needed.

ENDING:
Write the conclusion.

CALL TO ACTION:
Write a short audience engagement prompt.

YOUTUBE DESCRIPTION:
Write a suitable video description.

HASHTAGS:
Provide relevant hashtags.
"""

            with st.spinner(
                "AI is creating your script. Please wait..."
            ):

                response = client.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.8,
                        max_output_tokens=4096
                    )
                )

            if response.text:
                st.success("Your AI script has been generated!")

                st.markdown("## 📝 Generated Script")

                st.markdown(response.text)

                st.download_button(
                    label="📥 Download Script",
                    data=response.text,
                    file_name="ai_creator_script.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            else:
                st.error("AI returned an empty response. Please try again.")

        except KeyError:
            st.error(
                "Gemini API Key not found. "
                "Please check Streamlit Secrets."
            )

        except Exception as e:
            st.error(
                "Something went wrong while generating the script."
            )
            st.caption(str(e))

st.divider()

st.caption("AI Creator Studio | Version 0.2")
