# ABOUTME: Client for interacting with the Google GenAI Batch API.
# ABOUTME: Manages file uploads, job creation, and status tracking for batch processing.

from google import genai
from google.genai import types
import os

class BatchClient:
    def __init__(self, api_key=None):
        """
        Initializes the GenAI client.
        Args:
            api_key: Optional API key. Defaults to GEMINI_API_KEY environment variable.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment or passed to constructor")
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
        f = self.client.files.upload(path=jsonl_path)
        
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
        if job.state != "SUCCEEDED":
            raise ValueError(f"Job {job_name} is not in SUCCEEDED state (current state: {job.state})")
        
        result_file = getattr(job, "results_file", None)
        if not result_file:
            raise AttributeError(f"BatchJob '{job_name}' is missing required 'results_file' attribute. Check job output configuration.")
             
        self.client.files.download(name=result_file, path=output_path)
