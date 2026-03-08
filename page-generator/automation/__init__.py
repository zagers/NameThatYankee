"""
Automation module for Name That Yankee puzzle workflow.

This module provides automated tools to streamline the puzzle addition process,
including image processing, player image search, and workflow orchestration.
"""

from .image_processor import ImageProcessor
from .player_image_search import PlayerImageSearch
from .automated_workflow import AutomatedWorkflow
from .git_integration import GitIntegration

__all__ = [
    'ImageProcessor',
    'PlayerImageSearch', 
    'AutomatedWorkflow',
    'GitIntegration'
]
