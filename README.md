# YouTube Shorts Automated Generator

This Python application automates the creation of YouTube shorts from a simple input idea. It handles the entire process from content generation to video rendering with a modern web-based interface.

## Enhanced Features

- **AI-powered content generation** with multiple content styles:
  - Educational, entertaining, storytelling, tutorial, fact list, and motivational
- **Text-to-speech conversion** with 12+ language support
- **Background video selection/generation** with custom upload option
- **Caption generation and styling** with timing synchronization
- **Visual themes** for different looks and feels
- **Visual effects** including fades, zooms, and transitions
- **Intro and outro** with call-to-action overlays
- **Background music** support
- **Analytics dashboard** to track your video creation
- **Modern Streamlit web interface** for easy use

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
   Or on Windows, use the provided setup script:
   ```
   setup.bat
   ```
3. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ```
4. Ensure you have FFmpeg installed on your system

## Downloading Resources

The application works best with some background videos and music. You can download sample resources with the provided script:

```
python download_resources.py
```

Or use the `setup.bat` script on Windows which will offer to download resources automatically.

## Usage

### Streamlit Web Interface (Recommended)

Run the Streamlit app:

```
streamlit run app.py
```

Or on Windows:
```
run_app.bat
```

This will open a web interface where you can:
- Enter your video idea
- Choose from multiple content styles
- Select visual themes for your video
- Configure advanced options like intros, outros, and background music
- Generate videos with a single click
- View and download your generated shorts
- Track analytics on your video creation

### Command Line Interface

Run the main script:

```
python src/main.py --idea "Your video idea here"
```

Follow the prompts to enter your video idea and configure options.

## Directory Structure

- `src/`: Python source code for core functionality
- `output/`: Generated video files
- `resources/`: Background videos, audio files, and other assets
- `app.py`: Streamlit web interface
- `download_resources.py`: Utility to download sample resources
- `setup.bat`: Windows setup script

## Requirements

- Python 3.8+
- FFmpeg installed on your system
- OpenAI API key for content generation
- Streamlit for web interface

## GPU Acceleration

This project supports GPU acceleration for faster video processing. It automatically detects and uses:

- NVIDIA GPUs (via CUDA)
- AMD GPUs (via DirectX/AMF on Windows, VA-API on Linux)
- Intel GPUs (via QuickSync)
- Apple Silicon (via Metal/VideoToolbox)

For detailed information on setting up AMD GPU acceleration on Windows:

```
python -m src.check_gpu_acceleration    # Check if GPU acceleration is enabled
python -m src.setup_amd_acceleration    # Setup AMD GPU acceleration (run as administrator)
```

See [README_GPU_ACCELERATION.md](README_GPU_ACCELERATION.md) for detailed instructions.

## Customization

- Add your own background videos to the `resources/` directory
- Add background music to the `resources/music/` directory
- Modify the visual themes in `src/video_editor.py`
- Add new content styles in `src/content_generator.py`

## License

MIT 