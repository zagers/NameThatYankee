import pytest  # type: ignore
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import json
import config_manager  # type: ignore

class TestConfigManager:
    """Test configuration management functionality"""

    def test_config_manager_exists(self):
        """Test that config manager functions exist"""
        assert hasattr(config_manager, "load_config")
        assert hasattr(config_manager, "save_config")
        assert hasattr(config_manager, "get_config_path")

    def test_get_config_path(self):
        """Test getting the configuration file path"""
        config_path = config_manager.get_config_path()
        
        # Should be in the user's home directory
        assert config_path.parent == Path.home()
        assert config_path.name == ".yankee_generator_config.json"
        assert isinstance(config_path, Path)

    def test_get_config_path_with_mocker(self, mocker):
        """Test getting config path with mocked home directory"""
        mock_home = mocker.patch("config_manager.Path.home")
        mock_home.return_value = Path("/mock/home")
        expected_path = Path("/mock/home") / config_manager.CONFIG_FILE_NAME
        assert config_manager.get_config_path() == expected_path

    def test_load_config_file_not_exists(self, mocker, tmp_path):
        """Test loading config when file doesn't exist"""
        mocker.patch("config_manager.get_config_path", return_value=tmp_path / "nonexistent.json")
        assert config_manager.load_config() == {}

    def test_load_config_success(self, mocker, tmp_path):
        """Test loading config when file exists with valid JSON"""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"api_key": "12345"}')
        mocker.patch("config_manager.get_config_path", return_value=config_file)
        
        data = config_manager.load_config()
        assert data["api_key"] == "12345"

    def test_load_config_file_exists_invalid_json(self, mocker, tmp_path):
        """Test loading config when file exists but contains invalid JSON"""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"invalid": json}')  # Invalid JSON
        mocker.patch("config_manager.get_config_path", return_value=config_file)
        
        result = config_manager.load_config()
        # Should return empty dict when JSON is invalid
        assert result == {}

    def test_load_config_file_exists_io_error(self, mocker):
        """Test loading config when file exists but can't be read"""
        mocker.patch("config_manager.get_config_path", return_value=Path("/test/config.json"))
        mocker.patch("pathlib.Path.exists", return_value=True)
        mocker.patch("builtins.open", side_effect=IOError("Permission denied"))
        
        result = config_manager.load_config()
        # Should return empty dict when file can't be read
        assert result == {}

    def test_save_config_success(self, mocker, tmp_path):
        """Test successful config saving"""
        config_file = tmp_path / "config.json"
        mocker.patch("config_manager.get_config_path", return_value=config_file)
        
        config_manager.save_config({"api_key": "abc"})
        assert config_file.exists()
        assert config_file.read_text() == '{\n  "api_key": "abc"\n}'

    def test_save_config_io_error(self, mocker):
        """Test config saving with IO error"""
        mocker.patch("config_manager.get_config_path", return_value=Path("/test/config.json"))
        mocker.patch("builtins.open", side_effect=IOError("Permission denied"))
        
        mock_print = mocker.patch("builtins.print")
        
        # Should not raise exceptions, just print warning
        config_manager.save_config({"api_key": "test"})
        
        # Verify warning was printed
        mock_print.assert_called_once()
        print_call = str(mock_print.call_args[0][0])
        assert "Warning: Could not save config file" in print_call

    def test_save_config_empty_dict(self, mocker):
        """Test saving empty config dict"""
        mock_file = mock_open()
        mocker.patch("config_manager.get_config_path", return_value=Path("/test/config.json"))
        mocker.patch("builtins.open", mock_file)
        
        config_manager.save_config({})
        
        # Should still attempt to save even empty dict
        mock_file.assert_called_once()

    def test_save_config_complex_data(self, mocker):
        """Test saving complex nested config data"""
        complex_config = {
            "last_project_path": "/tmp/test_project",
            "gemini_api_key": "test_api_key_12345",
            "preferences": {
                "theme": "dark",
                "auto_save": True,
                "recent_projects": [
                    "/tmp/project1",
                    "/tmp/project2"
                ]
            },
            "stats": {
                "total_generated": 42,
                "last_generation": "2025-01-15"
            }
        }
        
        mock_file = mock_open()
        mocker.patch("config_manager.get_config_path", return_value=Path("/test/config.json"))
        mocker.patch("builtins.open", mock_file)
        
        config_manager.save_config(complex_config)
        
        # Should handle complex data without issues
        mock_file.assert_called_once()

    def test_config_file_name_constant(self):
        """Test that config file name is correctly defined"""
        assert config_manager.CONFIG_FILE_NAME == ".yankee_generator_config.json"

    def test_round_trip_config(self, mocker, tmp_path):
        """Test that saved config can be loaded back correctly"""
        original_config = {
            "last_project_path": "/tmp/test_project",
            "gemini_api_key": "test_api_key_12345",
            "preferences": {
                "automated": True,
                "mode": "facts-only"
            }
        }
        
        config_file = tmp_path / "config.json"
        mocker.patch("config_manager.get_config_path", return_value=config_file)
        
        # Save the config
        config_manager.save_config(original_config)
        
        # Load it back
        loaded_config = config_manager.load_config()
        
        assert loaded_config == original_config

    def test_load_config_partial_data(self, mocker, tmp_path):
        """Test loading config with only some fields present"""
        partial_config = {
            "last_project_path": "/tmp/test_project"
            # Missing gemini_api_key
        }
        
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(partial_config))
        mocker.patch("config_manager.get_config_path", return_value=config_file)
        
        result = config_manager.load_config()
        
        assert result == partial_config
        assert "last_project_path" in result
        assert "gemini_api_key" not in result

    def test_save_config_overwrites_existing(self, mocker, tmp_path):
        """Test that save_config overwrites existing config"""
        config_file = tmp_path / "config.json"
        mocker.patch("config_manager.get_config_path", return_value=config_file)
        
        # Save once
        config_manager.save_config({"old": "data"})
        assert config_file.read_text() == '{\n  "old": "data"\n}'
        
        # Save again with new data
        config_manager.save_config({"new": "data"})
        assert config_file.read_text() == '{\n  "new": "data"\n}'

    def test_config_path_is_absolute(self):
        """Test that config path is absolute"""
        config_path = config_manager.get_config_path()
        assert config_path.is_absolute()

    def test_config_path_home_directory(self):
        """Test that config path is in home directory"""
        config_path = config_manager.get_config_path()
        expected_parent = Path.home()
        assert config_path.parent == expected_parent

    def test_save_config_with_none_values(self, mocker):
        """Test saving config with None values"""
        config_with_none = {
            "last_project_path": None,
            "gemini_api_key": "test_key",
            "optional_field": None
        }
        
        mock_file = mock_open()
        mocker.patch("config_manager.get_config_path", return_value=Path("/test/config.json"))
        mocker.patch("builtins.open", mock_file)
        
        # Should handle None values without issues
        config_manager.save_config(config_with_none)
        
        mock_file.assert_called_once()

    def test_load_config_with_special_characters(self, mocker, tmp_path):
        """Test loading config with special characters in values"""
        special_config = {
            "project_path": "/path/with spaces and/special-chars_@#$%",
            "api_key": "key-with-special-chars!@#$%^&*()",
            "unicode_text": "Hello 世界 🚀",
            "escape_sequences": "Line1\nLine2\tTabbed"
        }
        
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(special_config))
        mocker.patch("config_manager.get_config_path", return_value=config_file)
        
        result = config_manager.load_config()
        
        assert result == special_config
        assert result["unicode_text"] == "Hello 世界 🚀"
        assert result["escape_sequences"] == "Line1\nLine2\tTabbed"

    def test_config_file_permissions_scenario(self, mocker):
        """Test scenario where config file has permission issues"""
        sample_config = {"test": "data"}
        
        # Test load fails due to permissions
        mocker.patch("config_manager.get_config_path", return_value=Path("/test/config.json"))
        mocker.patch("pathlib.Path.exists", return_value=True)
        mocker.patch("builtins.open", side_effect=IOError("Permission denied"))
        
        result = config_manager.load_config()
        assert result == {}
        
        # Test save fails due to permissions
        mock_print = mocker.patch("builtins.print")
        
        # Should not raise exception
        config_manager.save_config(sample_config)
        
        # Should print warning
        mock_print.assert_called_once()
        warning_message = str(mock_print.call_args[0][0])
        assert "Warning" in warning_message
        assert "Permission denied" in warning_message
