"""
Batch Processor Module
Processes multiple videos in parallel using multiprocessing pools and GPU acceleration
"""

import os
import time
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm

from .video_editor import create_final_video
from .performance_config import get_performance_config

# Configure logging
logger = logging.getLogger(__name__)

# Get performance configuration
perf_config = get_performance_config()

class BatchProcessor:
    """
    Processes multiple videos in parallel for maximum efficiency
    """
    
    def __init__(self, max_workers=None):
        """Initialize the batch processor
        
        Args:
            max_workers (int, optional): Maximum number of worker processes to use.
                                         If None, will use optimal number based on CPU cores.
        """
        if max_workers is None:
            # Leave at least 1 core free for system tasks
            self.max_workers = max(1, perf_config.num_cpu_cores - 1)
            
            # If using GPU, limit workers to avoid memory issues
            if perf_config.gpu_info['available']:
                # For GPU processing, typically 2-4 workers is optimal to avoid memory contention
                self.max_workers = min(self.max_workers, 4)
        else:
            self.max_workers = max_workers
        
        logger.info(f"Batch processor initialized with {self.max_workers} worker processes")
    
    def process_video_job(self, job):
        """Process a single video job
        
        Args:
            job (dict): Dictionary containing job parameters
            
        Returns:
            dict: Job result dictionary
        """
        start_time = time.time()
        job_id = job.get('job_id', 'unknown')
        
        try:
            # Extract job parameters
            background_video = job['background_video']
            audio_file = job['audio_file']
            captions_file = job['captions_file']
            output_file = job['output_file']
            theme = job.get('theme', 'default')
            add_music = job.get('add_music', False)
            add_intro = job.get('add_intro', False)
            add_outro = job.get('add_outro', True)
            
            # Create the video
            result_file = create_final_video(
                background_video, 
                audio_file, 
                captions_file, 
                output_file,
                theme=theme,
                add_music=add_music,
                add_intro=add_intro,
                add_outro=add_outro
            )
            
            # Calculate processing time
            elapsed = time.time() - start_time
            
            # Return job result
            return {
                'job_id': job_id,
                'status': 'success',
                'result_file': result_file,
                'elapsed_time': elapsed,
                'error': None
            }
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error processing job {job_id}: {str(e)}")
            return {
                'job_id': job_id,
                'status': 'error',
                'result_file': None,
                'elapsed_time': elapsed,
                'error': str(e)
            }
    
    def process_batch(self, jobs, show_progress=True):
        """Process a batch of video jobs in parallel
        
        Args:
            jobs (list): List of job dictionaries with parameters for each video
            show_progress (bool, optional): Whether to show a progress bar
            
        Returns:
            list: List of result dictionaries
        """
        if not jobs:
            logger.warning("No jobs provided to process")
            return []
        
        num_jobs = len(jobs)
        logger.info(f"Processing {num_jobs} jobs with {self.max_workers} workers")
        
        # Initialize progress bar if requested
        pbar = None
        if show_progress:
            pbar = tqdm(total=num_jobs, desc="Processing videos")
        
        results = []
        
        # Process jobs in parallel
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all jobs
            future_to_job = {executor.submit(self.process_video_job, job): job for job in jobs}
            
            # Process results as they complete
            for future in as_completed(future_to_job):
                job = future_to_job[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Log result
                    job_id = job.get('job_id', 'unknown')
                    if result['status'] == 'success':
                        logger.info(f"Job {job_id} completed successfully in {result['elapsed_time']:.2f} seconds")
                    else:
                        logger.error(f"Job {job_id} failed: {result['error']}")
                    
                    # Update progress bar
                    if pbar:
                        pbar.update(1)
                        
                except Exception as e:
                    job_id = job.get('job_id', 'unknown')
                    logger.error(f"Exception in job {job_id}: {str(e)}")
                    results.append({
                        'job_id': job_id,
                        'status': 'error',
                        'result_file': None,
                        'elapsed_time': 0,
                        'error': str(e)
                    })
                    if pbar:
                        pbar.update(1)
        
        # Close progress bar
        if pbar:
            pbar.close()
        
        # Log final stats
        successful_jobs = sum(1 for r in results if r['status'] == 'success')
        failed_jobs = sum(1 for r in results if r['status'] == 'error')
        logger.info(f"Batch processing completed: {successful_jobs} succeeded, {failed_jobs} failed")
        
        return results

def create_job(background_video, audio_file, captions_file, output_file, 
               job_id=None, theme='default', add_music=False, add_intro=False, add_outro=True):
    """Helper function to create a job dictionary
    
    Args:
        background_video (str): Path to background video
        audio_file (str): Path to audio file
        captions_file (str): Path to captions data file
        output_file (str): Path to save the output video
        job_id (str, optional): Unique identifier for this job
        theme (str, optional): Visual theme to use
        add_music (bool, optional): Whether to add background music
        add_intro (bool, optional): Whether to add intro animation
        add_outro (bool, optional): Whether to add call-to-action
        
    Returns:
        dict: Job dictionary
    """
    if job_id is None:
        # Generate a unique ID based on output file
        job_id = os.path.basename(output_file).split('.')[0]
    
    return {
        'job_id': job_id,
        'background_video': background_video,
        'audio_file': audio_file,
        'captions_file': captions_file,
        'output_file': output_file,
        'theme': theme,
        'add_music': add_music,
        'add_intro': add_intro,
        'add_outro': add_outro
    }

def process_directory(input_dir, output_dir, theme='default', add_music=False, add_intro=False, add_outro=True):
    """Process all videos in a directory
    
    Args:
        input_dir (str): Directory containing input files
        output_dir (str): Directory to save output files
        theme (str, optional): Visual theme to use
        add_music (bool, optional): Whether to add background music
        add_intro (bool, optional): Whether to add intro animation
        add_outro (bool, optional): Whether to add call-to-action
        
    Returns:
        list: Results of batch processing
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Find sets of files to process
    jobs = []
    
    # Group files by base name (before extension)
    file_groups = {}
    for filename in os.listdir(input_dir):
        base_name, ext = os.path.splitext(filename)
        if ext.lower() in ['.mp4', '.mov', '.avi', '.mp3', '.wav', '.json']:
            if base_name not in file_groups:
                file_groups[base_name] = []
            file_groups[base_name].append((filename, ext.lower()))
    
    # Create jobs from file groups
    for base_name, files in file_groups.items():
        # Find required files
        background_video = None
        audio_file = None
        captions_file = None
        
        for filename, ext in files:
            full_path = os.path.join(input_dir, filename)
            if ext in ['.mp4', '.mov', '.avi']:
                background_video = full_path
            elif ext in ['.mp3', '.wav']:
                audio_file = full_path
            elif ext == '.json':
                captions_file = full_path
        
        # Skip if missing required files
        if not (background_video and audio_file and captions_file):
            logger.warning(f"Skipping {base_name}: missing required files")
            continue
        
        # Create output file path
        output_file = os.path.join(output_dir, f"{base_name}_final.mp4")
        
        # Create and add job
        job = create_job(
            background_video, 
            audio_file, 
            captions_file, 
            output_file,
            job_id=base_name,
            theme=theme,
            add_music=add_music,
            add_intro=add_intro,
            add_outro=add_outro
        )
        
        jobs.append(job)
    
    # Process all jobs
    if jobs:
        processor = BatchProcessor()
        return processor.process_batch(jobs)
    else:
        logger.warning(f"No valid video sets found in {input_dir}")
        return []

if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    
    # Test batch processing
    jobs = [
        create_job(
            "output/test_background.mp4",
            "output/test_audio.mp3",
            "output/test_captions.json",
            "output/test_final1.mp4",
            job_id="test1",
            theme="modern"
        ),
        create_job(
            "output/test_background.mp4",
            "output/test_audio.mp3",
            "output/test_captions.json",
            "output/test_final2.mp4",
            job_id="test2",
            theme="dramatic"
        )
    ]
    
    processor = BatchProcessor()
    results = processor.process_batch(jobs)
    
    for result in results:
        print(f"Job {result['job_id']}: {result['status']} in {result['elapsed_time']:.2f} seconds") 