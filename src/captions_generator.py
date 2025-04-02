"""
Captions Generator Module
Creates visually appealing captions for YouTube shorts
"""

import os
import json
import logging
from pydub import AudioSegment

# Configure logging
logger = logging.getLogger(__name__)


def create_captions(script, audio_file, max_chars_per_line=40):
    """
    Create captions data from script and audio file
    
    Args:
        script (str): The script text
        audio_file (str): Path to the audio file for timing
        max_chars_per_line (int): Maximum characters per caption line
        
    Returns:
        str: Path to the captions data file (JSON)
    """
    try:
        logger.info("Generating captions data")
        
        # Parse script into sentences or logical chunks
        sentences = parse_script_to_sentences(script)
        
        # Get audio duration
        audio_duration = get_audio_duration(audio_file)
        
        # Generate caption timing data
        captions_data = generate_caption_timing(sentences, audio_duration, max_chars_per_line)
        
        # Save captions to file
        output_file = audio_file.replace("_audio.mp3", "_captions.json")
        save_captions_to_file(captions_data, output_file)
        
        logger.info(f"Captions data saved to {output_file}")
        return output_file
    
    except Exception as e:
        logger.error(f"Error creating captions: {str(e)}")
        # Create minimal captions as fallback
        return create_fallback_captions(script, audio_file)


def parse_script_to_sentences(script):
    """
    Parse script into sentences or logical chunks
    
    Args:
        script (str): The script text
        
    Returns:
        list: List of sentences
    """
    # Replace newlines with period if no punctuation
    text = script.replace("\n\n", ". ").replace("\n", ". ")
    
    # Split by sentence-ending punctuation
    raw_sentences = []
    current = ""
    
    for char in text:
        current += char
        if char in ['.', '!', '?'] and current.strip():
            raw_sentences.append(current.strip())
            current = ""
    
    # Add any remaining text
    if current.strip():
        raw_sentences.append(current.strip())
    
    # Clean up sentences
    sentences = []
    for sentence in raw_sentences:
        # Remove excessive whitespace
        clean = ' '.join(sentence.split())
        if clean:
            sentences.append(clean)
    
    return sentences


def get_audio_duration(audio_file):
    """
    Get duration of audio file in milliseconds
    
    Args:
        audio_file (str): Path to the audio file
        
    Returns:
        float: Duration in milliseconds
    """
    try:
        audio = AudioSegment.from_file(audio_file)
        return len(audio)
    except Exception as e:
        logger.error(f"Error getting audio duration: {str(e)}")
        # Fallback to estimated duration
        return 30000  # 30 seconds


def generate_caption_timing(sentences, audio_duration, max_chars_per_line):
    """
    Generate caption timing data
    
    Args:
        sentences (list): List of sentences
        audio_duration (float): Audio duration in milliseconds
        max_chars_per_line (int): Maximum characters per caption line
        
    Returns:
        list: List of caption data dictionaries
    """
    total_chars = sum(len(s) for s in sentences)
    captions_data = []
    
    start_time = 0
    for sentence in sentences:
        # Break long sentences into multiple lines
        lines = break_into_lines(sentence, max_chars_per_line)
        
        # Calculate duration based on characters proportion
        duration = (len(sentence) / total_chars) * audio_duration
        end_time = start_time + duration
        
        # Add caption data
        captions_data.append({
            "text": lines,
            "start_time": start_time,
            "end_time": end_time,
            "style": get_caption_style(sentence)
        })
        
        start_time = end_time
    
    return captions_data


def break_into_lines(text, max_chars_per_line):
    """
    Break text into multiple lines for better readability
    
    Args:
        text (str): Text to break into lines
        max_chars_per_line (int): Maximum characters per line
        
    Returns:
        list: List of lines
    """
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line) + len(word) + 1 > max_chars_per_line:
            lines.append(current_line.strip())
            current_line = word + " "
        else:
            current_line += word + " "
    
    if current_line.strip():
        lines.append(current_line.strip())
    
    return lines


def get_caption_style(text):
    """
    Determine caption style based on text content
    
    Args:
        text (str): Caption text
        
    Returns:
        dict: Style configuration
    """
    # Default style
    style = {
        "font": "Arial",
        "size": 60,
        "color": "#FFFFFF",
        "bg_color": "#00000080",  # Semi-transparent black
        "alignment": "center",
        "position": "center"
    }
    
    # Customize style based on content
    if text.isupper():
        style["size"] = 70  # Larger for emphasized text
    
    if any(punc in text for punc in "!?"):
        style["color"] = "#FFD700"  # Gold for exciting statements
    
    return style


def save_captions_to_file(captions_data, output_file):
    """
    Save captions data to JSON file
    
    Args:
        captions_data (list): List of caption data dictionaries
        output_file (str): Path to save JSON file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(captions_data, f, indent=2)


def create_fallback_captions(script, audio_file):
    """
    Create minimal fallback captions
    
    Args:
        script (str): The script text
        audio_file (str): Path to the audio file
        
    Returns:
        str: Path to the captions data file
    """
    output_file = audio_file.replace("_audio.mp3", "_captions.json")
    
    # Create simple caption
    captions_data = [{
        "text": [script[:40]],
        "start_time": 0,
        "end_time": 30000,  # 30 seconds
        "style": {
            "font": "Arial",
            "size": 60,
            "color": "#FFFFFF",
            "bg_color": "#00000080",
            "alignment": "center",
            "position": "center"
        }
    }]
    
    # Save to file
    save_captions_to_file(captions_data, output_file)
    
    return output_file


if __name__ == "__main__":
    # Simple test
    test_script = "This is a test script. It should be split into multiple captions. Each with proper timing."
    test_audio = "output/test_audio.mp3"
    create_captions(test_script, test_audio) 