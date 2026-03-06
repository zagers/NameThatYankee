"""
Git integration for automated workflow.

Handles git operations for committing and pushing puzzle updates.
"""

import subprocess
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

class GitIntegration:
    """Handles git operations for the automated workflow."""
    
    def __init__(self, project_dir: Path):
        """
        Initialize git integration.
        
        Args:
            project_dir: Path to the project directory
        """
        self.project_dir = project_dir
        self.git_dir = project_dir / ".git"
        
        if not self.git_dir.exists():
            logger.warning("Not a git repository - git operations will be disabled")
            self.is_git_repo = False
        else:
            self.is_git_repo = True
    
    def add_files(self, files: List[str]) -> bool:
        """
        Add files to git staging area.
        
        Args:
            files: List of file paths to add
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_git_repo:
            logger.warning("Not a git repository - cannot add files")
            return False
        
        try:
            for file_path in files:
                result = subprocess.run(
                    ['git', 'add', file_path],
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    logger.error(f"Failed to add {file_path}: {result.stderr}")
                    return False
                else:
                    logger.debug(f"Added {file_path} to git")
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Git add operation timed out")
            return False
        except Exception as e:
            logger.error(f"Error adding files to git: {e}")
            return False
    
    def commit(self, message: str) -> bool:
        """
        Commit staged changes with a message.
        
        Args:
            message: Commit message
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_git_repo:
            logger.warning("Not a git repository - cannot commit")
            return False
        
        try:
            # Check if there are staged changes
            result = subprocess.run(
                ['git', 'diff', '--cached', '--quiet'],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info("No staged changes to commit")
                return True
            
            # Commit changes
            result = subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Git commit failed: {result.stderr}")
                return False
            else:
                logger.info(f"Committed changes: {message}")
                return True
                
        except subprocess.TimeoutExpired:
            logger.error("Git commit operation timed out")
            return False
        except Exception as e:
            logger.error(f"Error committing changes: {e}")
            return False
    
    def push(self, remote: str = "origin", branch: str = "master") -> bool:
        """
        Push committed changes to remote repository.
        
        Args:
            remote: Remote repository name
            branch: Branch name to push
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_git_repo:
            logger.warning("Not a git repository - cannot push")
            return False
        
        try:
            result = subprocess.run(
                ['git', 'push', remote, branch],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"Git push failed: {result.stderr}")
                return False
            else:
                logger.info(f"Pushed changes to {remote}/{branch}")
                return True
                
        except subprocess.TimeoutExpired:
            logger.error("Git push operation timed out")
            return False
        except Exception as e:
            logger.error(f"Error pushing changes: {e}")
            return False
    
    def get_status(self) -> Optional[dict]:
        """
        Get current git status.
        
        Returns:
            Dictionary with status information or None if failed
        """
        if not self.is_git_repo:
            return None
        
        try:
            # Get branch info
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            current_branch = result.stdout.strip() if result.returncode == 0 else "unknown"
            
            # Get staged files
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            staged_files = result.stdout.strip().split('\n') if result.returncode == 0 else []
            
            # Get modified files
            result = subprocess.run(
                ['git', 'diff', '--name-only'],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            modified_files = result.stdout.strip().split('\n') if result.returncode == 0 else []
            
            # Get untracked files
            result = subprocess.run(
                ['git', 'ls-files', '--others', '--exclude-standard'],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            untracked_files = result.stdout.strip().split('\n') if result.returncode == 0 else []
            
            return {
                'current_branch': current_branch,
                'staged_files': [f for f in staged_files if f],
                'modified_files': [f for f in modified_files if f],
                'untracked_files': [f for f in untracked_files if f],
                'has_changes': bool(staged_files or modified_files or untracked_files)
            }
            
        except Exception as e:
            logger.error(f"Error getting git status: {e}")
            return None
    
    def has_uncommitted_changes(self) -> bool:
        """
        Check if there are uncommitted changes.
        
        Returns:
            True if there are uncommitted changes, False otherwise
        """
        status = self.get_status()
        if status:
            return status['has_changes']
        return False
    
    def is_ahead_of_remote(self, remote: str = "origin", branch: str = "master") -> bool:
        """
        Check if local branch is ahead of remote.
        
        Args:
            remote: Remote repository name
            branch: Branch name to check
            
        Returns:
            True if ahead of remote, False otherwise
        """
        if not self.is_git_repo:
            return False
        
        try:
            # Get commit count difference
            result = subprocess.run(
                ['git', 'rev-list', '--count', f'{remote}/{branch}..{branch}'],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                ahead_count = int(result.stdout.strip())
                return ahead_count > 0
            else:
                logger.debug(f"Could not check ahead status: {result.stderr}")
                return False
                
        except (ValueError, subprocess.TimeoutExpired, Exception) as e:
            logger.debug(f"Error checking ahead status: {e}")
            return False
    
    def safe_commit_and_push(self, message: str, remote: str = "origin", branch: str = "master") -> bool:
        """
        Safely commit and push changes with error handling.
        
        Args:
            message: Commit message
            remote: Remote repository name
            branch: Branch name to push
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_git_repo:
            logger.warning("Not a git repository - cannot commit and push")
            return False
        
        try:
            # Check if we have changes to commit
            if not self.has_uncommitted_changes():
                logger.info("No changes to commit")
                return True
            
            # Commit changes
            if not self.commit(message):
                return False
            
            # Check if we should push
            if self.is_ahead_of_remote(remote, branch):
                if not self.push(remote, branch):
                    return False
            else:
                logger.info("Local branch is not ahead of remote - skipping push")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in safe commit and push: {e}")
            return False
