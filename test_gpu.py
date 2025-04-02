"""
Test script for GPU acceleration in video processing
"""

import os
import logging
from src.performance_config import init_performance_settings, get_performance_config
from moviepy.editor import VideoFileClip

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gpu-test')

def test_video_processing():
    """Test video processing with GPU acceleration"""
    # Initialize performance settings
    config = init_performance_settings()
    
    # Print GPU information
    logger.info(f"GPU Vendor: {config.gpu_info.get('vendor', 'None')}")
    logger.info(f"GPU Model: {config.gpu_info.get('model', 'None')}")
    logger.info(f"GPU Available: {config.gpu_info.get('available', False)}")
    
    # Check if templates directory exists
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Find a video file to test with
    test_files = []
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith(('.mp4', '.mov', '.avi')):
                test_files.append(os.path.join(root, file))
    
    if not test_files:
        logger.error("No video files found for testing")
        return
    
    # Use the first video file found
    test_file = test_files[0]
    logger.info(f"Testing with video file: {test_file}")
    
    try:
        # Load the video
        clip = VideoFileClip(test_file)
        
        # Get encoding parameters
        encoding_params = config.get_moviepy_params()
        logger.info(f"Encoding parameters: {encoding_params}")
        
        # Process a short segment
        clip = clip.subclip(0, min(5, clip.duration))
        
        # Set output path
        output_path = os.path.join('templates', 'test_output.mp4')
        
        # Write the processed video
        logger.info("Writing video with GPU acceleration...")
        clip.write_videofile(
            output_path,
            **encoding_params
        )
        
        logger.info(f"Video successfully processed and saved to {output_path}")
        clip.close()
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise e

if __name__ == "__main__":
    test_video_processing() 