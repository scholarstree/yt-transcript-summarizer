import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter, JSONFormatter
import google.generativeai as genai

# API and Model Configuration
def configure_gemini_api(api_key, model_name="gemini-1.5-flash"):
    """
    Configures the GenAI API with the provided API key and model.
    
    Args:
        api_key (str): The API key for authentication.
        model_name (str): The name of the generative model. Default is "gemini-1.5-flash".
    
    Returns:
        object: The configured generative model instance.
    """
    if api_key:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(model_name)
    else:
        raise ValueError("API key is required.")

# Summarize using LLM
def generate_summary_gemini(model, summarization_prompt):
    """
    Generates a summary using the configured LLM model.
    
    Args:
        model (object): The configured generative model instance.
        summarization_prompt (str): The prompt to generate the summary.
    
    Returns:
        str: The generated summary text.
    """
    response = model.generate_content(summarization_prompt)
    return response.text


def extract_youtube_metadata(video_url):
    """
    Extract metadata from a YouTube video using yt_dlp.

    Args:
        video_url (str): The URL of the YouTube video.

    Returns:
        dict: A dictionary containing metadata such as title, description, views, like count, upload date, duration, uploader, and thumbnail URL.
    """
    ydl_opts = {
        'extractor_args': {'youtube': {'player_client': ['ios']}}
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        metadata = {
            "title": info.get("title"),
            "description": info.get("description"),
            "views": info.get("view_count"),
            "like_count": info.get("like_count"),
            "upload_date": info.get("upload_date"),
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "thumbnail": sorted(
                info.get("thumbnails", []),
                key=lambda x: x.get('preference', 0),
                reverse=True
            )[1 if len(info.get("thumbnails", [])) > 1 else 0].get("url") if info.get("thumbnails") else None
        }

        return metadata

    except yt_dlp.utils.DownloadError as e:
        print(f"Error downloading video metadata: {e}")
    except KeyError as e:
        print(f"Missing expected metadata field: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while extracting metadata: {e}")
    
    return None


def fetch_all_transcripts(video_url, formatter_type="text"):
    """
    Fetch all transcripts (manual and auto-generated) for a YouTube video.

    Parameters:
    - video_url (str): The URL of the YouTube video.
    - formatter_type (str): The type of formatter ("text" or "json").

    Returns:
    - dict: A dictionary of all transcripts with language codes as keys.
            Auto-generated transcripts are suffixed with '_auto'.
    """
    try:
        # Extract video ID
        video_id = video_url.split("v=")[1].split("&")[0]

        # Get all available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Choose formatter
        formatter = JSONFormatter() if formatter_type == "json" else TextFormatter()

        transcripts = {}
        for transcript in transcript_list:
            try:
                lang_code = transcript.language_code
                suffix = "_auto" if transcript.is_generated else ""
                fetched_transcript = transcript.fetch()
                formatted_transcript = formatter.format_transcript(fetched_transcript)
                transcripts[f"{lang_code}{suffix}"] = formatted_transcript
            except Exception as e:
                print(f"Error fetching transcript for {lang_code}{suffix}: {e}")

        return transcripts

    except YouTubeTranscriptApi.CouldNotRetrieveTranscript as e:
        print(f"Could not retrieve transcripts for the video: {e}")
    except YouTubeTranscriptApi.TranscriptsDisabled as e:
        print(f"Transcripts are disabled for this video: {e}")
    except IndexError:
        print("Invalid YouTube video URL format. Please check the URL.")
    except Exception as e:
        print(f"An unexpected error occurred while fetching transcripts: {e}")
    
    return None


def sort_transcripts(transcripts, preferred_languages=["en"]):
    """
    Sort transcripts based on language preferences.

    Parameters:
    - transcripts (dict): A dictionary of all transcripts with language codes as keys.
    - preferred_languages (list): List of preferred language codes in priority order.

    Returns:
    - dict: A sorted dictionary of transcripts.
    """
    try:
        sorted_transcripts = {}

        # Preferred manual and auto transcripts
        for lang in preferred_languages:
            if lang in transcripts:
                sorted_transcripts[lang] = transcripts.pop(lang)
            if f"{lang}_auto" in transcripts:
                sorted_transcripts[f"{lang}_auto"] = transcripts.pop(f"{lang}_auto")

        # Remaining manual and auto transcripts
        for lang_code, transcript in transcripts.items():
            sorted_transcripts[lang_code] = transcript

        return sorted_transcripts

    except Exception as e:
        print(f"An error occurred while sorting transcripts: {e}")
        return transcripts
