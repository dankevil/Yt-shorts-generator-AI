"""
Dependencies installer for GPU-accelerated video processing
"""
import os
import sys
import subprocess
import platform

def install_package(package, upgrade=False):
    """Install a package using pip"""
    cmd = [sys.executable, "-m", "pip", "install"]
    if upgrade:
        cmd.append("--upgrade")
    cmd.append(package)
    
    try:
        subprocess.check_call(cmd)
        print(f"Successfully installed {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"Failed to install {package}")
        return False

def detect_gpu():
    """Detect GPU type and return appropriate PyTorch installation command"""
    is_windows = platform.system() == "Windows"
    
    if is_windows:
        try:
            # Check for NVIDIA GPU on Windows
            gpu_info = subprocess.check_output("powershell -Command \"Get-WmiObject Win32_VideoController | Select-Object Name\"", 
                                              shell=True).decode('utf-8').lower()
            if 'nvidia' in gpu_info:
                print("NVIDIA GPU detected")
                return "nvidia"
            elif 'amd' in gpu_info or 'radeon' in gpu_info:
                print("AMD GPU detected")
                return "amd"
            else:
                print("No compatible GPU detected, will use CPU")
                return "cpu"
        except Exception as e:
            print(f"Error detecting GPU: {str(e)}")
            return "cpu"
    else:
        # For non-Windows systems
        try:
            # Try to check for NVIDIA GPU using nvidia-smi
            subprocess.check_output(["nvidia-smi"])
            print("NVIDIA GPU detected")
            return "nvidia"
        except:
            # Check for AMD GPU (only works on Linux)
            try:
                output = subprocess.check_output(["lspci"]).decode("utf-8").lower()
                if 'amd' in output or 'radeon' in output:
                    print("AMD GPU detected")
                    return "amd"
                else:
                    print("No compatible GPU detected, will use CPU")
                    return "cpu"
            except:
                print("No compatible GPU detection method found, will use CPU")
                return "cpu"

def main():
    print("Installing dependencies for GPU-accelerated video processing...")
    
    # Basic dependencies
    base_packages = [
        "numpy",
        "pillow",
        "moviepy>=1.0.3",
        "streamlit>=1.22.0",
        "opencv-python>=4.7.0.72",
        "ffmpeg-python>=0.2.0"
    ]
    
    # Install base packages
    for package in base_packages:
        install_package(package, upgrade=True)
    
    # Detect GPU type
    gpu_type = detect_gpu()
    
    # Install PyTorch based on GPU type
    if gpu_type == "nvidia":
        # Install CUDA-enabled PyTorch
        print("Installing PyTorch with CUDA support...")
        install_package("torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
    elif gpu_type == "amd":
        # For AMD, we can use ROCm on Linux, but on Windows we'll use CPU PyTorch
        if platform.system() == "Windows":
            print("Installing PyTorch for Windows (CPU version for AMD compatibility)...")
            install_package("torch torchvision torchaudio")
        else:
            # Linux with AMD GPU
            print("Installing PyTorch with ROCm support for AMD GPU...")
            install_package("torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.4.2")
    else:
        # CPU fallback
        print("Installing PyTorch CPU version...")
        install_package("torch torchvision torchaudio")
    
    # Install multiprocessing modules for parallel processing
    parallel_packages = [
        "tqdm",
        "concurrent-log-handler"
    ]
    for package in parallel_packages:
        install_package(package)
    
    # Ensure ffmpeg is accessible
    if platform.system() == "Windows":
        try:
            subprocess.check_output(["where", "ffmpeg"])
            print("FFmpeg is already installed and accessible.")
        except subprocess.CalledProcessError:
            print("FFmpeg not found in PATH. Please install FFmpeg manually and add it to your PATH.")
            print("You can download FFmpeg from: https://www.gyan.dev/ffmpeg/builds/")
            print("Download the 'ffmpeg-release-essentials.zip' file, extract it, and add the bin folder to your PATH.")
    else:
        try:
            subprocess.check_output(["which", "ffmpeg"])
            print("FFmpeg is already installed and accessible.")
        except subprocess.CalledProcessError:
            print("FFmpeg not found. Attempting to install...")
            if platform.system() == "Darwin":  # macOS
                try:
                    subprocess.check_call(["brew", "install", "ffmpeg"])
                except:
                    print("Failed to install FFmpeg. Please install it manually.")
            else:  # Linux
                try:
                    subprocess.check_call(["sudo", "apt", "update"])
                    subprocess.check_call(["sudo", "apt", "install", "-y", "ffmpeg"])
                except:
                    print("Failed to install FFmpeg. Please install it manually.")
    
    print("\nDependencies installation complete!")
    print("You can now use the GPU-accelerated video editor for faster processing.")

if __name__ == "__main__":
    main() 