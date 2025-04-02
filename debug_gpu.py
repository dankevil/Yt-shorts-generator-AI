"""
GPU Detection Debug Tool

This script helps identify if your GPU is properly detected and configured for the application.
"""

import subprocess
import platform
import logging
import sys

logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gpu-debug')

def detect_windows_gpu():
    """Detect GPU on Windows systems"""
    logger.info("Running Windows GPU detection...")
    
    try:
        # Get basic GPU info
        output = subprocess.check_output(
            "powershell -Command \"Get-WmiObject Win32_VideoController | Format-List Name, AdapterCompatibility, DriverVersion\"", 
            shell=True
        ).decode('utf-8')
        
        logger.info("GPU Information from WMI:")
        print("\n" + output)
        
        # Check if common GPU vendors are detected
        output_lower = output.lower()
        if 'nvidia' in output_lower:
            logger.info("NVIDIA GPU detected")
        elif any(gpu in output_lower for gpu in ['amd', 'radeon', 'ati', 'advanced micro devices']):
            logger.info("AMD GPU detected")
        else:
            logger.warning("No recognized dedicated GPU vendor detected")
        
        # Test DirectX information
        try:
            dxdiag = subprocess.check_output(
                "powershell -Command \"dxdiag /t dxinfo.txt\"", 
                shell=True
            )
            
            # Wait a bit for the file to be written
            import time
            time.sleep(2)
            
            # Read the DXDiag output
            if os.path.exists("dxinfo.txt"):
                with open("dxinfo.txt", "r") as f:
                    dx_content = f.read()
                
                print("\nDirectX Information:")
                
                # Extract relevant GPU sections
                display_sections = []
                current_section = []
                in_display_section = False
                
                for line in dx_content.split('\n'):
                    if line.startswith("-------------"):
                        if in_display_section:
                            display_sections.append("\n".join(current_section))
                        current_section = []
                        in_display_section = False
                    elif line.startswith("Display Devices"):
                        in_display_section = True
                        current_section.append(line)
                    elif in_display_section:
                        current_section.append(line)
                
                # Print display sections
                for section in display_sections:
                    print(section)
                    print("\n" + "-"*80 + "\n")
                
                # Clean up
                os.remove("dxinfo.txt")
            else:
                logger.warning("DXDiag output file not found")
        except Exception as e:
            logger.error(f"Error running DXDiag: {e}")
    
    except Exception as e:
        logger.error(f"Error during Windows GPU detection: {e}")

def main():
    """Main function to run GPU detection tests"""
    logger.info("Starting GPU detection debug process")
    logger.info(f"Operating System: {platform.system()} {platform.release()}")
    
    if platform.system() == "Windows":
        detect_windows_gpu()
    else:
        logger.info("This debug script currently only supports Windows. Please add appropriate detection for your OS.")
    
    # Try to import our performance config
    logger.info("Testing application's built-in GPU detection...")
    try:
        import os
        # Add the current directory to the path if not already there
        if os.getcwd() not in sys.path:
            sys.path.append(os.getcwd())
        
        from src.performance_config import get_performance_config, init_performance_settings
        
        # Initialize performance settings
        init_performance_settings()
        perf_config = get_performance_config()
        
        print("\nApplication GPU Detection Results:")
        print(f"GPU Detected: {perf_config.gpu_info['available']}")
        print(f"GPU Vendor: {perf_config.gpu_info.get('vendor', 'None')}")
        print(f"GPU Model: {perf_config.gpu_info.get('model', 'None')}")
        print(f"CUDA Available: {perf_config.has_cuda}")
        print(f"MPS Available: {perf_config.has_mps}")
        print(f"Video Codec: {perf_config.codec}")
        print(f"Encoding Preset: {perf_config.encoding_preset}")
    except Exception as e:
        logger.error(f"Error during application GPU detection: {e}")
    
    logger.info("GPU detection debug completed")

if __name__ == "__main__":
    import os
    main() 