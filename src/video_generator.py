"""
Video Generator Module
Creates or selects background videos for YouTube shorts
"""

import os
import random
import logging
import requests
from PIL import Image
from moviepy.editor import VideoFileClip, ImageClip, ColorClip

# Configure logging
logger = logging.getLogger(__name__)

# Default video dimensions for YouTube shorts (9:16 ratio)
DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1920


def create_video(output_file, duration=30, template_name=None):
    """
    Create or select a background video
    
    Args:
        output_file (str): Path to save the output video
        duration (int): Duration of the video in seconds
        template_name (str, optional): Name of the template to use
        
    Returns:
        str: Path to the created video file
    """
    try:
        logger.info(f"Creating background video for {duration} seconds")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # First try to use a template if specified
        if template_name and template_name != "default":
            template_video = find_template_video(template_name)
            if template_video:
                logger.info(f"Using template video: {template_video}")
                process_background_video(template_video, output_file, duration)
                return output_file
        
        # If no template specified or not found, try to find an existing video in resources directory
        background_video = find_background_video(duration)
        
        if background_video:
            logger.info(f"Using existing background video: {background_video}")
            # Resize and crop video to fit YouTube shorts format
            process_background_video(background_video, output_file, duration)
        else:
            logger.info("No suitable background video found, creating a solid color video")
            # Create a solid color background video
            create_color_video(output_file, duration)
        
        logger.info(f"Background video created: {output_file}")
        return output_file
        
    except Exception as e:
        logger.error(f"Error creating background video: {str(e)}")
        # Create a fallback color video
        create_color_video(output_file, duration)
        return output_file


def find_template_video(template_name):
    """
    Find a template video by name
    
    Args:
        template_name (str): Name of the template to find
        
    Returns:
        str or None: Path to the template video if found, None otherwise
    """
    templates_dir = "templates"
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir, exist_ok=True)
        return None
    
    # Check for exact match with .mp4 extension
    template_path = os.path.join(templates_dir, f"{template_name}.mp4")
    if os.path.exists(template_path):
        return template_path
    
    # Check for any file starting with the template name
    for file in os.listdir(templates_dir):
        if file.lower().startswith(template_name.lower()) and file.lower().endswith(('.mp4', '.mov')):
            return os.path.join(templates_dir, file)
    
    return None


def list_available_templates():
    """
    List all available template videos
    
    Returns:
        list: List of template names without extensions
    """
    templates_dir = "templates"
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir, exist_ok=True)
        return ["default"]
    
    templates = ["default"]  # Always include default option
    
    for file in os.listdir(templates_dir):
        if file.lower().endswith(('.mp4', '.mov')):
            # Add template name without extension
            template_name = os.path.splitext(file)[0]
            templates.append(template_name)
    
    return templates


def find_background_video(min_duration):
    """
    Find a suitable background video in resources directory
    
    Args:
        min_duration (int): Minimum duration required
        
    Returns:
        str or None: Path to a suitable video, or None if not found
    """
    resources_dir = "resources"
    video_extensions = ['.mp4', '.mov', '.avi']
    
    if not os.path.exists(resources_dir):
        return None
    
    video_files = []
    for root, _, files in os.walk(resources_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in video_extensions):
                video_files.append(os.path.join(root, file))
    
    # Check video durations
    suitable_videos = []
    for video_file in video_files:
        try:
            with VideoFileClip(video_file) as clip:
                if clip.duration >= min_duration:
                    suitable_videos.append(video_file)
        except Exception:
            continue
    
    if suitable_videos:
        return random.choice(suitable_videos)
    
    return None


def process_background_video(input_file, output_file, target_duration):
    """
    Process an existing video to fit YouTube shorts format
    
    Args:
        input_file (str): Path to input video
        output_file (str): Path to save processed video
        target_duration (int): Target duration in seconds
    """
    try:
        with VideoFileClip(input_file) as clip:
            # Calculate aspect ratio
            current_ratio = clip.w / clip.h
            target_ratio = DEFAULT_WIDTH / DEFAULT_HEIGHT
            
            # Resize and crop to fit 9:16 ratio
            if current_ratio > target_ratio:  # Too wide
                new_width = clip.h * target_ratio
                x1 = (clip.w - new_width) / 2
                cropped_clip = clip.crop(x1=x1, width=new_width)
            else:  # Too tall
                new_height = clip.w / target_ratio
                y1 = (clip.h - new_height) / 2
                cropped_clip = clip.crop(y1=y1, height=new_height)
            
            # Resize to standard dimensions
            resized_clip = cropped_clip.resize(width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT)
            
            # Trim to target duration (loop if too short)
            if resized_clip.duration >= target_duration:
                final_clip = resized_clip.subclip(0, target_duration)
            else:
                # Loop video to reach target duration
                n_loops = int(target_duration / resized_clip.duration) + 1
                final_clip = resized_clip.loop(n=n_loops).subclip(0, target_duration)
            
            # Write to file
            final_clip.write_videofile(output_file, codec="libx264", audio=False)
    
    except Exception as e:
        logger.error(f"Error processing background video: {str(e)}")
        create_color_video(output_file, target_duration)


def create_color_video(output_file, duration, color=(25, 25, 35)):
    """
    Create a solid color background video
    
    Args:
        output_file (str): Path to save the video
        duration (int): Duration in seconds
        color (tuple): RGB color tuple
    """
    try:
        # Create a solid color clip
        clip = ColorClip(size=(DEFAULT_WIDTH, DEFAULT_HEIGHT), color=color, duration=duration)
        
        # Write to file
        clip.write_videofile(output_file, codec="libx264", fps=30, audio=False)
    
    except Exception as e:
        logger.error(f"Error creating color video: {str(e)}")
        raise


if __name__ == "__main__":
    # Simple test
    output_path = "output/test_background.mp4"
    create_video(output_path, 15) 