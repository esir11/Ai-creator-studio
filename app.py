import streamlit as st

st.set_page_config(
    page_title="AI Creator Studio",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 AI Creator Studio")
st.caption("Your Personal AI YouTube Automation Platform")

st.divider()

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

st.divider()

st.header("🚀 Content Generator")

if st.button("Generate Content"):

    selected_text = (
        content_language
        if text_language == "Same as Content Language"
        else text_language
    )

    st.success("Content settings created!")

    st.write("Target Negara:", country)
    st.write("Bahasa Konten:", content_language)
    st.write("Bahasa Teks:", selected_text)
    st.write("Kategori:", category)
    st.write("Format:", video_format)

    st.info(
        "AI production system will be connected "
        "in the next development stage."
    )

st.divider()

st.caption("AI Creator Studio | Version 0.1")
