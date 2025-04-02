#!/usr/bin/env python
"""
YouTube Shorts Automated Generator
Main entry point for the application
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Local imports
from content_generator import generate_content
from text_to_speech import convert_text_to_speech
from video_generator import create_video
from captions_generator import create_captions
from video_editor import create_final_video

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def setup_directories():
    """Ensure all necessary directories exist."""
    os.makedirs("output", exist_ok=True)
    os.makedirs("resources", exist_ok=True)
    os.makedirs("resources/temp", exist_ok=True)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='YouTube Shorts Generator')
    parser.add_argument('--idea', type=str, help='Initial idea for the video')
    parser.add_argument('--duration', type=int, default=30, 
                      help='Duration of the video in seconds (max 60s for shorts)')
    return parser.parse_args()


def main():
    """Main execution function."""
    setup_directories()
    args = parse_arguments()
    
    # Get input idea
    idea = args.idea
    if not idea:
        idea = input("Enter an idea for your YouTube short: ")
    
    logger.info(f"Generating content for idea: {idea}")
    
    # Generate timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_base = f"output/short_{timestamp}"
    
    # Step 1: Generate content from idea
    script, title = generate_content(idea)
    logger.info(f"Generated script and title: {title}")
    
    # Step 2: Convert text to speech
    audio_file = convert_text_to_speech(script, f"{output_base}_audio.mp3")
    logger.info(f"Created audio file: {audio_file}")
    
    # Step 3: Generate or select background video
    background_video = create_video(f"{output_base}_background.mp4", args.duration)
    logger.info(f"Created background video: {background_video}")
    
    # Step 4: Generate captions
    captions_file = create_captions(script, audio_file)
    logger.info(f"Created captions file: {captions_file}")
    
    # Step 5: Edit final video with audio, background, and captions
    final_video = create_final_video(
        background_video, 
        audio_file, 
        captions_file, 
        f"{output_base}_final.mp4"
    )
    
    logger.info(f"Successfully created YouTube short: {final_video}")
    logger.info(f"Video title: {title}")
    
    return final_video


if __name__ == "__main__":
    try:
        output_file = main()
        print(f"\nSuccess! Your YouTube short has been created: {output_file}")
    except Exception as e:
        logger.error(f"Error generating YouTube short: {str(e)}")
        sys.exit(1) 