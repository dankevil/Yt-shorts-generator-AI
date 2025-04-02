"""
Resources Downloader
Downloads sample background videos and music for use in YouTube shorts
"""

import os
import requests
import zipfile
import logging
import argparse
from tqdm import tqdm
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# URLs for resources
RESOURCE_URLS = {
    "background_videos": "https://assets.mixkit.co/video-collections/369/369-download.zip",  # Sample vertical videos
    "background_music": "https://assets.mixkit.co/music-collections/44/44-download.zip",     # Sample background music
}

# Default directories
DEFAULT_RESOURCES_DIR = "resources"
VIDEO_DIR = os.path.join(DEFAULT_RESOURCES_DIR, "videos")
MUSIC_DIR = os.path.join(DEFAULT_RESOURCES_DIR, "music")


def download_file(url, target_path):
    """
    Download a file from URL to target path with progress bar
    
    Args:
        url (str): URL to download
        target_path (str): Path to save the file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Get file size for progress bar
        total_size = int(response.headers.get('content-length', 0))
        
        # Create target directory if it doesn't exist
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Download with progress bar
        with open(target_path, 'wb') as file, tqdm(
            desc=os.path.basename(target_path),
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in response.iter_content(chunk_size=8192):
                size = file.write(chunk)
                bar.update(size)
                
        return True
    
    except Exception as e:
        logger.error(f"Error downloading {url}: {str(e)}")
        return False


def extract_zip(zip_path, extract_to):
    """
    Extract a zip file to target directory
    
    Args:
        zip_path (str): Path to zip file
        extract_to (str): Directory to extract to
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Extracting {zip_path} to {extract_to}")
        
        # Create target directory if it doesn't exist
        os.makedirs(extract_to, exist_ok=True)
        
        # Extract zip
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Get total number of files for progress bar
            total_files = len(zip_ref.infolist())
            
            # Extract with progress bar
            for i, file in enumerate(zip_ref.infolist()):
                zip_ref.extract(file, extract_to)
                print(f"Extracting: {i+1}/{total_files} files", end='\r')
                
        logger.info(f"Successfully extracted {total_files} files")
        return True
    
    except Exception as e:
        logger.error(f"Error extracting {zip_path}: {str(e)}")
        return False


def process_extracted_files(directory):
    """
    Process extracted files - handle nested directories and cleanup
    
    Args:
        directory (str): Directory to process
    """
    # Walk through extracted files and move them to root directory
    for root, dirs, files in os.walk(directory):
        # Skip the root directory
        if root == directory:
            continue
            
        for file in files:
            source_file = os.path.join(root, file)
            target_file = os.path.join(directory, file)
            
            # Skip if file exists
            if os.path.exists(target_file):
                continue
                
            # Move file
            try:
                os.rename(source_file, target_file)
            except Exception as e:
                logger.error(f"Error moving {source_file}: {str(e)}")
    
    # Remove empty directories
    for root, dirs, files in os.walk(directory, topdown=False):
        for dir_name in dirs:
            try:
                dir_path = os.path.join(root, dir_name)
                if not os.listdir(dir_path):  # Check if directory is empty
                    os.rmdir(dir_path)
            except Exception as e:
                logger.error(f"Error removing directory {dir_path}: {str(e)}")


def download_resources(resource_type):
    """
    Download and extract resources
    
    Args:
        resource_type (str): Type of resource to download (background_videos, background_music, or all)
        
    Returns:
        bool: True if successful, False otherwise
    """
    if resource_type not in ["background_videos", "background_music", "all"]:
        logger.error(f"Invalid resource type: {resource_type}")
        return False
    
    resources_to_download = RESOURCE_URLS.items() if resource_type == "all" else [(resource_type, RESOURCE_URLS[resource_type])]
    
    for res_type, url in resources_to_download:
        logger.info(f"Downloading {res_type} from {url}")
        
        # Determine target directory
        target_dir = VIDEO_DIR if res_type == "background_videos" else MUSIC_DIR
        os.makedirs(target_dir, exist_ok=True)
        
        # Download zip file
        zip_path = os.path.join(target_dir, f"{res_type}.zip")
        if download_file(url, zip_path):
            # Extract zip file
            if extract_zip(zip_path, target_dir):
                # Process extracted files
                process_extracted_files(target_dir)
                
                # Remove zip file
                try:
                    os.remove(zip_path)
                except Exception as e:
                    logger.error(f"Error removing zip file {zip_path}: {str(e)}")
            
            logger.info(f"Successfully downloaded and extracted {res_type}")
        else:
            logger.error(f"Failed to download {res_type}")
            return False
    
    return True


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Download resources for YouTube Shorts Generator")
    parser.add_argument(
        "--resource", 
        type=str, 
        choices=["background_videos", "background_music", "all"], 
        default="all",
        help="Type of resource to download"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_RESOURCES_DIR,
        help="Directory to save resources"
    )
    
    args = parser.parse_args()
    
    # Update global variables based on output directory
    global DEFAULT_RESOURCES_DIR, VIDEO_DIR, MUSIC_DIR
    DEFAULT_RESOURCES_DIR = args.output_dir
    VIDEO_DIR = os.path.join(DEFAULT_RESOURCES_DIR, "videos")
    MUSIC_DIR = os.path.join(DEFAULT_RESOURCES_DIR, "music")
    
    logger.info(f"Downloading {args.resource} resources to {DEFAULT_RESOURCES_DIR}")
    
    if download_resources(args.resource):
        logger.info("All resources downloaded successfully")
        
        # Print summary
        video_count = len([f for f in os.listdir(VIDEO_DIR) if os.path.isfile(os.path.join(VIDEO_DIR, f))]) if os.path.exists(VIDEO_DIR) else 0
        music_count = len([f for f in os.listdir(MUSIC_DIR) if os.path.isfile(os.path.join(MUSIC_DIR, f))]) if os.path.exists(MUSIC_DIR) else 0
        
        logger.info(f"Downloaded {video_count} background videos and {music_count} music tracks")
        
        # Move videos to correct location
        if os.path.exists(VIDEO_DIR) and video_count > 0:
            os.makedirs(os.path.join(DEFAULT_RESOURCES_DIR), exist_ok=True)
            for file in os.listdir(VIDEO_DIR):
                source = os.path.join(VIDEO_DIR, file)
                target = os.path.join(DEFAULT_RESOURCES_DIR, file)
                if os.path.isfile(source) and not os.path.exists(target):
                    try:
                        os.rename(source, target)
                    except Exception as e:
                        logger.error(f"Error moving {source} to {target}: {str(e)}")
            
        print("\nYou can now use these resources in your YouTube Shorts Generator!")
    else:
        logger.error("Failed to download resources")


if __name__ == "__main__":
    main() 