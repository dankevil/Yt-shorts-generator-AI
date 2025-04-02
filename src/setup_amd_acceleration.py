"""
AMD GPU Acceleration Setup for Windows
Helps set up and configure AMD GPU acceleration for video processing
"""

import os
import sys
import subprocess
import platform
import logging
import ctypes
import winreg
import webbrowser
from urllib.request import urlretrieve
import zipfile
import tempfile
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('amd_setup')

def is_admin():
    """Check if the script is running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def check_ffmpeg_version():
    """Check if FFmpeg is installed and get its version"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode != 0:
            return None
        
        version_line = result.stdout.splitlines()[0]
        logger.info(f"Found FFmpeg: {version_line}")
        return version_line
    except Exception as e:
        logger.error(f"Error checking FFmpeg: {str(e)}")
        return None

def download_ffmpeg_with_amf():
    """Download FFmpeg build with AMD AMF support"""
    logger.info("Downloading FFmpeg with AMD AMF support...")
    
    # URL for FFmpeg that includes AMD AMF encoder (BtbN builds)
    download_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "ffmpeg.zip")
        
        # Download the file
        logger.info(f"Downloading from {download_url}...")
        urlretrieve(download_url, zip_path)
        
        # Extract the ZIP file
        logger.info("Extracting FFmpeg...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find the bin directory in the extracted files
        bin_dir = None
        for root, dirs, files in os.walk(temp_dir):
            if "bin" in dirs:
                bin_dir = os.path.join(root, "bin")
                break
        
        if not bin_dir:
            logger.error("Could not find the bin directory in the extracted files")
            return False
        
        # Determine where to install FFmpeg
        install_dir = os.path.join(os.environ['ProgramFiles'], 'FFmpeg')
        os.makedirs(install_dir, exist_ok=True)
        
        # Copy the files
        for file in os.listdir(bin_dir):
            shutil.copy2(os.path.join(bin_dir, file), os.path.join(install_dir, file))
        
        logger.info(f"FFmpeg with AMD AMF support installed to {install_dir}")
        
        # Add to PATH if not already there
        add_to_path(install_dir)
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        return True
        
    except Exception as e:
        logger.error(f"Error downloading FFmpeg: {str(e)}")
        return False

def add_to_path(directory):
    """Add a directory to the system PATH"""
    try:
        # Get the current PATH
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 0, winreg.KEY_ALL_ACCESS)
        path = winreg.QueryValueEx(key, 'Path')[0]
        
        # Check if the directory is already in PATH
        if directory.lower() not in path.lower():
            # Add the directory to PATH
            path = f"{path};{directory}"
            winreg.SetValueEx(key, 'Path', 0, winreg.REG_EXPAND_SZ, path)
            winreg.CloseKey(key)
            logger.info(f"Added {directory} to system PATH")
            
            # Notify the system about the change
            subprocess.run(['powershell', '-Command', 'SETX PATH "$env:path"'], capture_output=True)
            return True
        else:
            logger.info(f"{directory} is already in system PATH")
            return True
    
    except Exception as e:
        logger.error(f"Error adding to PATH: {str(e)}")
        return False

def check_amd_drivers():
    """Check if AMD drivers are properly installed"""
    try:
        # Check AMD driver registry
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\AMD\AMF') as key:
                version = winreg.QueryValueEx(key, 'Version')[0]
                logger.info(f"AMD Media Foundation (AMF) is installed, version: {version}")
                return True
        except:
            logger.warning("AMD Media Foundation (AMF) registry entry not found")
            
        # Check if AMD GPU is present
        gpu_info = subprocess.run(['powershell', '-Command', "Get-WmiObject Win32_VideoController | Format-List Name, AdapterCompatibility"], 
                                capture_output=True, text=True).stdout.lower()
        
        if 'amd' in gpu_info or 'radeon' in gpu_info or 'advanced micro devices' in gpu_info:
            logger.info("AMD GPU detected, but AMF is not properly installed")
            return False
        else:
            logger.warning("No AMD GPU detected in system")
            return False
            
    except Exception as e:
        logger.error(f"Error checking AMD drivers: {str(e)}")
        return False

def open_amd_driver_download():
    """Open the AMD driver download page"""
    logger.info("Opening AMD driver download page...")
    
    # Open the AMD driver download page
    webbrowser.open('https://www.amd.com/en/support')
    
    logger.info("Please download and install the latest drivers for your AMD GPU")
    logger.info("After installation, restart your computer and run this script again")
    
    return True

def configure_environment_variables():
    """Set up environment variables for AMD GPU acceleration"""
    try:
        # Set environment variables
        env_vars = {
            'AMF_ENABLE_HARDWARE_ENCODING': '1',
            'MOVIEPY_FFMPEG_OPTS': '-hwaccel dxva2'
        }
        
        # Set environment variables at the system level
        for var_name, var_value in env_vars.items():
            subprocess.run(['powershell', '-Command', f'[System.Environment]::SetEnvironmentVariable("{var_name}", "{var_value}", "Machine")'], 
                         capture_output=True)
            os.environ[var_name] = var_value
            logger.info(f"Set environment variable: {var_name}={var_value}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting environment variables: {str(e)}")
        return False

def update_project_config():
    """Update the project configuration to use AMD GPU"""
    try:
        # Import the performance config module
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from src.performance_config import init_performance_settings
        
        # Initialize the performance settings
        config = init_performance_settings()
        
        # Check if AMD GPU is detected
        if config.gpu_info.get('vendor') == 'amd':
            logger.info("Project configuration updated to use AMD GPU acceleration")
            config.print_system_info()
            return True
        else:
            logger.warning("AMD GPU not detected in project configuration")
            return False
            
    except Exception as e:
        logger.error(f"Error updating project configuration: {str(e)}")
        return False

def main():
    """Main function to set up AMD GPU acceleration"""
    logger.info("=== AMD GPU Acceleration Setup for Windows ===")
    
    # Check if running on Windows
    if platform.system() != 'Windows':
        logger.error("This script only works on Windows")
        return
    
    # Check if running with administrator privileges
    if not is_admin():
        logger.error("This script needs to be run with administrator privileges")
        logger.info("Please run this script as administrator")
        return
    
    # Check for AMD GPU
    logger.info("Checking for AMD GPU...")
    if not check_amd_drivers():
        logger.warning("AMD Media Foundation (AMF) not properly installed")
        
        # Ask if user wants to download AMD drivers
        logger.info("Would you like to open the AMD driver download page? (y/n)")
        if input().lower() == 'y':
            open_amd_driver_download()
            logger.info("Please run this script again after installing the drivers")
            return
    
    # Check FFmpeg
    logger.info("Checking FFmpeg installation...")
    ffmpeg_version = check_ffmpeg_version()
    
    if not ffmpeg_version:
        logger.warning("FFmpeg not found")
        
        # Ask if user wants to install FFmpeg
        logger.info("Would you like to download and install FFmpeg with AMD AMF support? (y/n)")
        if input().lower() == 'y':
            if download_ffmpeg_with_amf():
                logger.info("FFmpeg with AMD AMF support installed successfully")
            else:
                logger.error("Failed to install FFmpeg")
                return
        else:
            logger.info("FFmpeg installation skipped")
            return
    else:
        # Check if FFmpeg has AMD AMF support
        result = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True)
        encoder_output = result.stdout.lower()
        
        if 'h264_amf' not in encoder_output:
            logger.warning("Current FFmpeg installation does not support AMD AMF encoding")
            
            # Ask if user wants to download FFmpeg with AMF support
            logger.info("Would you like to download and install FFmpeg with AMD AMF support? (y/n)")
            if input().lower() == 'y':
                if download_ffmpeg_with_amf():
                    logger.info("FFmpeg with AMD AMF support installed successfully")
                else:
                    logger.error("Failed to install FFmpeg")
                    return
    
    # Configure environment variables
    logger.info("Configuring environment variables...")
    if configure_environment_variables():
        logger.info("Environment variables configured successfully")
    else:
        logger.error("Failed to configure environment variables")
    
    # Update project configuration
    logger.info("Updating project configuration...")
    if update_project_config():
        logger.info("Project configuration updated successfully")
    else:
        logger.warning("Failed to update project configuration")
    
    logger.info("=== AMD GPU Acceleration Setup Complete ===")
    logger.info("Please restart your computer to apply all changes")
    logger.info("After restarting, you can verify the setup by running:")
    logger.info("  python -m src.check_gpu_acceleration")

if __name__ == "__main__":
    main() 