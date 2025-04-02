"""
GPU Acceleration Checker Utility
Helps verify if GPU acceleration is properly configured, with special focus on AMD GPUs
"""

import os
import sys
import subprocess
import platform
import logging
from importlib import import_module

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gpu_checker')

def check_ffmpeg_support():
    """Check FFmpeg installation and available hardware acceleration methods"""
    logger.info("Checking FFmpeg installation and hardware acceleration support")
    
    try:
        # Check FFmpeg version
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"FFmpeg installed: {result.stdout.splitlines()[0]}")
        else:
            logger.error("FFmpeg not found or not working properly")
            return False
        
        # Check available encoders
        encoders = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True)
        encoder_output = encoders.stdout.lower()
        
        # Check for hardware acceleration encoders
        accel_encoders = {
            'nvidia': ['h264_nvenc', 'hevc_nvenc'],
            'amd': ['h264_amf', 'hevc_amf'],
            'intel': ['h264_qsv', 'hevc_qsv'],
            'generic': ['h264_vaapi', 'h264_videotoolbox']
        }
        
        logger.info("Checking available hardware encoders:")
        for vendor, vendor_encoders in accel_encoders.items():
            for encoder in vendor_encoders:
                if encoder in encoder_output:
                    logger.info(f"✓ {vendor.upper()} encoder {encoder} is available")
                else:
                    logger.info(f"✗ {vendor.upper()} encoder {encoder} is not available")
        
        # Check hardware acceleration methods
        hwaccel_output = subprocess.run(['ffmpeg', '-hwaccels'], capture_output=True, text=True).stdout.lower()
        logger.info("\nAvailable hardware acceleration methods:")
        
        acceleration_methods = [
            'cuda',  # NVIDIA
            'dxva2',  # Windows DirectX Video Acceleration
            'd3d11va',  # Windows DirectX 11 Video Acceleration
            'vaapi',  # Video Acceleration API (Linux)
            'vdpau',  # Video Decode and Presentation API for Unix
            'qsv',  # Intel Quick Sync Video
            'videotoolbox'  # macOS
        ]
        
        for method in acceleration_methods:
            if method in hwaccel_output:
                logger.info(f"✓ Hardware acceleration method '{method}' is available")
            else:
                logger.info(f"✗ Hardware acceleration method '{method}' is not available")
        
        return True
    
    except Exception as e:
        logger.error(f"Error checking FFmpeg: {str(e)}")
        return False

def check_amd_gpu_windows():
    """Perform specific checks for AMD GPUs on Windows"""
    if platform.system() != 'Windows':
        logger.info("Not on Windows, skipping AMD Windows-specific checks")
        return
    
    logger.info("\nPerforming AMD GPU checks for Windows:")
    
    # Check for AMD driver installation
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\AMD\AMF") as key:
            version = winreg.QueryValueEx(key, "Version")[0]
            logger.info(f"✓ AMD Media Foundation (AMF) is installed, version: {version}")
    except:
        logger.info("✗ AMD Media Foundation (AMF) registry entry not found")
    
    # Check AMD GPU DirectX capabilities
    try:
        dxdiag_output = subprocess.run(
            ['powershell', '-Command', 'dxdiag /t dxdiag_output.txt'], 
            capture_output=True, 
            text=True
        )
        
        # Wait for dxdiag to complete
        import time
        time.sleep(3)
        
        if os.path.exists('dxdiag_output.txt'):
            with open('dxdiag_output.txt', 'r') as f:
                content = f.read().lower()
                
            # Check for AMD GPU
            if 'amd' in content or 'radeon' in content or 'advanced micro devices' in content:
                logger.info("✓ AMD GPU detected in DirectX diagnostics")
                
                # Check DirectX version
                import re
                dx_version_match = re.search(r'directx version: (.*)', content)
                if dx_version_match:
                    logger.info(f"✓ DirectX Version: {dx_version_match.group(1)}")
                
                # Check for DirectX Video Acceleration
                if 'directdraw acceleration: enabled' in content:
                    logger.info("✓ DirectDraw Acceleration is enabled")
                else:
                    logger.info("✗ DirectDraw Acceleration is not enabled")
                    
                if 'direct3d acceleration: enabled' in content:
                    logger.info("✓ Direct3D Acceleration is enabled")
                else:
                    logger.info("✗ Direct3D Acceleration is not enabled")
            else:
                logger.info("✗ No AMD GPU detected in DirectX diagnostics")
            
            # Clean up the temporary file
            os.remove('dxdiag_output.txt')
    except Exception as e:
        logger.error(f"Error checking DirectX capabilities: {str(e)}")

def check_performance_config():
    """Test the performance config module with AMD GPU"""
    logger.info("\nTesting the project's performance configuration:")
    
    try:
        # Import the performance config module
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from src.performance_config import get_performance_config
        
        # Get the performance config
        perf_config = get_performance_config()
        
        # Print GPU information
        gpu_info = perf_config.gpu_info
        logger.info(f"GPU Vendor: {gpu_info.get('vendor', 'None')}")
        logger.info(f"GPU Model: {gpu_info.get('model', 'None')}")
        logger.info(f"GPU Available: {gpu_info.get('available', False)}")
        
        # Check if using AMD GPU
        if gpu_info.get('vendor') == 'amd':
            logger.info("AMD GPU detected in performance config")
            
            # Check codec selection
            logger.info(f"Selected codec: {perf_config.codec}")
            
            # Check FFmpeg parameters
            logger.info(f"FFmpeg parameters: {perf_config.ffmpeg_params}")
            
            # Check MoviePy parameters
            moviepy_params = perf_config.get_moviepy_params()
            logger.info(f"MoviePy parameters: {moviepy_params}")
            
            # Check environment variables
            logger.info("\nRelevant environment variables:")
            env_vars = ['MOVIEPY_FFMPEG_OPTS', 'AMF_ENABLE_HARDWARE_ENCODING', 'PYTORCH_USE_OPENCL']
            for var in env_vars:
                if var in os.environ:
                    logger.info(f"{var} = {os.environ[var]}")
                else:
                    logger.info(f"{var} is not set")
        else:
            logger.info("AMD GPU not detected in performance config")
        
    except Exception as e:
        logger.error(f"Error testing performance config: {str(e)}")

def main():
    """Main function to perform all checks"""
    logger.info(f"=== GPU Acceleration Checker for {platform.system()} ===")
    logger.info(f"System: {platform.system()} {platform.release()} ({platform.machine()})")
    
    # Run FFmpeg checks
    check_ffmpeg_support()
    
    # Run AMD-specific checks on Windows
    if platform.system() == 'Windows':
        check_amd_gpu_windows()
    
    # Check our project's performance configuration
    check_performance_config()
    
    logger.info("\n=== GPU Acceleration Check Complete ===")
    logger.info("If you're using an AMD GPU on Windows and hardware acceleration isn't working:")
    logger.info("1. Make sure you have the latest AMD drivers installed")
    logger.info("2. Verify that the AMF encoder is available in FFmpeg")
    logger.info("3. Check that DirectX acceleration is enabled")
    logger.info("4. Try setting the environment variable: AMF_ENABLE_HARDWARE_ENCODING=1")

if __name__ == "__main__":
    main() 