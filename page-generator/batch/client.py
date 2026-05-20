# ABOUTME: Client for interacting with the Google GenAI Batch API.
# ABOUTME: Manages file uploads, job creation, and status tracking for batch processing.

from google import genai
from google.genai import types
import os
import sys
from pathlib import Path

# Add page-generator to path to import config_manager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config_manager

class BatchClient:
    def __init__(self, api_key=None):
        """
        Initializes the GenAI client.
        Args:
            api_key: Optional API key. Defaults to GEMINI_API_KEY env or local config.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        
        # Fallback to local config file
        if not self.api_key:
            config = config_manager.load_config()
            self.api_key = config.get("gemini_api_key")
            
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment or local config")
            
        self.client = genai.Client(api_key=self.api_key)
        
    def submit_batch(self, jsonl_path, model="gemini-3.1-flash-lite"):
        """
        Uploads a JSONL file and creates a batch job.
        Args:
            jsonl_path: Path to the .jsonl file containing requests.
            model: The Gemini model to use.
        Returns:
            The created BatchJob object.
        """
        # 1. Upload the file
        # Note: google-genai handles the file upload
        f = self.client.files.upload(
            file=jsonl_path,
            config={'mime_type': 'application/jsonl'}
        )
        
        # 2. Create the batch job
        job = self.client.batches.create(
            model=model,
            src=f.name
        )
        return job

    def get_job(self, job_name):
        """
        Retrieves the status and details of a batch job.
        Args:
            job_name: The resource name of the job (e.g. 'batches/12345').
        Returns:
            The BatchJob object.
        """
        return self.client.batches.get(name=job_name)
        
    def list_jobs(self):
        """
        Lists all batch jobs.
        Returns:
            A list of BatchJob objects.
        """
        return list(self.client.batches.list())

    def download_results(self, job_name, output_path):
        """
        Downloads the results of a completed batch job.
        Args:
            job_name: The resource name of the job.
            output_path: Local path where the results file will be saved.
        Raises:
            ValueError: If the job is not SUCCEEDED or has no results file.
        """
        job = self.get_job(job_name)
        state_str = str(job.state)
        if "SUCCEEDED" not in state_str:
            raise ValueError(f"Job {job_name} is not in SUCCEEDED state (current state: {job.state})")
        
        # In the new SDK, the destination file is in job.dest.file_name
        result_file = None
        if hasattr(job, 'dest') and hasattr(job.dest, 'file_name'):
            result_file = job.dest.file_name
        
        if not result_file:
            raise AttributeError(f"BatchJob '{job_name}' is missing result file information in 'dest.file_name'.")
             
        file_data = self.client.files.download(file=result_file)
        with open(output_path, 'wb') as f:
            f.write(file_data)

if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Gemini Batch API Client")
    parser.add_argument("--submit", type=str, help="Path to JSONL file to submit")
    parser.add_argument("--status", type=str, help="Job ID to check status for")
    parser.add_argument("--download", type=str, nargs=2, metavar=('JOB_ID', 'OUTPUT_PATH'), help="Job ID and output path to download results")
    parser.add_argument("--list", action="store_true", help="List all batch jobs")
    
    args = parser.parse_args()
    client = BatchClient()
    
    try:
        if args.submit:
            job = client.submit_batch(args.submit)
            print(f"Successfully submitted batch job.")
            print(f"Job Name: {job.name}")
            print(f"State: {job.state}")
            print(f"Create Time: {job.create_time}")
            
        elif args.status:
            job = client.get_job(args.status)
            print(f"Job: {job.name}")
            print(f"State: {job.state}")
            if job.state == "FAILED":
                print(f"Error: {job.error}")
            elif job.state == "SUCCEEDED":
                print(f"Results File: {getattr(job, 'results_file', 'N/A')}")
                
        elif args.download:
            job_id, output_path = args.download
            print(f"Downloading results for {job_id} to {output_path}...")
            client.download_results(job_id, output_path)
            print("Download complete.")
            
        elif args.list:
            jobs = client.list_jobs()
            print(f"{'Job Name':<30} {'State':<15} {'Created'}")
            print("-" * 60)
            for j in jobs:
                print(f"{j.name:<30} {j.state:<15} {j.create_time}")
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
