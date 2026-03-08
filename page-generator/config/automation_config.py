"""
Configuration management for automation features.

Handles settings and preferences for the automated workflow.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)

class AutomationConfig:
    """Configuration manager for automation features."""
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize automation configuration.
        
        Args:
            config_file: Path to configuration file, uses default if None
        """
        if config_file is None:
            config_file = Path.cwd() / "automation_config.json"
        
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"Loaded automation config from {self.config_file}")
                return config
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
                logger.info("Using default configuration")
        
        # Default configuration
        default_config = {
            "image_processing": {
                "quality": 85,
                "max_width": 800,
                "max_height": 600,
                "min_width": 200,
                "min_height": 200
            },
            "player_image_search": {
                "max_results": 10,
                "timeout_seconds": 30,
                "prefer_baseball_cards": True,
                "fallback_enabled": True
            },
            "git_integration": {
                "auto_commit": False,
                "auto_push": False,
                "remote": "origin",
                "branch": "master"
            },
            "workflow": {
                "auto_approve_player": True,
                "skip_manual_review": True,
                "cleanup_temp_files": True,
                "batch_processing_enabled": True
            },
            "logging": {
                "level": "INFO",
                "file": "automation.log"
            }
        }
        
        # Save default config
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Saved automation config to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving config file: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key (supports dot notation like 'image_processing.quality')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set configuration value using dot notation.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        keys = key.split('.')
        config = self.config
        
        try:
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set the value
            config[keys[-1]] = value
            return self._save_config(self.config)
            
        except Exception as e:
            logger.error(f"Error setting config value {key}: {e}")
            return False
    
    def update(self, updates: Dict[str, Any]) -> bool:
        """
        Update multiple configuration values.
        
        Args:
            updates: Dictionary of key-value pairs to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            for key, value in updates.items():
                self.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            return False
    
    def get_image_processing_config(self) -> Dict[str, Any]:
        """Get image processing configuration."""
        return self.get('image_processing', {})
    
    def get_player_search_config(self) -> Dict[str, Any]:
        """Get player image search configuration."""
        return self.get('player_image_search', {})
    
    def get_git_config(self) -> Dict[str, Any]:
        """Get git integration configuration."""
        return self.get('git_integration', {})
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """Get workflow configuration."""
        return self.get('workflow', {})
    
    def is_auto_commit_enabled(self) -> bool:
        """Check if auto-commit is enabled."""
        return self.get('git_integration.auto_commit', False)
    
    def is_auto_push_enabled(self) -> bool:
        """Check if auto-push is enabled."""
        return self.get('git_integration.auto_push', False)
    
    def is_manual_review_skipped(self) -> bool:
        """Check if manual review is skipped."""
        return self.get('workflow.skip_manual_review', True)
    
    def set_auto_commit(self, enabled: bool) -> bool:
        """Enable or disable auto-commit."""
        return self.set('git_integration.auto_commit', enabled)
    
    def set_auto_push(self, enabled: bool) -> bool:
        """Enable or disable auto-push."""
        return self.set('git_integration.auto_push', enabled)
    
    def set_image_quality(self, quality: int) -> bool:
        """Set image processing quality."""
        return self.set('image_processing.quality', quality)
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate configuration and return issues.
        
        Returns:
            Dictionary with validation results
        """
        issues = []
        warnings = []
        
        # Validate image processing settings
        img_config = self.get_image_processing_config()
        quality = img_config.get('quality', 85)
        if not isinstance(quality, int) or quality < 1 or quality > 100:
            issues.append("Image quality must be an integer between 1 and 100")
        
        max_width = img_config.get('max_width', 800)
        if not isinstance(max_width, int) or max_width < 100:
            issues.append("Max width must be an integer >= 100")
        
        max_height = img_config.get('max_height', 600)
        if not isinstance(max_height, int) or max_height < 100:
            issues.append("Max height must be an integer >= 100")
        
        # Validate git settings
        git_config = self.get_git_config()
        if git_config.get('auto_push', False) and not git_config.get('auto_commit', False):
            warnings.append("Auto-push is enabled but auto-commit is disabled")
        
        # Validate workflow settings
        workflow_config = self.get_workflow_config()
        if workflow_config.get('auto_approve_player', False) and not workflow_config.get('skip_manual_review', False):
            warnings.append("Auto-approve player is enabled but manual review is not skipped")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to default values."""
        try:
            if self.config_file.exists():
                self.config_file.unlink()
            self.config = self._load_config()
            logger.info("Reset automation configuration to defaults")
            return True
        except Exception as e:
            logger.error(f"Error resetting configuration: {e}")
            return False
    
    def export_config(self, export_path: Path) -> bool:
        """Export configuration to specified file."""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Exported automation config to {export_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting config: {e}")
            return False
    
    def import_config(self, import_path: Path) -> bool:
        """Import configuration from specified file."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Validate imported config
            temp_config = self.config
            self.config = imported_config
            validation = self.validate_config()
            
            if not validation['valid']:
                self.config = temp_config  # Restore original config
                logger.error(f"Invalid imported config: {validation['issues']}")
                return False
            
            # Save imported config
            if self._save_config(self.config):
                logger.info(f"Imported automation config from {import_path}")
                return True
            else:
                self.config = temp_config  # Restore original config
                return False
                
        except Exception as e:
            logger.error(f"Error importing config: {e}")
            return False
