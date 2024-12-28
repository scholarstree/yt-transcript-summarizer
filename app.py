import streamlit as st
from jinja2 import Environment, FileSystemLoader
from utils.utils import *
import logging

# Set up Jinja environment
env = Environment(loader=FileSystemLoader("templates"))

# Sidebar for configuration
st.sidebar.title("Configuration")
api_key = st.sidebar.text_input("Enter API Key", type="password")
model_name = st.sidebar.selectbox("Select Model", ["gemini-1.5-flash"], disabled=True)

# Load default prompt template
default_template_path = "summarization_prompt.jinja"
default_prompt_template = ""
try:
    with open(f"templates/{default_template_path}", "r") as template_file:
        default_prompt_template = template_file.read()
except FileNotFoundError:
    st.sidebar.error("⛔ Default template file not found!")

# Allow user to customize prompt template
# Expander for prompt customization
with st.sidebar.expander("Prompt Template", expanded=False):
    custom_prompt_template = st.text_area(
        "Edit Prompt Template", 
        default_prompt_template, 
        height=500
    )

# Initialize the model
model = None
if api_key:
    try:
        model = configure_gemini_api(api_key, model_name)
    except ValueError as e:
        st.sidebar.error(f"⛔ {str(e)}")
else:
    st.sidebar.error("⛔ Please enter a valid API key.")

# Streamlit App
st.title("📸 YouTube Transcript Summarizer")

# Main layout for URL input and process
video_url = st.text_input("Enter YouTube Video URL", "")

# Process when the button is clicked
if st.button("Summarize Transcript"):
    with st.expander("Logs", expanded=False):
        if not video_url:
            st.error("⛔ Please enter a valid YouTube video URL.")
        else:
            st.write("🔄 Extracting metadata...")

            # Extract metadata
            metadata = extract_youtube_metadata(video_url)
            if metadata:
                st.success("✅ Metadata extracted successfully!")
                st.text_area("Metadata", value=str(metadata), height=150)
                st.write("🔄 Fetching transcripts...")
                all_transcripts = fetch_all_transcripts(video_url, formatter_type="text")

                if all_transcripts:
                    # Sort transcripts by preference
                    sorted_transcripts = sort_transcripts(all_transcripts, preferred_languages=["en"])
                    if sorted_transcripts:
                        lang = list(sorted_transcripts.keys())[0]
                        transcript = sorted_transcripts[lang]
                        st.success(f"✅ Transcript fetched in language: {lang}")
                        st.text_area("Transcript", value=transcript, height=150)
                        
                        # Load and customize Jinja template
                        template = env.from_string(custom_prompt_template)
                        summarization_prompt = template.render(
                            title=metadata["title"],
                            uploader=metadata["uploader"],
                            upload_date=metadata["upload_date"],
                            duration=metadata["duration"],
                            description=metadata["description"],
                            lang=lang,
                            transcript=transcript,
                        )
                        st.write("🛠️ Creating summarization prompt...")
                        st.success("✅ Summarization prompt created successfully!")
                        st.text_area("Summarization Prompt", value=summarization_prompt, height=300)

                    else:
                        st.error("⛔ Failed to sort transcripts.")
                else:
                    st.error("⛔ Failed to fetch transcripts.")
            else:
                st.error("⛔ Failed to extract metadata.")
            st.write("🔄 Generating summary...")
        try:
            summary = generate_summary_gemini(model, summarization_prompt)
            st.success("✅ Summary generated successfully!")
            st.text_area("Summary", value=summary, height=300)
        except Exception as e:
            st.error(f"⛔ Failed to generate summary: {str(e)}")
    
    # Render the summary using Markdown
    st.markdown(summary, unsafe_allow_html=True)
