"""
Benchmarking tool for video processing
Compares performance between CPU-only and GPU-accelerated processing
"""

import os
import time
import logging
import argparse
import tempfile
import shutil
import json
from datetime import datetime
from tabulate import tabulate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import after logging configuration
try:
    from src.performance_config import get_performance_config, init_performance_settings
    from src.video_editor import create_final_video
    from src.batch_processor import BatchProcessor, create_job
except ImportError as e:
    logger.error(f"Error importing required modules: {str(e)}")
    logger.error("Make sure you're running this script from the project root directory")
    exit(1)

def run_single_video_benchmark(video_path, audio_path, captions_path, use_gpu=True):
    """Run a benchmark for a single video
    
    Args:
        video_path (str): Path to the background video
        audio_path (str): Path to the audio file
        captions_path (str): Path to the captions file
        use_gpu (bool): Whether to use GPU acceleration
    
    Returns:
        dict: Benchmark results
    """
    # Create temporary output directory
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, "benchmark_output.mp4")
    
    # Configure environment for CPU or GPU
    if not use_gpu:
        # Force CPU-only mode
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
        os.environ['CPU_ONLY'] = '1'
    else:
        # Enable GPU if available
        os.environ['CUDA_VISIBLE_DEVICES'] = '0'
        os.environ['CPU_ONLY'] = '0'
    
    # Reinitialize performance settings
    perf_config = init_performance_settings()
    
    # Log the configuration
    logger.info(f"Running benchmark with GPU: {use_gpu}")
    logger.info(f"GPU available: {perf_config.gpu_info['available']}")
    if perf_config.gpu_info['available']:
        logger.info(f"GPU model: {perf_config.gpu_info['model'] or perf_config.gpu_info['vendor']}")
        logger.info(f"Using codec: {perf_config.codec}")
    
    # Run the benchmark
    start_time = time.time()
    
    try:
        create_final_video(
            video_path,
            audio_path,
            captions_path,
            output_path,
            theme="default",
            add_music=False,
            add_intro=True,
            add_outro=True
        )
        
        # Calculate statistics
        end_time = time.time()
        duration = end_time - start_time
        
        # Get output file size
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # Size in MB
        
        # Get video duration
        from moviepy.editor import VideoFileClip
        video = VideoFileClip(output_path)
        video_duration = video.duration
        video.close()
        
        # Calculate processing ratio (processing time / video duration)
        processing_ratio = duration / video_duration
        
        # Return results
        result = {
            "success": True,
            "gpu_used": use_gpu,
            "gpu_available": perf_config.gpu_info['available'],
            "gpu_model": perf_config.gpu_info.get('model', None) or perf_config.gpu_info.get('vendor', None),
            "duration_seconds": duration,
            "file_size_mb": file_size,
            "video_duration_seconds": video_duration,
            "processing_ratio": processing_ratio,
            "output_path": output_path
        }
    
    except Exception as e:
        logger.error(f"Error during benchmark: {str(e)}")
        result = {
            "success": False,
            "gpu_used": use_gpu,
            "error": str(e),
            "duration_seconds": time.time() - start_time
        }
    
    return result, temp_dir

def run_batch_benchmark(video_path, audio_path, captions_path, batch_size=4, use_gpu=True):
    """Run a benchmark for batch processing
    
    Args:
        video_path (str): Path to the background video
        audio_path (str): Path to the audio file
        captions_path (str): Path to the captions file
        batch_size (int): Number of videos to process in parallel
        use_gpu (bool): Whether to use GPU acceleration
    
    Returns:
        dict: Benchmark results
    """
    # Create temporary output directory
    temp_dir = tempfile.mkdtemp()
    
    # Configure environment for CPU or GPU
    if not use_gpu:
        # Force CPU-only mode
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
        os.environ['CPU_ONLY'] = '1'
    else:
        # Enable GPU if available
        os.environ['CUDA_VISIBLE_DEVICES'] = '0'
        os.environ['CPU_ONLY'] = '0'
    
    # Reinitialize performance settings
    perf_config = init_performance_settings()
    
    # Create batch processor with specified workers
    processor = BatchProcessor(max_workers=batch_size)
    
    # Create jobs
    jobs = []
    for i in range(batch_size):
        output_path = os.path.join(temp_dir, f"batch_output_{i}.mp4")
        job = create_job(
            video_path,
            audio_path,
            captions_path,
            output_path,
            job_id=f"batch_{i}",
            theme="default",
            add_music=False,
            add_intro=True,
            add_outro=True
        )
        jobs.append(job)
    
    # Run the benchmark
    start_time = time.time()
    
    try:
        results = processor.process_batch(jobs)
        
        # Calculate statistics
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Calculate average job duration
        successful_jobs = [r for r in results if r['status'] == 'success']
        if successful_jobs:
            avg_job_duration = sum(r['elapsed_time'] for r in successful_jobs) / len(successful_jobs)
        else:
            avg_job_duration = 0
        
        # Calculate speedup factor
        if len(successful_jobs) > 0:
            speedup = (avg_job_duration * len(successful_jobs)) / total_duration
        else:
            speedup = 0
        
        # Get video duration (use the first successful job)
        video_duration = 0
        if successful_jobs:
            from moviepy.editor import VideoFileClip
            video = VideoFileClip(successful_jobs[0]['result_file'])
            video_duration = video.duration
            video.close()
        
        # Return results
        result = {
            "success": True,
            "gpu_used": use_gpu,
            "gpu_available": perf_config.gpu_info['available'],
            "gpu_model": perf_config.gpu_info.get('model', None) or perf_config.gpu_info.get('vendor', None),
            "batch_size": batch_size,
            "total_duration_seconds": total_duration,
            "avg_job_duration_seconds": avg_job_duration,
            "speedup_factor": speedup,
            "successful_jobs": len(successful_jobs),
            "failed_jobs": len(results) - len(successful_jobs),
            "video_duration_seconds": video_duration
        }
    
    except Exception as e:
        logger.error(f"Error during batch benchmark: {str(e)}")
        result = {
            "success": False,
            "gpu_used": use_gpu,
            "error": str(e),
            "batch_size": batch_size,
            "duration_seconds": time.time() - start_time
        }
    
    return result, temp_dir

def run_comprehensive_benchmark(video_path, audio_path, captions_path):
    """Run a comprehensive benchmark comparing CPU and GPU performance
    
    Args:
        video_path (str): Path to the background video
        audio_path (str): Path to the audio file
        captions_path (str): Path to the captions file
    """
    results = []
    temp_dirs = []
    
    try:
        # Single video processing - CPU
        logger.info("Running single video benchmark (CPU)...")
        cpu_result, cpu_temp = run_single_video_benchmark(
            video_path, audio_path, captions_path, use_gpu=False
        )
        temp_dirs.append(cpu_temp)
        results.append(cpu_result)
        
        # Single video processing - GPU
        logger.info("Running single video benchmark (GPU)...")
        gpu_result, gpu_temp = run_single_video_benchmark(
            video_path, audio_path, captions_path, use_gpu=True
        )
        temp_dirs.append(gpu_temp)
        results.append(gpu_result)
        
        # Batch processing - CPU (4 videos)
        logger.info("Running batch processing benchmark (CPU, 4 videos)...")
        cpu_batch_result, cpu_batch_temp = run_batch_benchmark(
            video_path, audio_path, captions_path, batch_size=4, use_gpu=False
        )
        temp_dirs.append(cpu_batch_temp)
        results.append(cpu_batch_result)
        
        # Batch processing - GPU (4 videos)
        logger.info("Running batch processing benchmark (GPU, 4 videos)...")
        gpu_batch_result, gpu_batch_temp = run_batch_benchmark(
            video_path, audio_path, captions_path, batch_size=4, use_gpu=True
        )
        temp_dirs.append(gpu_batch_temp)
        results.append(gpu_batch_result)
        
        # Create report
        print_benchmark_report(results)
        
        # Save results to file
        save_benchmark_results(results)
    
    finally:
        # Clean up temporary directories
        for temp_dir in temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Error cleaning up temp directory: {str(e)}")

def print_benchmark_report(results):
    """Print a formatted benchmark report
    
    Args:
        results (list): List of benchmark results
    """
    print("\n" + "="*80)
    print(" "*30 + "BENCHMARK RESULTS")
    print("="*80 + "\n")
    
    # Filter out failed benchmarks
    successful_results = [r for r in results if r.get("success", False)]
    
    # Single video comparisons
    single_results = [r for r in successful_results if "batch_size" not in r]
    if len(single_results) >= 2:
        cpu_result = next((r for r in single_results if not r["gpu_used"]), None)
        gpu_result = next((r for r in single_results if r["gpu_used"]), None)
        
        if cpu_result and gpu_result:
            speedup = cpu_result["duration_seconds"] / gpu_result["duration_seconds"]
            
            print("SINGLE VIDEO PROCESSING COMPARISON:")
            table_data = [
                ["", "CPU", "GPU", "Speedup"],
                ["Processing Time (sec)", f"{cpu_result['duration_seconds']:.2f}", f"{gpu_result['duration_seconds']:.2f}", f"{speedup:.2f}x"],
                ["Processing Ratio", f"{cpu_result['processing_ratio']:.2f}", f"{gpu_result['processing_ratio']:.2f}", ""],
                ["File Size (MB)", f"{cpu_result['file_size_mb']:.2f}", f"{gpu_result['file_size_mb']:.2f}", ""]
            ]
            print(tabulate(table_data, headers="firstrow", tablefmt="grid"))
            print("")
    
    # Batch processing comparisons
    batch_results = [r for r in successful_results if "batch_size" in r]
    if len(batch_results) >= 2:
        cpu_batch = next((r for r in batch_results if not r["gpu_used"]), None)
        gpu_batch = next((r for r in batch_results if r["gpu_used"]), None)
        
        if cpu_batch and gpu_batch:
            batch_speedup = cpu_batch["total_duration_seconds"] / gpu_batch["total_duration_seconds"]
            
            print("BATCH PROCESSING COMPARISON:")
            table_data = [
                ["", "CPU", "GPU", "Speedup"],
                ["Total Processing Time (sec)", f"{cpu_batch['total_duration_seconds']:.2f}", f"{gpu_batch['total_duration_seconds']:.2f}", f"{batch_speedup:.2f}x"],
                ["Avg Job Duration (sec)", f"{cpu_batch['avg_job_duration_seconds']:.2f}", f"{gpu_batch['avg_job_duration_seconds']:.2f}", ""],
                ["Batch Size", f"{cpu_batch['batch_size']}", f"{gpu_batch['batch_size']}", ""],
                ["Successful Jobs", f"{cpu_batch['successful_jobs']}", f"{gpu_batch['successful_jobs']}", ""]
            ]
            print(tabulate(table_data, headers="firstrow", tablefmt="grid"))
    
    # Hardware info
    gpu_info = None
    for r in successful_results:
        if r["gpu_available"]:
            gpu_info = r["gpu_model"]
            break
    
    print("\nHARDWARE INFORMATION:")
    if gpu_info:
        print(f"GPU: {gpu_info}")
    else:
        print("No compatible GPU detected")
    
    print("\n" + "="*80 + "\n")

def save_benchmark_results(results):
    """Save benchmark results to a JSON file
    
    Args:
        results (list): List of benchmark results
    """
    # Create results directory
    results_dir = "benchmark_results"
    os.makedirs(results_dir, exist_ok=True)
    
    # Create unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(results_dir, f"benchmark_{timestamp}.json")
    
    # Save results
    with open(filename, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "results": results
        }, f, indent=2)
    
    logger.info(f"Benchmark results saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description="Benchmark video processing performance")
    parser.add_argument("--video", required=True, help="Path to background video file")
    parser.add_argument("--audio", required=True, help="Path to audio file")
    parser.add_argument("--captions", required=True, help="Path to captions JSON file")
    parser.add_argument("--mode", choices=["all", "cpu", "gpu", "batch"], default="all", 
                        help="Benchmark mode (default: all)")
    parser.add_argument("--batch-size", type=int, default=4, 
                        help="Batch size for batch processing (default: 4)")
    
    args = parser.parse_args()
    
    # Verify input files exist
    for path, name in [(args.video, "Video"), (args.audio, "Audio"), (args.captions, "Captions")]:
        if not os.path.exists(path):
            logger.error(f"{name} file not found: {path}")
            return 1
    
    # Run appropriate benchmark
    if args.mode == "all":
        run_comprehensive_benchmark(args.video, args.audio, args.captions)
    elif args.mode == "cpu":
        result, temp_dir = run_single_video_benchmark(args.video, args.audio, args.captions, use_gpu=False)
        print_benchmark_report([result])
        shutil.rmtree(temp_dir)
    elif args.mode == "gpu":
        result, temp_dir = run_single_video_benchmark(args.video, args.audio, args.captions, use_gpu=True)
        print_benchmark_report([result])
        shutil.rmtree(temp_dir)
    elif args.mode == "batch":
        result, temp_dir = run_batch_benchmark(
            args.video, args.audio, args.captions, batch_size=args.batch_size, use_gpu=True
        )
        print_benchmark_report([result])
        shutil.rmtree(temp_dir)
    
    return 0

if __name__ == "__main__":
    exit(main()) 