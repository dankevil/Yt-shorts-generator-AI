"""
Text-to-Speech Module
Converts text scripts to spoken audio using gTTS
"""

import os
import logging
from gtts import gTTS
from pydub import AudioSegment

# Configure logging
logger = logging.getLogger(__name__)


def convert_text_to_speech(text, output_file, language='en', slow=False):
    """
    Convert text to speech and save to file
    
    Args:
        text (str): The text to convert to speech
        output_file (str): Path to save the audio file
        language (str): Language code (default: 'en')
        slow (bool): Whether to speak slowly (default: False)
        
    Returns:
        str: Path to the saved audio file
    """
    try:
        logger.info(f"Converting text to speech, output: {output_file}")
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Clean up text for better speech
        cleaned_text = clean_text_for_tts(text)
        
        # Convert text to speech
        tts = gTTS(text=cleaned_text, lang=language, slow=slow)
        
        # Save to file
        temp_file = output_file.replace(".mp3", "_temp.mp3")
        tts.save(temp_file)
        
        # Process audio for better quality (normalize, adjust speed)
        process_audio(temp_file, output_file)
        
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
        logger.info("Text-to-speech conversion completed successfully")
        return output_file
    
    except Exception as e:
        logger.error(f"Error in text-to-speech conversion: {str(e)}")
        raise


def clean_text_for_tts(text):
    """
    Clean and prepare text for better TTS results
    
    Args:
        text (str): Input text
        
    Returns:
        str: Cleaned text
    """
    # Replace newlines with periods for better pausing
    text = text.replace("\n\n", ". ").replace("\n", ". ")
    
    # Remove multiple spaces
    text = " ".join(text.split())
    
    # Add pauses for better flow by ensuring punctuation has spaces after it
    for punct in ['.', ',', '!', '?', ':', ';']:
        text = text.replace(punct, punct + ' ')
    
    # Remove multiple spaces again after adding punctuation spaces
    text = " ".join(text.split())
    
    return text


def process_audio(input_file, output_file):
    """
    Process audio file for better quality
    
    Args:
        input_file (str): Path to input audio file
        output_file (str): Path to save processed audio
    """
    try:
        # Load audio
        audio = AudioSegment.from_mp3(input_file)
        
        # Normalize audio (adjust volume)
        normalized_audio = audio.normalize()
        
        # Save processed audio
        normalized_audio.export(output_file, format="mp3")
        
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        # If processing fails, use the original file
        if os.path.exists(input_file) and input_file != output_file:
            import shutil
            shutil.copy(input_file, output_file)


if __name__ == "__main__":
    # Simple test
    test_text = "This is a test of the text to speech conversion. It should sound natural and clear."
    output_path = "output/test_audio.mp3"
    convert_text_to_speech(test_text, output_path) 