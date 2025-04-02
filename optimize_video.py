"""
Video Editor Optimization Tool
Installs dependencies and optimizes video processing using GPU acceleration
"""

import os
import sys
import subprocess
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import torch
        import numpy
        import moviepy.editor
        import concurrent.futures
        return True
    except ImportError as e:
        logger.warning(f"Missing dependency: {str(e)}")
        return False

def install_dependencies():
    """Install required dependencies"""
    logger.info("Installing dependencies...")
    install_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "install_dependencies.py")
    if os.path.exists(install_script):
        subprocess.call([sys.executable, install_script])
    else:
        logger.error("Could not find install_dependencies.py")
        return False
    return True

def run_benchmark(video_path, audio_path, captions_path, mode="all"):
    """Run benchmark to compare performance"""
    logger.info(f"Running benchmark in mode: {mode}")
    benchmark_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "benchmark.py")
    if os.path.exists(benchmark_script):
        cmd = [
            sys.executable, benchmark_script,
            "--video", video_path,
            "--audio", audio_path,
            "--captions", captions_path,
            "--mode", mode
        ]
        subprocess.call(cmd)
    else:
        logger.error("Could not find benchmark.py")
        return False
    return True

def process_video(video_path, audio_path, captions_path, output_path, use_gpu=True, batch_processing=False, batch_size=4):
    """Process a video with optimized settings"""
    logger.info(f"Processing video with GPU acceleration: {use_gpu}")
    
    try:
        # Import required modules
        from src.performance_config import get_performance_config
        
        if batch_processing:
            # Use batch processing
            from src.batch_processor import BatchProcessor, create_job
            
            # Create batch processor
            processor = BatchProcessor(max_workers=batch_size)
            
            # Create a single job
            job = create_job(
                video_path,
                audio_path,
                captions_path,
                output_path,
                job_id="optimize_video",
                theme="default",
                add_music=True,
                add_intro=True,
                add_outro=True
            )
            
            # Process the job
            results = processor.process_batch([job])
            
            # Check results
            if results and results[0]['status'] == 'success':
                logger.info(f"Video processed successfully: {results[0]['result_file']}")
                logger.info(f"Processing time: {results[0]['elapsed_time']:.2f} seconds")
                return True
            else:
                logger.error(f"Error processing video: {results[0]['error'] if results else 'Unknown error'}")
                return False
            
        else:
            # Use direct processing
            from src.video_editor import create_final_video
            
            # Set environment variables for GPU/CPU mode
            if not use_gpu:
                os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
                os.environ['CPU_ONLY'] = '1'
            else:
                os.environ['CUDA_VISIBLE_DEVICES'] = '0'
                os.environ['CPU_ONLY'] = '0'
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Process the video
            result = create_final_video(
                video_path,
                audio_path,
                captions_path,
                output_path,
                theme="default",
                add_music=True,
                add_intro=True,
                add_outro=True
            )
            
            if result:
                logger.info(f"Video processed successfully: {result}")
                return True
            else:
                logger.error("Error processing video")
                return False
    
    except ImportError as e:
        logger.error(f"Error importing required modules: {str(e)}")
        logger.error("Make sure dependencies are installed correctly")
        return False
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        return False

def process_directory(input_dir, output_dir, use_gpu=True, batch_size=4):
    """Process all videos in a directory"""
    logger.info(f"Processing directory: {input_dir}")
    
    try:
        # Import required modules
        from src.batch_processor import process_directory
        
        # Set environment variables for GPU/CPU mode
        if not use_gpu:
            os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
            os.environ['CPU_ONLY'] = '1'
        else:
            os.environ['CUDA_VISIBLE_DEVICES'] = '0'
            os.environ['CPU_ONLY'] = '0'
        
        # Process the directory
        results = process_directory(
            input_dir,
            output_dir,
            theme="default",
            add_music=True,
            add_intro=True,
            add_outro=True
        )
        
        # Check results
        if results:
            successful = sum(1 for r in results if r['status'] == 'success')
            failed = sum(1 for r in results if r['status'] == 'error')
            
            logger.info(f"Processed {len(results)} videos: {successful} successful, {failed} failed")
            return True
        else:
            logger.warning("No videos found for processing")
            return False
    
    except ImportError as e:
        logger.error(f"Error importing required modules: {str(e)}")
        logger.error("Make sure dependencies are installed correctly")
        return False
    except Exception as e:
        logger.error(f"Error processing directory: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Optimize video processing with GPU acceleration")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Install dependencies command
    install_parser = subparsers.add_parser("install", help="Install required dependencies")
    
    # Benchmark command
    benchmark_parser = subparsers.add_parser("benchmark", help="Run performance benchmark")
    benchmark_parser.add_argument("--video", required=True, help="Path to background video file")
    benchmark_parser.add_argument("--audio", required=True, help="Path to audio file")
    benchmark_parser.add_argument("--captions", required=True, help="Path to captions JSON file")
    benchmark_parser.add_argument("--mode", choices=["all", "cpu", "gpu", "batch"], default="all", 
                          help="Benchmark mode (default: all)")
    
    # Process single video command
    process_parser = subparsers.add_parser("process", help="Process a single video")
    process_parser.add_argument("--video", required=True, help="Path to background video file")
    process_parser.add_argument("--audio", required=True, help="Path to audio file")
    process_parser.add_argument("--captions", required=True, help="Path to captions JSON file")
    process_parser.add_argument("--output", required=True, help="Path to save the output video")
    process_parser.add_argument("--cpu", action="store_true", help="Use CPU-only mode")
    process_parser.add_argument("--batch", action="store_true", help="Use batch processing")
    
    # Process directory command
    dir_parser = subparsers.add_parser("process-dir", help="Process all videos in a directory")
    dir_parser.add_argument("--input", required=True, help="Input directory with videos, audio, and captions")
    dir_parser.add_argument("--output", required=True, help="Output directory for processed videos")
    dir_parser.add_argument("--cpu", action="store_true", help="Use CPU-only mode")
    
    args = parser.parse_args()
    
    # Handle commands
    if args.command == "install":
        # Install dependencies
        if not check_dependencies():
            if not install_dependencies():
                logger.error("Failed to install dependencies")
                return 1
        else:
            logger.info("All dependencies already installed")
    
    elif args.command == "benchmark":
        # Make sure dependencies are installed
        if not check_dependencies():
            logger.warning("Missing dependencies, installing...")
            if not install_dependencies():
                logger.error("Failed to install dependencies")
                return 1
        
        # Run benchmark
        if not run_benchmark(args.video, args.audio, args.captions, args.mode):
            logger.error("Benchmark failed")
            return 1
    
    elif args.command == "process":
        # Make sure dependencies are installed
        if not check_dependencies():
            logger.warning("Missing dependencies, installing...")
            if not install_dependencies():
                logger.error("Failed to install dependencies")
                return 1
        
        # Process video
        if not process_video(args.video, args.audio, args.captions, args.output, not args.cpu, args.batch):
            logger.error("Video processing failed")
            return 1
    
    elif args.command == "process-dir":
        # Make sure dependencies are installed
        if not check_dependencies():
            logger.warning("Missing dependencies, installing...")
            if not install_dependencies():
                logger.error("Failed to install dependencies")
                return 1
        
        # Process directory
        if not process_directory(args.input, args.output, not args.cpu):
            logger.error("Directory processing failed")
            return 1
    
    else:
        # No command specified, show help
        parser.print_help()
    
    return 0

if __name__ == "__main__":
    exit(main()) 