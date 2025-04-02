"""
Performance Configuration Module for Video Processing
Optimizes system settings for high-performance video editing
"""

import os
import multiprocessing
import logging
import platform
import subprocess

# Configure logging
logger = logging.getLogger(__name__)

class PerformanceConfig:
    """Manages performance-related settings for the video editor"""
    
    def __init__(self):
        """Initialize performance settings"""
        self.num_cpu_cores = multiprocessing.cpu_count()
        self.optimal_threads = max(4, self.num_cpu_cores - 1)  # Leave one core free for system
        self.gpu_info = self._detect_gpu()
        self.has_cuda = self._has_cuda()
        self.has_mps = self._has_mps()  # Apple Silicon GPU support
        self.ffmpeg_params = self._get_ffmpeg_params()
        self.encoding_preset = self._get_encoding_preset()
        self.codec = self._get_codec()
        
    def _detect_gpu(self):
        """Detect GPU information"""
        gpu_info = {
            'vendor': None,
            'model': None,
            'available': False
        }
        
        try:
            if platform.system() == 'Windows':
                # Get GPU info on Windows
                output = subprocess.check_output(
                    "powershell -Command \"Get-WmiObject Win32_VideoController | Format-List Name, AdapterCompatibility\"", 
                    shell=True
                ).decode('utf-8').lower()
                
                logger.debug(f"GPU detection output: {output}")
                
                if 'nvidia' in output:
                    gpu_info['vendor'] = 'nvidia'
                    gpu_info['available'] = True
                    # Try to get more detailed info
                    try:
                        model_info = output
                        # Extract model name from the output
                        for line in model_info.split('\n'):
                            if line.strip().startswith('name'):
                                gpu_info['model'] = line.split(':')[1].strip()
                                break
                    except Exception as e:
                        logger.warning(f"Error getting NVIDIA GPU model: {e}")
                    
                elif any(gpu in output for gpu in ['amd', 'radeon', 'ati', 'advanced micro devices']):
                    gpu_info['vendor'] = 'amd'
                    gpu_info['available'] = True
                    # Try to get model info
                    try:
                        model_info = output
                        # Extract model name from the output
                        for line in model_info.split('\n'):
                            if line.strip().startswith('name'):
                                gpu_info['model'] = line.split(':')[1].strip()
                                break
                    except Exception as e:
                        logger.warning(f"Error getting AMD GPU model: {e}")
            else:
                # Unix-based systems
                try:
                    # Check for NVIDIA GPU
                    nvidia_info = subprocess.check_output(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader']).decode('utf-8').strip()
                    if nvidia_info:
                        gpu_info['vendor'] = 'nvidia'
                        gpu_info['model'] = nvidia_info
                        gpu_info['available'] = True
                except:
                    # Check for AMD GPU on Linux
                    try:
                        output = subprocess.check_output(['lspci']).decode('utf-8').lower()
                        if 'amd' in output or 'radeon' in output:
                            gpu_info['vendor'] = 'amd'
                            gpu_info['available'] = True
                            # Try to extract model name
                            for line in output.split('\n'):
                                if 'amd' in line or 'radeon' in line:
                                    gpu_info['model'] = line.split(':')[-1].strip()
                                    break
                    except:
                        # Check for Apple Silicon
                        if platform.system() == 'Darwin' and platform.machine() == 'arm64':
                            gpu_info['vendor'] = 'apple'
                            gpu_info['model'] = 'Apple Silicon'
                            gpu_info['available'] = True
        except Exception as e:
            logger.warning(f"Error detecting GPU: {str(e)}")
        
        return gpu_info

    def _has_cuda(self):
        """Check if CUDA is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def _has_mps(self):
        """Check if Apple MPS (Metal Performance Shaders) is available"""
        try:
            import torch
            return hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
        except ImportError:
            return False

    def _get_ffmpeg_params(self):
        """Get optimal ffmpeg parameters based on detected hardware"""
        params = []
        
        if not self.gpu_info['available']:
            return params
        
        # Windows-specific parameters
        if platform.system() == 'Windows':
            if self.gpu_info['vendor'] == 'nvidia':
                # For NVIDIA, apply both input and output acceleration
                params = ['-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda']
            elif self.gpu_info['vendor'] == 'amd':
                # For AMD on Windows, use D3D11VA hardware acceleration
                params = ['-hwaccel', 'dxva2']
        
        # Linux-specific parameters
        elif platform.system() == 'Linux':
            if self.gpu_info['vendor'] == 'nvidia':
                params = ['-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda']
            elif self.gpu_info['vendor'] == 'amd':
                # For AMD on Linux, we'll use environment variables instead
                # This is handled in get_moviepy_params
                params = []
        
        # macOS-specific parameters
        elif platform.system() == 'Darwin':
            params = ['-hwaccel', 'videotoolbox']
        
        return params

    def _get_encoding_preset(self):
        """Get optimal encoding preset based on hardware"""
        # Options: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
        if self.gpu_info['available']:
            return "fast"  # Good balance with GPU acceleration
        else:
            # Without GPU, use faster preset to compensate
            return "veryfast"
    
    def _get_codec(self):
        """Get optimal video codec based on hardware"""
        if not self.gpu_info['available']:
            return 'libx264'  # Default CPU codec
        
        if platform.system() == 'Windows':
            if self.gpu_info['vendor'] == 'nvidia':
                return 'h264_nvenc'
            elif self.gpu_info['vendor'] == 'amd':
                # Try to use AMD hardware encoding with h264_amf
                try:
                    # Check if h264_amf is available by running a test command
                    subprocess.check_output(['ffmpeg', '-encoders'], stderr=subprocess.STDOUT).decode('utf-8')
                    if 'h264_amf' in subprocess.check_output(['ffmpeg', '-encoders'], stderr=subprocess.STDOUT).decode('utf-8'):
                        logger.info("Using AMD h264_amf encoder")
                        return 'h264_amf'
                    else:
                        logger.info("AMD h264_amf encoder not available, falling back to libx264")
                        return 'libx264'
                except:
                    # If any error occurs, fall back to CPU encoding
                    logger.info("Error checking for AMD encoder, falling back to libx264")
                    return 'libx264'
        
        # Linux with NVIDIA
        elif platform.system() == 'Linux' and self.gpu_info['vendor'] == 'nvidia':
            return 'h264_nvenc'
        
        # Default to CPU encoding for other cases
        return 'libx264'
    
    def get_moviepy_params(self):
        """Get optimal parameters for MoviePy video writing"""
        params = {
            'codec': self.codec,
            'audio_codec': 'aac',
            'threads': self.optimal_threads,
            'preset': self.encoding_preset,
            'ffmpeg_params': self.ffmpeg_params if self.ffmpeg_params else None,
            'verbose': False
        }
        
        # For AMD GPUs on Windows, enable hardware acceleration
        if self.gpu_info['available'] and self.gpu_info['vendor'] == 'amd' and platform.system() == 'Windows':
            # Use AMD-specific parameters
            logger.info("Configuring AMD GPU acceleration for video processing")
            
            # If codec is h264_amf, add specific settings
            if self.codec == 'h264_amf':
                # Additional FFmpeg parameters for AMD encoding
                if params['ffmpeg_params'] is None:
                    params['ffmpeg_params'] = []
                
                # Add AMD-specific encoding parameters
                params['ffmpeg_params'].extend([
                    '-quality', 'speed',  # Optimize for speed
                    '-rc', 'vbr_latency',  # Variable bitrate for better quality
                    '-usage', 'ultralowlatency'  # Better for video processing
                ])
            
            # Set environment variables for MoviePy to use
            os.environ['MOVIEPY_FFMPEG_OPTS'] = '-hwaccel dxva2'
        
        # For other AMD GPUs, we'll set environment variables instead of using input_params
        elif self.gpu_info['available'] and self.gpu_info['vendor'] == 'amd':
            # Set environment variables that will be picked up by ffmpeg
            if platform.system() == 'Linux':
                os.environ['MOVIEPY_FFMPEG_OPTS'] = '-hwaccel vaapi -vaapi_device /dev/dri/renderD128'
        
        return params
    
    def get_temp_folder(self):
        """Get optimal temporary folder location"""
        # Use RAM disk if available for temporary files (much faster)
        if platform.system() == 'Windows':
            ram_disk = None
            for drive in range(ord('Z'), ord('A'), -1):
                drive_letter = chr(drive) + ':'
                if os.path.exists(drive_letter):
                    try:
                        # Check if this is a RAM disk by writing a temp file
                        test_file = os.path.join(drive_letter, 'temp_test.txt')
                        with open(test_file, 'w') as f:
                            f.write('test')
                        os.remove(test_file)
                        ram_disk = drive_letter
                        break
                    except:
                        continue
            
            if ram_disk:
                temp_folder = os.path.join(ram_disk, 'temp_video_processing')
                os.makedirs(temp_folder, exist_ok=True)
                return temp_folder
        
        # Fallback to regular temp directory
        import tempfile
        temp_dir = os.path.join(tempfile.gettempdir(), 'video_processing')
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir
    
    def print_system_info(self):
        """Print system information for debugging"""
        print("\n=== System Performance Configuration ===")
        print(f"CPU Cores: {self.num_cpu_cores}")
        print(f"Optimal Thread Count: {self.optimal_threads}")
        print(f"GPU Vendor: {self.gpu_info['vendor'] or 'None'}")
        print(f"GPU Model: {self.gpu_info['model'] or 'None'}")
        print(f"CUDA Available: {self.has_cuda}")
        print(f"Apple MPS Available: {self.has_mps}")
        print(f"Video Codec: {self.codec}")
        print(f"Encoding Preset: {self.encoding_preset}")
        print(f"FFmpeg Parameters: {self.ffmpeg_params}")
        print("=======================================\n")

# Create a singleton instance for global use
performance_config = PerformanceConfig()

def get_performance_config():
    """Get the performance configuration singleton"""
    return performance_config

def init_performance_settings():
    """Initialize performance settings and return the config"""
    config = get_performance_config()
    # Set environment variables to optimize performance
    if config.gpu_info['available']:
        # Set environment variables for better GPU utilization
        if config.gpu_info['vendor'] == 'nvidia':
            os.environ['CUDA_VISIBLE_DEVICES'] = '0'  # Use the first GPU
            try:
                import torch
                torch.backends.cudnn.benchmark = True  # Use cuDNN auto-tuner
            except ImportError:
                pass
        elif config.gpu_info['vendor'] == 'amd':
            # Set AMD-specific environment variables for FFMPEG
            if platform.system() == 'Windows':
                # Use DirectX hardware acceleration for AMD GPUs on Windows
                os.environ['MOVIEPY_FFMPEG_OPTS'] = '-hwaccel dxva2'
                
                # Set OpenCL environment variables if PyTorch is used
                try:
                    import torch
                    # If torch is installed, prefer OpenCL on AMD
                    os.environ['PYTORCH_USE_OPENCL'] = '1'
                except ImportError:
                    pass
                
                # Additional AMD specific optimizations
                # Enable hardware encoding with AMF
                os.environ['AMF_ENABLE_HARDWARE_ENCODING'] = '1'
            elif platform.system() == 'Linux':
                os.environ['MOVIEPY_FFMPEG_OPTS'] = '-hwaccel vaapi -vaapi_device /dev/dri/renderD128'
    
    # Configure temp directory for fast I/O
    temp_dir = config.get_temp_folder()
    os.environ['TMPDIR'] = temp_dir
    os.environ['TEMP'] = temp_dir
    os.environ['TMP'] = temp_dir
    
    # Print debug information
    if os.environ.get('DEBUG', '0') == '1':
        config.print_system_info()
    
    return config

# Initialize on import
init_performance_settings() 