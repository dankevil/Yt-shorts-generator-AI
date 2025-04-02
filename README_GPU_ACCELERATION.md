# GPU Acceleration for Video Processing

This document explains how to set up and use GPU acceleration for faster video processing in this project, with a special focus on AMD GPUs on Windows.

## Supported GPU Types

The project supports the following GPU technologies:

- **NVIDIA GPUs** (using CUDA acceleration)
- **AMD GPUs** (using DirectX/DXVA2 acceleration on Windows, VA-API on Linux)
- **Intel GPUs** (using QuickSync)
- **Apple Silicon** (using Metal/VideoToolbox)

## AMD GPU Support on Windows

AMD GPUs on Windows can accelerate video processing through DirectX Video Acceleration (DXVA2) and AMD's Media Foundation (AMF) for encoding. Follow these steps to set up AMD GPU acceleration:

### Automated Setup (Recommended)

1. Run the AMD GPU setup script with administrator privileges:

```
python -m src.setup_amd_acceleration
```

2. This script will:
   - Check for and help you install the latest AMD drivers
   - Install FFmpeg with AMD AMF encoder support if needed
   - Configure environment variables for GPU acceleration
   - Update the project configuration for AMD GPU

3. Restart your computer after the setup completes

### Manual Setup

If you prefer to set up AMD GPU acceleration manually:

1. **Install Latest AMD Drivers**
   - Download and install the latest drivers from [AMD's website](https://www.amd.com/en/support)
   - Make sure the AMD Media Foundation (AMF) components are installed

2. **Install FFmpeg with AMD Support**
   - Download FFmpeg with AMF support from [BtbN's FFmpeg Builds](https://github.com/BtbN/FFmpeg-Builds/releases)
   - Extract and add to your system PATH

3. **Set Required Environment Variables**
   - Set `AMF_ENABLE_HARDWARE_ENCODING=1` in your system environment variables
   - Set `MOVIEPY_FFMPEG_OPTS=-hwaccel dxva2` in your system environment variables

## Verifying GPU Acceleration

To verify that your GPU acceleration is working properly:

```
python -m src.check_gpu_acceleration
```

This will check:
- If your GPU is properly detected
- If the necessary hardware acceleration methods are available
- If the AMD AMF encoder is available (for AMD GPUs)
- If the environment variables are properly set

## Troubleshooting AMD GPU Issues

If you're having issues with AMD GPU acceleration:

1. **Check Your Drivers**
   - Make sure you have the latest AMD drivers installed
   - Reinstall your drivers if necessary

2. **Verify FFmpeg Installation**
   - Run `ffmpeg -encoders | findstr amf` to check for AMD AMF encoder
   - Run `ffmpeg -hwaccels` to check for available hardware acceleration methods
   - If DXVA2 or D3D11VA isn't listed, your FFmpeg build doesn't support them

3. **Check DirectX Diagnostics**
   - Run `dxdiag` from the Run dialog
   - Check that DirectX is up to date and that hardware acceleration is enabled

4. **Common Error Messages**
   - "Cannot initialize AMD encoder" - AMF encoders not properly installed
   - "Cannot find AMD encoder" - h264_amf not available in your FFmpeg build
   - "No compatible AMD hardware" - Your AMD GPU may be too old to support AMF

## Performance Considerations

- AMD GPU acceleration is most effective for decoding (reading) video files
- Encoding (writing) performance varies by AMD GPU model
- Newer AMD GPUs (RX 5000 series and newer) provide better encoding performance
- For best performance, use MP4 or MOV output with h264 codec

## Advanced Configuration

Advanced users can customize the AMD GPU acceleration settings by modifying:

- `src/performance_config.py` - Adjust AMF encoder settings
- AMD environment variables - For more control over GPU usage

## Additional Resources

- [AMD Video Core Next Encoder](https://www.amd.com/en/technologies/vcn)
- [FFmpeg AMD AMF Documentation](https://trac.ffmpeg.org/wiki/Hardware/AMD)
- [DirectX Video Acceleration](https://en.wikipedia.org/wiki/DirectX_Video_Acceleration) 