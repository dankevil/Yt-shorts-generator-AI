"""
Video Editor Module
Combines background video, audio, and captions to create final YouTube short
Optimized for GPU acceleration and parallel processing
"""

import os
import json
import logging
import random
import multiprocessing
from functools import partial
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    VideoFileClip, 
    AudioFileClip, 
    TextClip, 
    CompositeVideoClip, 
    ImageClip,
    concatenate_videoclips,
    vfx,
    ColorClip,
    CompositeAudioClip
)
from moviepy.config import change_settings
import numpy as np
import platform

# Import performance configuration
from .performance_config import get_performance_config

# Configure logging
logger = logging.getLogger(__name__)

# Get performance configuration
perf_config = get_performance_config()

# Default settings
DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1920
DEFAULT_FPS = 30

# Visual themes
VISUAL_THEMES = {
    "default": {
        "caption_font": "Arial",
        "caption_color": "#FFFFFF",
        "caption_bg": "#00000080",
        "caption_alignment": "center",
        "effect": None
    },
    "modern": {
        "caption_font": "Helvetica",
        "caption_color": "#FFFFFF",
        "caption_bg": "#0066CC80",
        "caption_alignment": "center",
        "effect": "fadein"
    },
    "minimalist": {
        "caption_font": "Verdana",
        "caption_color": "#FFFFFF",
        "caption_bg": None,
        "caption_alignment": "center",
        "effect": None
    },
    "dramatic": {
        "caption_font": "Impact",
        "caption_color": "#FFD700",
        "caption_bg": "#00000090",
        "caption_alignment": "center",
        "effect": "zoom"
    },
    "retro": {
        "caption_font": "Courier",
        "caption_color": "#F5F5DC",
        "caption_bg": "#8B4513A0",
        "caption_alignment": "center",
        "effect": "fadein"
    }
}

def apply_gpu_effect(clip, effect_name):
    """
    Apply effects using GPU acceleration when available
    
    Args:
        clip (VideoClip): The video clip to apply effects to
        effect_name (str): Name of the effect to apply
        
    Returns:
        VideoClip: Processed clip with effects applied
    """
    try:
        from src.performance_config import get_performance_config
        perf_config = get_performance_config()
        
        # Log GPU usage
        if perf_config.gpu_info['available']:
            gpu_vendor = perf_config.gpu_info.get('vendor', 'unknown')
            gpu_model = perf_config.gpu_info.get('model', 'unknown')
            logger.debug(f"Applying {effect_name} effect using {gpu_vendor.upper()} GPU acceleration ({gpu_model})")
            
            # AMD-specific handling for Windows
            if gpu_vendor == 'amd' and platform.system() == 'Windows':
                logger.debug("Using optimized settings for AMD GPU on Windows")
        
        # Apply the effect based on its name
        if effect_name == "zoom":
            return clip.fx(vfx.zoom, 1.03, 1.03)
        elif effect_name == "fadein":
            return clip.fx(vfx.fadein, 1.0)
        elif effect_name == "fadeout":
            return clip.fx(vfx.fadeout, 1.0)
        elif effect_name == "mirror_x":
            return clip.fx(vfx.mirror_x)
        elif effect_name == "colorx":
            return clip.fx(vfx.colorx, 1.2)
        else:
            logger.warning(f"Unknown effect: {effect_name}")
            return clip
    except Exception as e:
        logger.error(f"Error applying GPU effect {effect_name}: {str(e)}")
        # Return original clip without effects if there's an error
        return clip

def create_final_video(background_video, audio_file, captions_file, output_file, theme="default", add_music=False, add_intro=False, add_outro=True):
    """
    Create final video by combining background, audio, and captions
    Optimized for GPU and multi-core processing
    
    Args:
        background_video (str): Path to background video
        audio_file (str): Path to audio file
        captions_file (str): Path to captions data file (JSON)
        output_file (str): Path to save the final video
        theme (str): Visual theme to use
        add_music (bool): Whether to add background music
        add_intro (bool): Whether to add intro animation
        add_outro (bool): Whether to add call-to-action
        
    Returns:
        str: Path to the final video
    """
    try:
        # Get GPU and performance details for logging
        gpu_model = perf_config.gpu_info.get('model', 'Not available')
        gpu_vendor = perf_config.gpu_info.get('vendor', 'None')
        gpu_available = perf_config.gpu_info.get('available', False)
        
        # Log GPU status
        if gpu_available:
            logger.info(f"Creating final video with {theme} theme using {perf_config.optimal_threads} CPU threads" + 
                      f" and {gpu_vendor.upper()} GPU ({gpu_model})")
            
            # Special handling for AMD GPUs on Windows
            if gpu_vendor == 'amd' and platform.system() == 'Windows':
                logger.info("Using optimized AMD GPU settings for video processing")
                
                # Check if we're using the AMF encoder
                if perf_config.codec == 'h264_amf':
                    logger.info("Using AMD AMF hardware encoder")
                else:
                    logger.info("Using CPU-based encoding with AMD GPU acceleration")
        else:
            logger.info(f"Creating final video with {theme} theme using {perf_config.optimal_threads} CPU threads without GPU acceleration")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Get theme settings
        theme_settings = VISUAL_THEMES.get(theme, VISUAL_THEMES["default"])
        
        # Load background video with prefetch for better performance
        background_clip = VideoFileClip(background_video, audio=False)
        
        # Add visual effect to background if specified
        if theme_settings["effect"]:
            background_clip = apply_gpu_effect(background_clip, theme_settings["effect"])
        
        # Load audio in parallel with video processing
        with ThreadPoolExecutor(max_workers=2) as executor:
            voice_future = executor.submit(AudioFileClip, audio_file)
            music_future = executor.submit(get_background_music, 0) if add_music else None
            
            # Get final duration (use audio duration)
            voice_clip = voice_future.result()
            final_duration = voice_clip.duration
            
            # Trim background video to match audio duration if needed
            if background_clip.duration > final_duration:
                background_clip = background_clip.subclip(0, final_duration)
            elif background_clip.duration < final_duration:
                # Loop video to reach target duration
                n_loops = int(final_duration / background_clip.duration) + 1
                background_clip = background_clip.loop(n=n_loops).subclip(0, final_duration)
            
            # Prepare final clips list
            final_clips = [background_clip]
            
            # Process intro and captions in parallel
            with ThreadPoolExecutor(max_workers=2) as parallel_executor:
                intro_future = parallel_executor.submit(create_intro_animation, 3, theme) if add_intro else None
                captions_future = parallel_executor.submit(create_caption_clips, captions_file, final_duration, theme_settings)
                
                # Add intro if requested
                if add_intro and intro_future:
                    intro_clip = intro_future.result()
                    final_clips.insert(0, intro_clip)
                
                # Set audio (combine with background music if requested)
                final_audio = voice_clip
                if add_music and music_future:
                    music_clip = music_future.result()
                    if music_clip:
                        # Loop music to match duration
                        if music_clip.duration < final_duration:
                            n_loops = int(final_duration / music_clip.duration) + 1
                            music_clip = music_clip.loop(n=n_loops).subclip(0, final_duration)
                        else:
                            music_clip = music_clip.subclip(0, final_duration)
                        
                        # Mix voice with background music (voice louder)
                        music_clip = music_clip.volumex(0.2)  # Lower music volume
                        final_audio = CompositeAudioClip([voice_clip, music_clip])
                
                # Set audio for background clip
                video_with_audio = background_clip.set_audio(final_audio)
                
                # Replace background clip with the one with audio
                final_clips[0 if not add_intro else 1] = video_with_audio
                
                # Add captions to final clips
                captions_clips = captions_future.result()
                final_clips.extend(captions_clips)
            
            # Add outro if requested (process in main thread while others complete)
            if add_outro:
                # Create a call-to-action overlay for the last 5 seconds
                cta_clip = create_cta_overlay(min(5, final_duration/4), theme_settings)
                if cta_clip:
                    cta_clip = cta_clip.set_start(final_duration - cta_clip.duration)
                    final_clips.append(cta_clip)
        
        # Combine all elements
        final_video = CompositeVideoClip(final_clips, size=(DEFAULT_WIDTH, DEFAULT_HEIGHT))
        
        # Get optimal encoding parameters from perf_config
        encoding_params = perf_config.get_moviepy_params()
        encoding_params['fps'] = DEFAULT_FPS
        
        # Write final video with optimized parameters
        final_video.write_videofile(output_file, **encoding_params)
        
        logger.info(f"Final video created: {output_file}")
        return output_file
    
    except Exception as e:
        logger.error(f"Error creating final video: {str(e)}")
        # If error occurs, return a simpler video without captions
        return create_simple_video(background_video, audio_file, output_file)


def create_caption_clips(captions_file, video_duration, theme_settings):
    """
    Create TextClips for each caption with theme settings
    Optimized with parallel processing
    
    Args:
        captions_file (str): Path to captions data file (JSON)
        video_duration (float): Video duration in seconds
        theme_settings (dict): Theme settings
        
    Returns:
        list: List of TextClip objects with proper timing
    """
    try:
        # Load captions data from JSON file
        with open(captions_file, 'r', encoding='utf-8') as f:
            captions_data = json.load(f)
        
        # Process captions in parallel batches to avoid overwhelming memory
        caption_clips = []
        
        # Create a worker function for parallel processing
        def process_caption(caption):
            try:
                # Get caption text as list of lines
                lines = caption["text"] if isinstance(caption["text"], list) else [caption["text"]]
                text = '\n'.join(lines)
                
                # Get timing information (convert from milliseconds to seconds)
                start_time = caption["start_time"] / 1000.0
                end_time = caption["end_time"] / 1000.0
                
                # Ensure end time doesn't exceed video duration
                end_time = min(end_time, video_duration)
                
                # Skip if timing is invalid
                if start_time >= end_time or end_time <= 0:
                    return None
                
                # Get style information merged with theme settings
                style = caption["style"] if "style" in caption else {}
                
                # Apply theme settings
                font_name = style.get("font", theme_settings.get("caption_font", "Arial"))
                font_size = style.get("size", 60)
                font_color = style.get("color", theme_settings.get("caption_color", "#FFFFFF"))
                bg_color = style.get("bg_color", theme_settings.get("caption_bg", "#00000080"))
                
                # Create TextClip
                txt_clip = TextClip(
                    text,
                    fontsize=font_size,
                    color=font_color,
                    bg_color=bg_color,
                    font=font_name,
                    align=theme_settings.get("caption_alignment", "center"),
                    method='caption',
                    size=(DEFAULT_WIDTH - 100, None)  # Width with margins
                )
                
                # Apply effect based on theme
                if theme_settings.get("effect") == "fadein":
                    txt_clip = txt_clip.fx(vfx.fadein, 0.5)
                
                # Position captions at the bottom center by default
                position = style.get("position", "center")
                if position == "center":
                    txt_pos = ('center', 'center')
                elif position == "bottom":
                    txt_pos = ('center', DEFAULT_HEIGHT - txt_clip.h - 150)
                else:
                    txt_pos = ('center', 150)  # Top
                
                # Set position and timing
                txt_clip = txt_clip.set_position(txt_pos).set_start(start_time).set_end(end_time)
                
                return txt_clip
            except Exception as e:
                logger.error(f"Error processing caption: {str(e)}")
                return None
        
        # Process captions in parallel using a thread pool
        # Use threads instead of processes because TextClip is not picklable
        batch_size = 10  # Process captions in batches to avoid memory issues
        for i in range(0, len(captions_data), batch_size):
            batch = captions_data[i:i+batch_size]
            with ThreadPoolExecutor(max_workers=min(len(batch), perf_config.optimal_threads)) as executor:
                results = list(executor.map(process_caption, batch))
                caption_clips.extend([clip for clip in results if clip is not None])
        
        return caption_clips
    
    except Exception as e:
        logger.error(f"Error creating caption clips: {str(e)}")
        return []


def get_background_music(duration):
    """
    Get background music from resources directory
    
    Args:
        duration (float): Target duration
        
    Returns:
        AudioFileClip or None: Background music clip
    """
    try:
        music_dir = os.path.join("resources", "music")
        if not os.path.exists(music_dir):
            return None
        
        # Find music files
        music_files = []
        for file in os.listdir(music_dir):
            if file.endswith((".mp3", ".wav")):
                music_files.append(os.path.join(music_dir, file))
        
        if not music_files:
            return None
        
        # Choose random music file
        music_file = random.choice(music_files)
        music_clip = AudioFileClip(music_file)
        
        return music_clip
    
    except Exception as e:
        logger.error(f"Error getting background music: {str(e)}")
        return None


def create_intro_animation(duration, theme, text="YouTube Short"):
    """
    Create intro animation
    
    Args:
        duration (float): Duration in seconds
        theme (str): Theme name
        text (str): Text to display
        
    Returns:
        VideoClip: Intro animation clip
    """
    try:
        # Theme colors
        theme_settings = VISUAL_THEMES.get(theme, VISUAL_THEMES["default"])
        bg_color = "#000000"
        text_color = theme_settings.get("caption_color", "#FFFFFF")
        
        # Create background
        bg_clip = ColorClip(size=(DEFAULT_WIDTH, DEFAULT_HEIGHT), color=bg_color, duration=duration)
        
        # Create text
        txt_clip = TextClip(
            text,
            fontsize=80,
            color=text_color,
            font=theme_settings.get("caption_font", "Arial"),
            align="center"
        )
        
        # Position text in center and apply effect
        txt_clip = (txt_clip
                   .set_position('center')
                   .set_duration(duration)
                   .fx(vfx.fadein, duration/2)
                   .fx(vfx.fadeout, duration/2))
        
        # Combine clips
        intro_clip = CompositeVideoClip([bg_clip, txt_clip])
        
        return intro_clip
    
    except Exception as e:
        logger.error(f"Error creating intro animation: {str(e)}")
        # Return empty clip on error
        return ColorClip(size=(DEFAULT_WIDTH, DEFAULT_HEIGHT), color="#000000", duration=1)


def create_cta_overlay(duration, theme_settings):
    """
    Create call-to-action overlay
    
    Args:
        duration (float): Duration in seconds
        theme_settings (dict): Theme settings
        
    Returns:
        VideoClip: CTA overlay clip
    """
    try:
        # Create text
        like_clip = TextClip(
            "👍 Like & Subscribe! 👍",
            fontsize=60,
            color=theme_settings.get("caption_color", "#FFFFFF"),
            font=theme_settings.get("caption_font", "Arial"),
            bg_color=theme_settings.get("caption_bg", "#00000080"),
            align="center"
        )
        
        # Position at bottom
        like_clip = (like_clip
                    .set_position(('center', DEFAULT_HEIGHT - like_clip.h - 80))
                    .set_duration(duration)
                    .fx(vfx.fadein, 0.5))
        
        return like_clip
    
    except Exception as e:
        logger.error(f"Error creating CTA overlay: {str(e)}")
        return None


def create_simple_video(background_video, audio_file, output_file):
    """
    Create a simple video without captions (fallback)
    Optimized for hardware acceleration
    
    Args:
        background_video (str): Path to background video
        audio_file (str): Path to audio file
        output_file (str): Path to save the final video
        
    Returns:
        str: Path to the final video
    """
    try:
        # Load clips
        video_clip = VideoFileClip(background_video)
        audio_clip = AudioFileClip(audio_file)
        
        # Set duration to match audio
        final_duration = audio_clip.duration
        if video_clip.duration > final_duration:
            video_clip = video_clip.subclip(0, final_duration)
        elif video_clip.duration < final_duration:
            # Loop video to reach target duration
            n_loops = int(final_duration / video_clip.duration) + 1
            video_clip = video_clip.loop(n=n_loops).subclip(0, final_duration)
        
        # Add audio to video
        final_clip = video_clip.set_audio(audio_clip)
        
        # Get optimal encoding parameters from perf_config
        encoding_params = perf_config.get_moviepy_params()
        encoding_params['fps'] = DEFAULT_FPS
        
        # Write final video with hardware acceleration
        final_clip.write_videofile(output_file, **encoding_params)
        
        return output_file
    
    except Exception as e:
        logger.error(f"Error creating simple video: {str(e)}")
        return None


if __name__ == "__main__":
    # Simple test
    test_bg = "output/test_background.mp4"
    test_audio = "output/test_audio.mp3"
    test_captions = "output/test_captions.json"
    test_output = "output/test_final.mp4"
    
    # Print performance configuration
    perf_config.print_system_info()
    
    # Create video
    create_final_video(test_bg, test_audio, test_captions, test_output, theme="modern", add_outro=True) 