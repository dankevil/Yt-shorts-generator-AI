"""
YouTube Shorts Generator - Streamlit Frontend
"""

import os
import time
import json
import random
import string
import logging
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import math
from moviepy.editor import VideoFileClip
from moviepy.editor import vfx
import platform

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ytauto-app')

# Import backend functionality
from src.content_generator import generate_content, CONTENT_STYLES
from src.text_to_speech import convert_text_to_speech
from src.video_generator import create_video, list_available_templates
from src.captions_generator import create_captions
from src.video_editor import create_final_video, VISUAL_THEMES
from src.performance_config import get_performance_config, init_performance_settings

# Load environment variables
load_dotenv()

# Initialize performance settings
init_performance_settings()
perf_config = get_performance_config()

# Constants
APP_VERSION = "1.1.0"
ANALYTICS_FILE = "resources/analytics.json"
LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "zh-CN": "Chinese (Simplified)",
    "ar": "Arabic",
    "hi": "Hindi",
    "ko": "Korean"
}


# Page configuration
st.set_page_config(
    page_title="YouTube Shorts Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with improved design
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        color: #FF0000;
        text-align: center;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .sub-header {
        font-size: 1.8rem;
        margin-bottom: 1.2rem;
        color: #333;
        border-bottom: 2px solid #FF0000;
        padding-bottom: 0.5rem;
    }
    .output-video {
        width: 100%;
        max-width: 405px;
        margin: 0 auto;
        display: block;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .stProgress > div > div > div > div {
        background-color: #FF0000;
    }
    .stats-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .stats-number {
        font-size: 2rem;
        font-weight: bold;
        color: #FF0000;
    }
    .stButton button {
        background-color: #FF0000;
        color: white;
        border-radius: 5px;
    }
    .stButton button:hover {
        background-color: #CC0000;
    }
    .footer {
        text-align: center;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #ddd;
        color: #666;
        font-size: 0.8rem;
    }
    /* Responsive improvements */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
        }
        .sub-header {
            font-size: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'generation_history' not in st.session_state:
        st.session_state.generation_history = []
    if 'theme_preview' not in st.session_state:
        st.session_state.theme_preview = {}
    if 'analytics_data' not in st.session_state:
        st.session_state.analytics_data = load_analytics_data()
    if 'page' not in st.session_state:
        st.session_state.page = "generate"


def load_analytics_data():
    """Load analytics data from file or initialize new data"""
    if os.path.exists(ANALYTICS_FILE):
        try:
            with open(ANALYTICS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    
    # Initial analytics structure
    return {
        "total_videos": 0,
        "total_duration": 0,
        "by_theme": {},
        "by_style": {},
        "by_language": {},
        "history": []
    }


def update_analytics(video_data):
    """Update analytics with new video generation data"""
    analytics = st.session_state.analytics_data
    
    # Update counters
    analytics["total_videos"] += 1
    analytics["total_duration"] += video_data.get("duration", 0)
    
    # Update theme stats
    theme = video_data.get("theme", "default")
    analytics["by_theme"][theme] = analytics["by_theme"].get(theme, 0) + 1
    
    # Update style stats
    style = video_data.get("style", "educational")
    analytics["by_style"][style] = analytics["by_style"].get(style, 0) + 1
    
    # Update language stats
    language = video_data.get("language", "en")
    analytics["by_language"][language] = analytics["by_language"].get(language, 0) + 1
    
    # Add to history
    video_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    analytics["history"].append(video_data)
    
    # Save updated analytics
    os.makedirs(os.path.dirname(ANALYTICS_FILE), exist_ok=True)
    with open(ANALYTICS_FILE, 'w') as f:
        json.dump(analytics, f, indent=2)
    
    # Update session state
    st.session_state.analytics_data = analytics


# App Header
def render_header():
    """Render the app header"""
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("<h1 class='main-header'>YouTube Shorts Generator</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 1.2rem;'>Create engaging YouTube shorts in minutes from a simple idea</p>", unsafe_allow_html=True)


# Sidebar configuration
def render_sidebar():
    """Render the sidebar with configuration options"""
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/YouTube_play_button_icon_%282013-2017%29.svg/1280px-YouTube_play_button_icon_%282013-2017%29.svg.png", width=60)
        st.header("Configuration")
        
        # Navigation
        st.subheader("Navigation")
        if st.button("🛠️ Generator", use_container_width=True):
            st.session_state.page = "generate"
        if st.button("🎬 My Videos", use_container_width=True):
            st.session_state.page = "videos"
        if st.button("📊 Analytics", use_container_width=True):
            st.session_state.page = "analytics"
        if st.button("🎨 Template Editor", use_container_width=True):
            st.session_state.page = "template_editor"
        if st.button("❓ Help", use_container_width=True):
            st.session_state.page = "help"
            
        st.markdown("---")
        
        # API Key Configuration
        api_key = st.text_input("OpenAI API Key", 
                               value=os.getenv("OPENAI_API_KEY", ""),
                               type="password",
                               help="Enter your OpenAI API key for content generation")
        
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            st.success("API Key set!")
        else:
            st.warning("Please enter your OpenAI API key")
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown(f"""
        This app automatically generates YouTube Shorts based on your idea.
        
        Version: {APP_VERSION}
        
        Features:
        - AI-powered script generation
        - Multiple content styles
        - Visual themes & effects
        - Background music support
        - Multiple language support
        - Analytics & history tracking
        """)
        
        # Footer
        st.markdown("---")
        st.markdown("<div class='footer'>© 2025 YouTube Shorts Generator</div>", unsafe_allow_html=True)


# Generator page
def render_generator_page():
    """Render the main generator page"""
    # Add global perf_config reference
    global perf_config
    
    st.markdown("<h2 class='sub-header'>Generate New Video</h2>", unsafe_allow_html=True)
    
    # Add tabs for single video creation and batch processing
    tab1, tab2 = st.tabs(["Single Video", "Batch Processing"])
    
    with tab1:
        # Create two columns for main settings and preview
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # Input for video idea
            idea = st.text_area("Enter your video idea", 
                               placeholder="Example: Amazing facts about space exploration",
                               help="Describe the topic or concept for your YouTube Short")
            
            # Content style selection
            style_options = list(CONTENT_STYLES.keys())
            content_style = st.selectbox(
                "Content Style",
                options=style_options,
                index=0,
                format_func=lambda x: x.replace('_', ' ').title(),
                help="Select the style of content for your video"
            )
            
            # Two columns for basic settings
            basic_col1, basic_col2 = st.columns(2)
            
            with basic_col1:
                # Video duration
                duration = st.slider("Video Duration (seconds)", 
                                   min_value=10, 
                                   max_value=60, 
                                   value=30,
                                   step=5,
                                   help="YouTube Shorts can be up to 60 seconds")
                
                # TTS language
                tts_language = st.selectbox(
                    "Voice Language", 
                    options=list(LANGUAGES.keys()),
                    index=0,
                    format_func=lambda x: LANGUAGES[x],
                    help="Select language for the voice narration"
                )
            
            with basic_col2:
                # Visual theme
                visual_theme = st.selectbox(
                    "Visual Theme",
                    options=list(VISUAL_THEMES.keys()),
                    index=0,
                    format_func=lambda x: x.replace('_', ' ').title(),
                    help="Select the visual style for your video"
                )
                
                # Background template selection
                template_options = list_available_templates()
                template_name = st.selectbox(
                    "Background Template",
                    options=template_options,
                    index=0,
                    format_func=lambda x: x.replace('_', ' ').title(),
                    help="Select a video template from the templates directory"
                )
            
            # Add max_words parameter back
            max_words = st.slider("Max Script Words", 
                                min_value=50, 
                                max_value=250, 
                                value=150,
                                help="Maximum number of words in the generated script")
            
            # Advanced options expander
            with st.expander("Advanced Options"):
                adv_col1, adv_col2 = st.columns(2)
                
                with adv_col1:
                    add_intro = st.checkbox("Add Intro Animation", 
                                         value=True,
                                         help="Add a short intro animation to your video")
                    
                    add_music = st.checkbox("Add Background Music", 
                                         value=True,
                                         help="Add background music to your video (requires music files in resources/music)")
                    
                    # GPU acceleration option
                    use_gpu = st.checkbox("Use GPU Acceleration", 
                                        value=True,
                                        help="Enable GPU acceleration for faster video processing (requires NVIDIA or AMD GPU)")
                    
                    # Display GPU info if available
                    if perf_config.gpu_info['available']:
                        st.caption(f"Detected GPU: {perf_config.gpu_info['model'] or perf_config.gpu_info['vendor'].upper()}")
                    else:
                        st.caption("No compatible GPU detected")
                
                with adv_col2:
                    # Add option for batch processing
                    use_batch_processing = st.checkbox("Enable Batch Processing", 
                                                    value=False,
                                                    help="Process multiple videos in parallel for faster results")
                    
                    if use_batch_processing:
                        batch_size = st.slider("Max Concurrent Jobs",
                                             min_value=2,
                                             max_value=8,
                                             value=4,
                                             help="Maximum number of videos to process simultaneously")
                    
                    # Show performance info option
                    show_perf_info = st.checkbox("Show Performance Info", 
                                              value=False,
                                              help="Display hardware utilization information during processing")
                
                # Store GPU acceleration and batch processing settings in session state
                if 'use_gpu' not in st.session_state:
                    st.session_state.use_gpu = use_gpu
                else:
                    st.session_state.use_gpu = use_gpu
                
                if 'use_batch_processing' not in st.session_state:
                    st.session_state.use_batch_processing = use_batch_processing
                else:
                    st.session_state.use_batch_processing = use_batch_processing
                
                if use_batch_processing and 'batch_size' not in st.session_state:
                    st.session_state.batch_size = batch_size
                elif use_batch_processing:
                    st.session_state.batch_size = batch_size
                
                if 'show_perf_info' not in st.session_state:
                    st.session_state.show_perf_info = show_perf_info
                else:
                    st.session_state.show_perf_info = show_perf_info
                
                # Display current hardware info if showing performance info
                if show_perf_info:
                    st.divider()
                    hardware_col1, hardware_col2 = st.columns(2)
                    
                    # Import performance config here to avoid circular imports
                    try:
                        from src.performance_config import get_performance_config
                        perf_config = get_performance_config()
                        
                        with hardware_col1:
                            st.write("**Hardware Configuration:**")
                            st.write(f"CPU Cores: {perf_config.num_cpu_cores}")
                            st.write(f"Optimal Threads: {perf_config.optimal_threads}")
                            
                        with hardware_col2:
                            st.write("**GPU Information:**")
                            if perf_config.gpu_info['available']:
                                st.write(f"GPU: {perf_config.gpu_info['model'] or perf_config.gpu_info['vendor'].upper()}")
                                st.write(f"Video Codec: {perf_config.codec}")
                                st.write(f"CUDA Available: {perf_config.has_cuda}")
                            else:
                                st.write("No compatible GPU detected")
                                st.write("Using CPU for video processing")
                    except ImportError:
                        st.write("Unable to load performance information")
        
        with col2:
            # Theme preview
            st.markdown("<h3 style='text-align:center; margin-bottom:1rem;'>Theme Preview</h3>", unsafe_allow_html=True)
            
            # Show sample based on selected theme
            theme_image_placeholder = st.empty()
            theme_desc_placeholder = st.empty()
            
            # Show theme preview (simulated)
            theme_descriptions = {
                "default": "Clean and simple design with white text on semi-transparent black background.",
                "modern": "Sleek blue accents with smooth fade-in animations.",
                "minimalist": "Pure text without backgrounds for a clean, distraction-free look.",
                "dramatic": "Bold Impact font with golden text on dark background and subtle zoom effect.",
                "retro": "Vintage style with sepia tones and old-school typewriter font."
            }
            
            theme_image_placeholder.image(f"https://via.placeholder.com/400x600?text={visual_theme.title()}+Theme", 
                             use_column_width=True,
                             caption="Sample visual style")
            
            theme_desc_placeholder.info(theme_descriptions.get(visual_theme, "Select a theme to see its description"))
        
    # Generate button
    generate_button = st.button("💫 Generate YouTube Short", type="primary", use_container_width=True)
    
    if generate_button and idea:
        if not os.getenv("OPENAI_API_KEY"):
            st.error("⚠️ Please enter your OpenAI API key in the sidebar.")
        else:
            # Create progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Create directories if they don't exist
                os.makedirs("output", exist_ok=True)
                os.makedirs("resources", exist_ok=True)
                os.makedirs("resources/temp", exist_ok=True)
                os.makedirs("resources/music", exist_ok=True)
                
                # Generate unique timestamp for this run
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                output_base = f"output/short_{timestamp}"
                
                # Step 1: Generate content
                status_text.text("Generating script and title...")
                progress_text = st.empty()
                progress_text.text("Generating content...")
                script, title, hook = generate_content(
                    idea, 
                    max_words=max_words,
                    style=content_style
                )
                progress_bar.progress(20)
                
                # Show generated content
                st.subheader("Generated Content")
                st.markdown(f"**Title:** {title}")
                if hook:
                    st.markdown(f"**Hook:** {hook}")
                st.markdown(f"**Script:**\n{script}")
                
                # Step 2: Convert text to speech
                status_text.text("Converting text to speech...")
                audio_file = convert_text_to_speech(script, f"{output_base}_audio.mp3", language=tts_language)
                progress_bar.progress(40)
                
                # Display audio
                st.audio(audio_file)
                
                # Step 3: Generate background video
                status_text.text("Creating background video...")
                
                if enable_custom_bg and 'bg_file' in locals() and bg_file:
                    # Save uploaded background video
                    temp_bg_path = f"resources/temp/uploaded_bg_{timestamp}.mp4"
                    with open(temp_bg_path, "wb") as f:
                        f.write(bg_file.getbuffer())
                    
                    # Process the uploaded background
                    background_video = temp_bg_path
                    output_bg = f"{output_base}_background.mp4"
                    from src.video_generator import process_background_video
                    process_background_video(background_video, output_bg, duration)
                    background_video = output_bg
                else:
                    # Generate background video
                    background_video = create_video(
                        f"{output_base}_background.mp4",
                        duration=int(duration),
                        template_name=template_name
                    )
                
                progress_bar.progress(60)
                
                # Step 4: Generate captions
                status_text.text("Creating captions...")
                captions_file = create_captions(script, audio_file)
                progress_bar.progress(80)
                
                # Step 5: Create final video
                status_text.text("Finalizing video...")
                
                # Set environment variables for GPU based on user selection
                if 'use_gpu' in st.session_state:
                    if st.session_state.use_gpu:
                        os.environ['CUDA_VISIBLE_DEVICES'] = '0'
                        os.environ['CPU_ONLY'] = '0'
                    else:
                        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
                        os.environ['CPU_ONLY'] = '1'
                
                # Show performance monitoring if requested
                if 'show_perf_info' in st.session_state and st.session_state.show_perf_info:
                    try:
                        perf_col1, perf_col2 = st.columns(2)
                        with perf_col1:
                            st.markdown("**Processing with:**")
                            from src.performance_config import get_performance_config
                            perf_config = get_performance_config()
                            if perf_config.gpu_info['available'] and st.session_state.use_gpu:
                                st.markdown(f"🚀 **GPU**: {perf_config.gpu_info['model'] or perf_config.gpu_info['vendor'].upper()}")
                                st.markdown(f"🎬 **Codec**: {perf_config.codec}")
                                st.markdown(f"⚙️ **Threads**: {perf_config.optimal_threads}")
                            else:
                                st.markdown("💻 **CPU processing**")
                                st.markdown(f"⚙️ **Threads**: {perf_config.optimal_threads}")
                        
                        # Add placeholder for timing information
                        with perf_col2:
                            st.markdown("**Performance Metrics:**")
                            time_placeholder = st.empty()
                            fps_placeholder = st.empty()
                            
                            # Start timing
                            perf_start_time = time.time()
                    except Exception as e:
                        st.warning(f"Could not initialize performance monitoring: {str(e)}")
                
                # Use batch processing if selected
                if 'use_batch_processing' in st.session_state and st.session_state.use_batch_processing:
                    try:
                        # Import batch processor
                        from src.batch_processor import BatchProcessor, create_job
                        
                        # Create batch processor with user-defined batch size
                        batch_size = st.session_state.batch_size if 'batch_size' in st.session_state else 4
                        processor = BatchProcessor(max_workers=batch_size)
                        
                        # Create a single job
                        job = create_job(
                            background_video,
                            audio_file,
                            captions_file,
                            f"{output_base}_final.mp4",
                            job_id=timestamp,
                            theme=visual_theme,
                            add_music=add_music,
                            add_intro=add_intro,
                            add_outro=add_outro
                        )
                        
                        # Process the job (single job in batch mode for consistent API)
                        results = processor.process_batch([job], show_progress=False)
                        
                        # Get the result
                        if results and results[0]['status'] == 'success':
                            final_video = results[0]['result_file']
                            processing_time = results[0]['elapsed_time']
                            status_text.text(f"✅ Video generated in {processing_time:.2f} seconds using batch processing!")
                        else:
                            st.error(f"Error in batch processing: {results[0]['error'] if results else 'Unknown error'}")
                            raise Exception("Batch processing failed")
                    
                    except ImportError:
                        st.warning("Batch processing module not available. Falling back to standard processing.")
                        final_video = create_final_video(
                            background_video,
                            audio_file,
                            captions_file,
                            f"{output_base}_final.mp4",
                            theme=visual_theme,
                            add_music=add_music,
                            add_intro=add_intro,
                            add_outro=add_outro
                        )
                    except Exception as e:
                        st.error(f"Batch processing error: {str(e)}")
                        # Fallback to standard processing
                        final_video = create_final_video(
                            background_video,
                            audio_file,
                            captions_file,
                            f"{output_base}_final.mp4",
                            theme=visual_theme,
                            add_music=add_music,
                            add_intro=add_intro,
                            add_outro=add_outro
                        )
                else:
                    # Standard processing
                    final_video = create_final_video(
                        background_video,
                        audio_file,
                        captions_file,
                        f"{output_base}_final.mp4",
                        theme=visual_theme,
                        add_music=add_music,
                        add_intro=add_intro,
                        add_outro=add_outro
                    )
                
                progress_bar.progress(100)
                
                # Display success message and final video
                status_text.text("✅ YouTube Short successfully generated!")
                
                # Update performance metrics if enabled
                if 'show_perf_info' in st.session_state and st.session_state.show_perf_info and 'perf_start_time' in locals():
                    try:
                        # Calculate performance metrics
                        perf_end_time = time.time()
                        processing_time = perf_end_time - perf_start_time
                        
                        # Get video duration
                        video_clip = VideoFileClip(final_video)
                        video_duration = video_clip.duration
                        video_clip.close()
                        
                        # Calculate FPS and speedup factor
                        fps = video_duration / processing_time
                        
                        # Update the placeholders
                        time_placeholder.markdown(f"⏱️ **Processing time**: {processing_time:.2f} seconds")
                        fps_placeholder.markdown(f"⚡ **Processing speed**: {fps:.2f}x real-time")
                        
                        # Add additional metrics
                        st.markdown(f"Video duration: {video_duration:.2f} seconds")
                        st.markdown(f"Processing ratio: {processing_time/video_duration:.2f}x")
                    except Exception as e:
                        st.warning(f"Error calculating performance metrics: {str(e)}")
                
                # Show final video
                st.video(final_video)
                
                # Success message with download button
                st.success(f"Your YouTube Short '{title}' has been generated successfully!")
                
                with open(final_video, "rb") as file:
                    st.download_button(
                        label="⬇️ Download Video",
                        data=file,
                        file_name=f"youtube_short_{timestamp}.mp4",
                        mime="video/mp4"
                    )
                
                # Add to history
                video_data = {
                    "id": timestamp,
                    "title": title,
                    "idea": idea,
                    "style": content_style,
                    "theme": visual_theme,
                    "language": tts_language,
                    "duration": duration,
                    "file_path": final_video
                }
                
                st.session_state.generation_history.append(video_data)
                
                # Update analytics
                update_analytics(video_data)
                
            except Exception as e:
                st.error(f"Error generating video: {str(e)}")
                status_text.text("❌ Error occurred during generation")
    
    elif generate_button and not idea:
        st.warning("Please enter a video idea first.")

    with tab2:
        st.markdown("### Generate Videos in Batch from CSV")
        
        # Add help expander with instructions
        with st.expander("How to use batch processing"):
            st.markdown("""
            ## CSV Batch Processing Instructions
            
            1. **Download the template CSV** using the button below
            2. **Fill the CSV** with your video ideas following the format:
               - **topic**: Main idea for the video
               - **content_style**: Style of content (educational, listicle, etc.)
               - **duration**: Length in seconds (10-60)
               - **language**: Voice language code (en, es, fr, etc.)
               - **visual_theme**: Visual style (modern, minimal, vibrant, etc.)
               - **template_name**: Name of the template to use (without extension)
            3. **Upload your completed CSV** using the uploader below
            4. **Click "Generate Videos in Batch"** to process all videos
            
            The generated videos will be saved in the output directory and shown below after processing.
            """)
        
        # CSV upload
        st.markdown("#### Upload a CSV file with video ideas")
        csv_file = st.file_uploader("Upload CSV", type=["csv"], help="Upload a CSV file with video ideas")
        
        # Show template download link
        template_path = "templates/video_ideas_template.csv"
        if os.path.exists(template_path):
            with open(template_path, "rb") as file:
                st.download_button(
                    label="Download CSV Template",
                    data=file,
                    file_name="video_ideas_template.csv",
                    mime="text/csv",
                    help="Download a template CSV file to fill with your video ideas"
                )
        else:
            st.warning("CSV template file not found. Please run setup first.")
        
        # Process CSV if uploaded
        if csv_file is not None:
            try:
                # Read CSV
                df = pd.read_csv(csv_file)
                
                # Display CSV contents
                st.markdown("#### CSV Preview")
                st.dataframe(df)
                
                # Validate CSV format
                required_columns = ["topic", "content_style", "duration", "language", "visual_theme", "template_name"]
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    st.error(f"Missing required columns: {', '.join(missing_columns)}")
                else:
                    # Process videos
                    st.markdown("#### Generate Videos")
                    
                    # Settings for batch processing
                    st.markdown("Batch Processing Settings:")
                    output_dir = st.text_input("Output Directory", 
                                             value="output/batch",
                                             help="Directory where generated videos will be saved")
                    
                    # Create output directory if it doesn't exist
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # Add button to start batch processing
                    if st.button("Generate Videos in Batch"):
                        # Record start time
                        start_time = time.time()
                        
                        # Set environment variables for GPU based on user selection
                        if 'use_gpu' in st.session_state:
                            if st.session_state.use_gpu:
                                os.environ['CUDA_VISIBLE_DEVICES'] = '0'
                                os.environ['CPU_ONLY'] = '0'
                            else:
                                os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
                                os.environ['CPU_ONLY'] = '1'
                        
                        # Use true parallel batch processing if selected
                        if 'use_batch_processing' in st.session_state and st.session_state.use_batch_processing:
                            try:
                                # Import batch processor
                                from src.batch_processor import BatchProcessor, create_job
                                
                                # Create batch processor with user-defined batch size
                                batch_size = st.session_state.batch_size if 'batch_size' in st.session_state else 4
                                processor = BatchProcessor(max_workers=batch_size)
                                
                                st.info(f"Using parallel batch processing with {batch_size} concurrent jobs")
                                
                                # Create jobs for all rows in the CSV
                                jobs = []
                                for i, row in df.iterrows():
                                    # Create a unique name for the output file
                                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                                    video_id = f"{i+1}_{timestamp}"
                                    output_base = f"{output_dir}/video_{video_id}"
                                    
                                    # Generate content (needs to be done sequentially for each video)
                                    with st.spinner(f"Preparing content for video {i+1}/{len(df)}: {row['topic']}"):
                                        # Generate script and title
                                        script, title, hook = generate_content(
                                            row['topic'], 
                                            max_words=150,  # Use a fixed value for batch processing
                                            style=row['content_style']
                                        )
                                        
                                        # Generate audio
                                        audio_path = f"{output_base}_audio.mp3"
                                        convert_text_to_speech(script, audio_path, language=row['language'])
                                        
                                        # Generate background video
                                        background_path = f"{output_base}_background.mp4"
                                        create_video(
                                            background_path,
                                            duration=int(row['duration']),
                                            template_name=row['template_name']
                                        )
                                        
                                        # Generate captions
                                        captions_path = f"{output_base}_captions.json"
                                        create_captions(script, audio_path, captions_path)
                                        
                                        # Create job for final video
                                        job = create_job(
                                            background_path,
                                            audio_path,
                                            captions_path,
                                            f"{output_base}_final.mp4",
                                            job_id=f"video_{i+1}",
                                            theme=row['visual_theme'],
                                            add_music=True,
                                            add_intro=True,
                                            add_outro=True
                                        )
                                        jobs.append(job)
                                
                                # Process all jobs in parallel
                                progress_text = st.empty()
                                progress_text.text(f"Processing {len(jobs)} videos in parallel...")
                                
                                # Create a progress bar
                                batch_progress = st.progress(0)
                                
                                # Process the jobs
                                results = processor.process_batch(jobs, show_progress=False)
                                
                                # Update the progress bar to complete
                                batch_progress.progress(100)
                                
                                # Process results
                                successful_jobs = sum(1 for r in results if r['status'] == 'success')
                                failed_jobs = sum(1 for r in results if r['status'] == 'error')
                                
                                # Update analytics for successful jobs
                                for i, result in enumerate(results):
                                    if result['status'] == 'success':
                                        row = df.iloc[i]
                                        video_data = {
                                            "id": result['job_id'],
                                            "topic": row['topic'],
                                            "style": row['content_style'],
                                            "language": row['language'],
                                            "duration": int(row['duration']),
                                            "theme": row['visual_theme'],
                                            "timestamp": datetime.now().isoformat(),
                                            "path": result['result_file'],
                                            "processing_time": result['elapsed_time']
                                        }
                                        update_analytics(video_data)
                                
                                # Display completion message
                                end_time = time.time()
                                elapsed_time = end_time - start_time
                                st.success(f"Batch processing completed in {elapsed_time:.2f} seconds! {successful_jobs} videos succeeded, {failed_jobs} failed.")
                                
                                # Display video links for successful jobs
                                st.markdown("### Generated Videos")
                                st.markdown("The following videos have been generated:")
                                
                                for result in results:
                                    if result['status'] == 'success':
                                        st.video(result['result_file'])
                                
                            except ImportError as e:
                                st.warning(f"Parallel batch processing not available: {str(e)}. Falling back to sequential processing.")
                                # Fall back to traditional sequential processing
                                process_csv_sequentially(df, output_dir)
                            except Exception as e:
                                st.error(f"Error in parallel batch processing: {str(e)}")
                                # Fall back to traditional sequential processing
                                process_csv_sequentially(df, output_dir)
                        else:
                            # Traditional sequential processing
                            process_csv_sequentially(df, output_dir)
            
            except Exception as e:
                st.error(f"Error processing CSV: {str(e)}")


# Videos page (My Videos)
def render_videos_page():
    """Render the videos management page"""
    # Add global perf_config reference
    global perf_config
    
    st.markdown("<h2 class='sub-header'>Videos Management</h2>", unsafe_allow_html=True)
    
    # Check for video files
    output_dir = Path("output")
    if output_dir.exists():
        video_files = list(output_dir.glob("*_final.mp4"))
        
        if video_files:
            # Show statistics
            total_videos = len(video_files)
            total_size_mb = sum(f.stat().st_size for f in video_files) / (1024 * 1024)
            
            stat1, stat2, stat3 = st.columns(3)
            with stat1:
                st.markdown(f"""
                <div class='stats-card'>
                    <div class='stats-number'>{total_videos}</div>
                    <div>Videos Generated</div>
                </div>
                """, unsafe_allow_html=True)
            
            with stat2:
                st.markdown(f"""
                <div class='stats-card'>
                    <div class='stats-number'>{total_size_mb:.1f} MB</div>
                    <div>Total Size</div>
                </div>
                """, unsafe_allow_html=True)
            
            with stat3:
                latest_date = max(f.stat().st_mtime for f in video_files)
                latest_date_str = datetime.fromtimestamp(latest_date).strftime("%Y-%m-%d")
                st.markdown(f"""
                <div class='stats-card'>
                    <div class='stats-number'>{latest_date_str}</div>
                    <div>Latest Video</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Search and filter
            search = st.text_input("Search videos by timestamp or ID", 
                                 placeholder="e.g., 20250301")
            
            # Filter videos
            filtered_videos = [v for v in video_files if search.lower() in v.stem.lower()] if search else video_files
            
            if filtered_videos:
                st.write(f"Showing {len(filtered_videos)} videos")
                
                # Create columns to display videos
                num_cols = 3
                videos_per_row = (len(filtered_videos) + num_cols - 1) // num_cols
                
                for row in range(videos_per_row):
                    cols = st.columns(num_cols)
                    for col_idx in range(num_cols):
                        video_idx = row * num_cols + col_idx
                        if video_idx < len(filtered_videos):
                            with cols[col_idx]:
                                video_file = filtered_videos[video_idx]
                                
                                # Get timestamp from filename
                                timestamp = video_file.stem.split("_")[1]
                                formatted_time = time.strftime(
                                    "%Y-%m-%d %H:%M:%S", 
                                    time.strptime(timestamp, "%Y%m%d_%H%M%S") if "_" in timestamp else time.localtime()
                                )
                                
                                # Display video with timestamp
                                st.video(str(video_file))
                                st.caption(f"Generated on {formatted_time}")
                                
                                # Download button
                                with open(str(video_file), "rb") as file:
                                    st.download_button(
                                        label="Download",
                                        data=file,
                                        file_name=f"youtube_short_{timestamp}.mp4",
                                        mime="video/mp4",
                                        key=f"download_{video_idx}"
                                    )
                                
                                # Delete button
                                if st.button("Delete", key=f"delete_{video_idx}"):
                                    try:
                                        video_file.unlink()
                                        st.success("Video deleted successfully!")
                                        st.experimental_rerun()
                                    except Exception as e:
                                        st.error(f"Error deleting video: {str(e)}")
            else:
                st.info("No videos match your search criteria")
        else:
            st.info("No generated videos found. Generate a video first!")
    else:
        st.info("Output directory doesn't exist yet. Generate a video first!")


# Analytics page
def render_analytics_page():
    """Render the analytics page"""
    # Add global perf_config reference
    global perf_config
    
    st.markdown("<h2 class='sub-header'>Analytics Dashboard</h2>", unsafe_allow_html=True)
    
    analytics = st.session_state.analytics_data
    
    if analytics["total_videos"] > 0:
        # Overview statistics
        stat1, stat2, stat3, stat4 = st.columns(4)
        
        with stat1:
            st.markdown(f"""
            <div class='stats-card'>
                <div class='stats-number'>{analytics["total_videos"]}</div>
                <div>Total Videos</div>
            </div>
            """, unsafe_allow_html=True)
        
        with stat2:
            avg_duration = analytics["total_duration"] / analytics["total_videos"] if analytics["total_videos"] > 0 else 0
            st.markdown(f"""
            <div class='stats-card'>
                <div class='stats-number'>{avg_duration:.1f}s</div>
                <div>Avg Duration</div>
            </div>
            """, unsafe_allow_html=True)
        
        with stat3:
            # Most used theme
            if analytics["by_theme"]:
                most_used_theme = max(analytics["by_theme"].items(), key=lambda x: x[1])[0]
                st.markdown(f"""
                <div class='stats-card'>
                    <div class='stats-number'>{most_used_theme.title()}</div>
                    <div>Top Theme</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class='stats-card'>
                    <div class='stats-number'>-</div>
                    <div>Top Theme</div>
                </div>
                """, unsafe_allow_html=True)
        
        with stat4:
            # Most used style
            if analytics["by_style"]:
                most_used_style = max(analytics["by_style"].items(), key=lambda x: x[1])[0]
                st.markdown(f"""
                <div class='stats-card'>
                    <div class='stats-number'>{most_used_style.title()}</div>
                    <div>Top Style</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class='stats-card'>
                    <div class='stats-number'>-</div>
                    <div>Top Style</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Charts
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Theme chart
            if analytics["by_theme"]:
                st.subheader("Videos by Theme")
                theme_df = pd.DataFrame({
                    'Theme': [k.title() for k in analytics["by_theme"].keys()],
                    'Count': list(analytics["by_theme"].values())
                })
                theme_chart = px.pie(theme_df, values='Count', names='Theme', hole=0.4)
                theme_chart.update_layout(height=400)
                st.plotly_chart(theme_chart, use_container_width=True)
        
        with chart_col2:
            # Style chart
            if analytics["by_style"]:
                st.subheader("Videos by Content Style")
                style_df = pd.DataFrame({
                    'Style': [k.title() for k in analytics["by_style"].keys()],
                    'Count': list(analytics["by_style"].values())
                })
                style_chart = px.bar(style_df, x='Style', y='Count', color='Style')
                style_chart.update_layout(height=400)
                st.plotly_chart(style_chart, use_container_width=True)
        
        # History table
        st.subheader("Generation History")
        if analytics["history"]:
            history_df = pd.DataFrame(analytics["history"])
            if not history_df.empty:
                # Clean up columns for display
                display_cols = ["timestamp", "title", "idea", "style", "theme", "language", "duration"]
                display_cols = [col for col in display_cols if col in history_df.columns]
                
                st.dataframe(
                    history_df[display_cols],
                    use_container_width=True,
                    column_config={
                        "timestamp": "Generated On",
                        "title": "Title",
                        "idea": "Idea",
                        "style": "Content Style",
                        "theme": "Visual Theme",
                        "language": "Language",
                        "duration": "Duration (s)"
                    }
                )
    else:
        st.info("No analytics data available yet. Generate some videos to see statistics!")


# Help page
def render_help_page():
    """Render the help page"""
    # Add global perf_config reference
    global perf_config
    
    st.markdown("<h2 class='sub-header'>Help & Documentation</h2>", unsafe_allow_html=True)
    
    # Create tabs for different help sections
    help_tab1, help_tab2, help_tab3, help_tab4 = st.tabs([
        "Getting Started", "Content Styles", "Visual Themes", "FAQ"
    ])
    
    with help_tab1:
        st.markdown("""
        ### Getting Started
        
        #### Step 1: Configure API
        1. Enter your OpenAI API key in the sidebar
        2. You need this for generating video content
        
        #### Step 2: Create Your First Short
        1. Navigate to the Generator page
        2. Enter your video idea in the text field
        3. Select your preferred content style and visual theme
        4. Click "Generate YouTube Short"
        5. Wait for processing - this may take a few minutes
        6. Preview your video and download it when ready
        
        #### Step 3: Customize Your Videos
        - Try different content styles, visual themes, and languages
        - Check the "Advanced Options" section for more customization
        - Upload custom background videos for unique shorts
        
        #### Step 4: Track and Analyze
        - View all your generated videos in the "My Videos" page
        - Check analytics and statistics in the "Analytics" page
        - Refine your approach based on what works best
        """)
    
    with help_tab2:
        st.markdown("""
        ### Content Styles
        
        Each style creates a different type of script:
        
        **Educational**
        - Informative and factual
        - Focuses on explaining concepts clearly
        - Includes interesting facts and details
        
        **Entertaining**
        - Fun, engaging, and sometimes humorous
        - Designed to capture attention and entertain
        - More casual tone
        
        **Storytelling**
        - Narrative format with beginning, middle, and end
        - Emotionally engaging content
        - Character or scenario focused
        
        **Tutorial**
        - Step-by-step instructions
        - Process or skill focused
        - Clear, actionable information
        
        **Fact List**
        - Collection of interesting facts
        - Bite-sized information
        - Focuses on surprising or lesser-known details
        
        **Motivational**
        - Inspirational tone
        - Encourages and uplifts the viewer
        - Often includes quotes or actionable advice
        """)
    
    with help_tab3:
        st.markdown("""
        ### Visual Themes
        
        The visual theme affects how your video looks:
        
        **Default**
        - Clean, simple design
        - White text on semi-transparent black background
        - Balanced and professional
        
        **Modern**
        - Sleek with blue accents
        - Smooth fade-in animations
        - Contemporary and clean
        
        **Minimalist**
        - Pure text without backgrounds
        - Distraction-free design
        - Focus on content only
        
        **Dramatic**
        - Bold Impact font
        - Golden text on dark backgrounds
        - Subtle zoom effects
        
        **Retro**
        - Vintage style with sepia tones
        - Typewriter-style font
        - Old-school aesthetic
        """)
    
    with help_tab4:
        st.markdown("""
        ### Frequently Asked Questions
        
        **Q: How long does it take to generate a video?**
        
        A: Generation typically takes 1-5 minutes depending on video length, complexity, and your computer's performance.
        
        **Q: What format are the videos saved in?**
        
        A: Videos are saved as MP4 files with H.264 encoding, compatible with all major platforms including YouTube.
        
        **Q: Do I need FFmpeg installed?**
        
        A: Yes, FFmpeg is required for video processing. Make sure it's installed and available in your system path.
        
        **Q: Can I use these videos commercially?**
        
        A: The videos you generate are yours to use. However, be mindful of copyright if you use custom background videos or music not included with the app.
        
        **Q: Where can I get background music?**
        
        A: Place MP3 or WAV files in the resources/music directory to use as background music. Make sure you have rights to use any music you add.
        
        **Q: How can I improve video quality?**
        
        A: For best quality:
        - Use high-resolution background videos (1080x1920)
        - Write clear, concise ideas
        - Select the appropriate content style for your topic
        - Use custom backgrounds for specific themes
        """)


def render_template_editor_page():
    """Render the video template editor page"""
    # Add global perf_config reference
    global perf_config
    
    # Helper functions for the template editor
    def get_video_info(video_path):
        """Get basic information about a video file"""
        clip = VideoFileClip(video_path)
        info = {
            "duration": clip.duration,
            "width": clip.size[0],
            "height": clip.size[1],
            "fps": clip.fps
        }
        clip.close()
        return info
    
    def process_video_template(input_path, output_path, start_time, end_time, crop_params, additional_params=None):
        """Process video template based on parameters"""
        try:
            # Load the video
            clip = VideoFileClip(input_path)
            
            # Cut the clip to the selected time segment
            clip = clip.subclip(start_time, end_time)
            
            # Apply cropping
            if "method" in crop_params:
                # Predefined crop methods
                method = crop_params["method"]
                w, h = clip.size
                
                if method == "center":
                    # Center crop to 9:16 aspect ratio
                    target_ratio = 9/16
                    current_ratio = w/h
                    
                    if current_ratio > target_ratio:
                        # Too wide, crop width
                        new_w = int(h * target_ratio)
                        x1 = (w - new_w) // 2
                        clip = clip.crop(x1=x1, width=new_w)
                    else:
                        # Too tall, crop height
                        new_h = int(w / target_ratio)
                        y1 = (h - new_h) // 2
                        clip = clip.crop(y1=y1, height=new_h)
                        
                elif method == "top":
                    new_h = int(w * 16/9)
                    clip = clip.crop(y1=0, height=min(new_h, h))
                    
                elif method == "bottom":
                    new_h = int(w * 16/9)
                    y1 = max(0, h - new_h)
                    clip = clip.crop(y1=y1, height=min(new_h, h))
                    
                elif method == "left":
                    new_w = int(h * 9/16)
                    clip = clip.crop(x1=0, width=min(new_w, w))
                    
                elif method == "right":
                    new_w = int(h * 9/16)
                    x1 = max(0, w - new_w)
                    clip = clip.crop(x1=x1, width=min(new_w, w))
            else:
                # Custom cropping
                w, h = clip.size
                top = int(h * crop_params["top"])
                bottom = int(h * crop_params["bottom"])
                left = int(w * crop_params["left"])
                right = int(w * crop_params["right"])
                
                # Calculate new dimensions
                new_h = h - top - bottom
                new_w = w - left - right
                
                # Apply crop if dimensions are valid
                if new_w > 0 and new_h > 0:
                    clip = clip.crop(x1=left, y1=top, width=new_w, height=new_h)
            
            # Apply additional processing
            if additional_params:
                # Resize to shorts format (9:16)
                if additional_params.get("resize_resolution", False):
                    clip = clip.resize(width=1080, height=1920)
                
                # Apply basic filters
                if additional_params.get("apply_filters", False):
                    # Apply GPU-accelerated effects if available
                    if st.session_state.get('template_editor_use_gpu', True) and perf_config.gpu_info['available']:
                        from src.video_editor import apply_gpu_effect
                        clip = apply_gpu_effect(clip, "colorx")
                    else:
                        # Standard effects without GPU
                        clip = clip.fx(vfx.lum_contrast, lum=1.2, contrast=1.1)
                
                # Loop to target duration
                if additional_params.get("loop_video", False):
                    target_duration = additional_params.get("target_duration", 15)
                    
                    if clip.duration < target_duration:
                        # Calculate number of loops needed
                        loops_needed = math.ceil(target_duration / clip.duration)
                        # Create a list of clip copies
                        clips = [clip] * loops_needed
                        # Concatenate clips
                        from moviepy.editor import concatenate_videoclips
                        clip = concatenate_videoclips(clips)
                        # Trim to exact target duration
                        clip = clip.subclip(0, target_duration)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Get codec and ffmpeg params based on GPU availability
            use_gpu = st.session_state.get('template_editor_use_gpu', True)
            if use_gpu and perf_config.gpu_info['available']:
                logger.info(f"Using GPU acceleration with {perf_config.gpu_info['vendor']} GPU")
                encoding_params = perf_config.get_moviepy_params()
            else:
                logger.info("Using CPU processing")
                encoding_params = {
                    'codec': 'libx264',
                    'audio_codec': 'aac',
                    'temp_audiofile': 'temp-audio.m4a',
                    'remove_temp': True,
                    'fps': 30
                }
            
            try:
                # Write the processed video
                clip.write_videofile(
                    output_path,
                    **encoding_params
                )
            except Exception as encoding_error:
                logger.warning(f"Error with selected encoder: {str(encoding_error)}. Falling back to CPU encoding.")
                # Fallback to CPU encoding if GPU encoding fails
                fallback_params = {
                    'codec': 'libx264',
                    'audio_codec': 'aac',
                    'temp_audiofile': 'temp-audio.m4a',
                    'remove_temp': True,
                    'fps': 30,
                    'preset': 'medium'
                }
                clip.write_videofile(
                    output_path,
                    **fallback_params
                )
            
            clip.close()
            return True
            
        except Exception as e:
            print(f"Error processing video: {str(e)}")
            raise e
    
    st.title("🎬 Video Template Editor")
    st.subheader("Create custom video templates for your shorts")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Video file uploader
        uploaded_video = st.file_uploader(
            "Upload Video", 
            type=["mp4", "mov", "avi"], 
            help="Upload a video file to create a template"
        )
        
        # Video preview and controls
        if uploaded_video is not None:
            # Save uploaded video to temp file
            temp_video_path = os.path.join("temp", "temp_upload.mp4")
            os.makedirs("temp", exist_ok=True)
            
            with open(temp_video_path, "wb") as f:
                f.write(uploaded_video.getbuffer())
            
            # Display video
            st.video(temp_video_path)
            
            # Video information
            video_info = get_video_info(temp_video_path)
            st.info(f"Duration: {video_info['duration']:.2f}s | Resolution: {video_info['width']}x{video_info['height']}")
        else:
            st.info("Upload a video to start editing")
    
    with col2:
        st.subheader("Editing Controls")
        
        template_name = st.text_input(
            "Template Name",
            value="custom_template",
            help="Enter a name for your template (no spaces or special characters)"
        )
        
        # Replace any spaces or special characters
        template_name = "".join(c if c.isalnum() or c == '_' else '_' for c in template_name)
        
        # Crop settings
        st.markdown("### Video Crop")
        crop_option = st.radio(
            "Crop Method",
            options=["Center", "Top", "Bottom", "Left", "Right", "Custom"],
            index=0
        )
        
        if crop_option == "Custom":
            st.markdown("#### Custom Crop Settings")
            # For simplicity, we'll use sliders to adjust crop percentage
            top_crop = st.slider("Crop from Top (%)", 0, 100, 0)
            bottom_crop = st.slider("Crop from Bottom (%)", 0, 100, 0)
            left_crop = st.slider("Crop from Left (%)", 0, 100, 0)
            right_crop = st.slider("Crop from Right (%)", 0, 100, 0)
        
        # Time segment settings
        st.markdown("### Time Settings")
        
        if uploaded_video is not None:
            max_duration = video_info['duration']
            start_time = st.slider("Start Time (seconds)", 0.0, max(0.1, max_duration-1), 0.0)
            end_time = st.slider("End Time (seconds)", min(start_time + 0.1, max_duration), max_duration, max_duration)
            
            st.info(f"Selected Duration: {end_time - start_time:.2f}s")
        else:
            st.slider("Start Time (seconds)", 0.0, 10.0, 0.0, disabled=True)
            st.slider("End Time (seconds)", 0.0, 10.0, 10.0, disabled=True)
            
        # Additional settings
        with st.expander("Advanced Settings"):
            col1, col2 = st.columns(2)
            
            with col1:
                resize_resolution = st.checkbox("Resize to Shorts Format (9:16)", value=True)
                apply_filters = st.checkbox("Apply Basic Enhancement (Brightness/Contrast)", value=False)
                
                # Add GPU acceleration option
                use_gpu = st.checkbox("Use GPU Acceleration", 
                                    value=True,
                                    help="Enable GPU acceleration for faster video processing (requires NVIDIA or AMD GPU)")
                
                # Display GPU info if available
                if perf_config.gpu_info['available']:
                    st.caption(f"Detected GPU: {perf_config.gpu_info['model'] or perf_config.gpu_info['vendor'].upper()}")
                else:
                    st.caption("No compatible GPU detected")
            
            with col2:
                loop_video = st.checkbox("Loop to Target Duration", value=False)
                
                if loop_video:
                    target_duration = st.slider("Target Duration (seconds)", 
                                              min_value=5, 
                                              max_value=60, 
                                              value=15)
            
            # Store GPU acceleration setting in session state
            if 'template_editor_use_gpu' not in st.session_state:
                st.session_state.template_editor_use_gpu = use_gpu
            else:
                st.session_state.template_editor_use_gpu = use_gpu
            
        # Process button
        if uploaded_video is not None:
            process_button = st.button("Process Template", type="primary", use_container_width=True)
            
            if process_button:
                with st.spinner("Processing video template..."):
                    try:
                        # Determine output path
                        output_path = os.path.join("templates", f"{template_name}.mp4")
                        
                        # Process the video based on settings
                        if crop_option == "Custom":
                            crop_params = {
                                "top": top_crop / 100,
                                "bottom": bottom_crop / 100,
                                "left": left_crop / 100,
                                "right": right_crop / 100
                            }
                        else:
                            crop_params = {"method": crop_option.lower()}
                        
                        # Additional parameters based on settings
                        additional_params = {
                            "resize_resolution": resize_resolution,
                            "apply_filters": apply_filters,
                            "loop_video": loop_video
                        }
                        
                        if loop_video:
                            additional_params["target_duration"] = target_duration
                        
                        # Call the process function
                        result = process_video_template(
                            temp_video_path,
                            output_path,
                            start_time,
                            end_time,
                            crop_params,
                            additional_params
                        )
                        
                        if result:
                            st.success(f"Template '{template_name}' created successfully!")
                            # Refresh template list
                            st.session_state.templates_refreshed = True
                    except Exception as e:
                        st.error(f"Error processing template: {str(e)}")
        else:
            st.button("Process Template", disabled=True, use_container_width=True)
    
    # List of existing templates
    st.markdown("---")
    st.subheader("Existing Templates")
    
    templates = list_available_templates()
    if templates:
        template_cols = st.columns(4)
        
        for i, template in enumerate(templates):
            with template_cols[i % 4]:
                st.markdown(f"**{template.replace('_', ' ').title()}**")
                
                # Try to find template thumbnail or video
                template_path = os.path.join("templates", f"{template}.mp4")
                if os.path.exists(template_path):
                    st.video(template_path, start_time=0)
                    
                    # Add delete button
                    if template != "default" and st.button(f"Delete {template}", key=f"del_{template}"):
                        try:
                            os.remove(template_path)
                            st.success(f"Template '{template}' deleted!")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error deleting template: {str(e)}")
    else:
        st.info("No templates found. Create your first template using the editor above.")


def process_csv_sequentially(df, output_dir):
    """Process CSV data sequentially (fallback method)
    
    Args:
        df (DataFrame): DataFrame containing video generation instructions
        output_dir (str): Directory to save output files
    """
    # Record start time
    start_time = time.time()
    
    # Process each row in the CSV
    for i, row in df.iterrows():
        with st.spinner(f"Generating video {i+1}/{len(df)}: {row['topic']}"):
            try:
                # Create a unique name for the output file
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                video_id = f"{i+1}_{timestamp}"
                output_base = f"{output_dir}/video_{video_id}"
                
                # Generate content
                progress_text = st.empty()
                progress_bar = st.progress(0)
                
                progress_text.text("Generating content...")
                script, title, hook = generate_content(
                    row['topic'], 
                    max_words=150,  # Use a fixed value for batch processing
                    style=row['content_style']
                )
                progress_bar.progress(20)
                
                # Generate audio
                progress_text.text("Generating audio...")
                audio_path = f"{output_base}_audio.mp3"
                convert_text_to_speech(script, audio_path, language=row['language'])
                progress_bar.progress(40)
                
                # Generate background video
                progress_text.text("Creating background video...")
                background_path = f"{output_base}_background.mp4"
                create_video(
                    background_path,
                    duration=int(row['duration']),
                    template_name=row['template_name']
                )
                progress_bar.progress(60)
                
                # Generate captions
                progress_text.text("Generating captions...")
                captions_path = f"{output_base}_captions.json"
                create_captions(script, audio_path, captions_path)
                progress_bar.progress(80)
                
                # Create final video
                progress_text.text("Creating final video...")
                output_path = f"{output_base}_final.mp4"
                final_video = create_final_video(
                    background_path,
                    audio_path,
                    captions_path,
                    output_path,
                    theme=row['visual_theme'],
                    add_music=True,
                    add_intro=True, 
                    add_outro=True
                )
                progress_bar.progress(100)
                
                # Update analytics
                video_data = {
                    "id": video_id,
                    "topic": row['topic'],
                    "style": row['content_style'],
                    "language": row['language'],
                    "duration": int(row['duration']),
                    "theme": row['visual_theme'],
                    "words": len(script.split()),
                    "template": row['template_name'],
                    "timestamp": datetime.now().isoformat(),
                    "path": output_path
                }
                update_analytics(video_data)
                
                # Success message
                progress_text.text(f"Video {i+1} completed: {row['topic']}")
                
            except Exception as e:
                st.error(f"Error generating video {i+1}: {str(e)}")
    
    # Display completion message
    end_time = time.time()
    elapsed_time = end_time - start_time
    st.success(f"Sequential batch processing completed in {elapsed_time:.2f} seconds!")
    
    # Display video links
    st.markdown("### Generated Videos")
    st.markdown("The following videos have been generated:")
    
    for file in os.listdir(output_dir):
        if file.endswith("_final.mp4"):
            video_path = os.path.join(output_dir, file)
            st.video(video_path)


# Main application
def main():
    """Main execution function"""
    # Initialize session state
    initialize_session_state()
    
    # Render header
    render_header()
    
    # Render sidebar
    render_sidebar()
    
    # Render appropriate page based on navigation state
    if st.session_state.page == "generate":
        render_generator_page()
    elif st.session_state.page == "videos":
        render_videos_page()
    elif st.session_state.page == "analytics":
        render_analytics_page()
    elif st.session_state.page == "help":
        render_help_page()
    elif st.session_state.page == "template_editor":
        render_template_editor_page()


if __name__ == "__main__":
    main() 