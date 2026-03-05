import pytest  # type: ignore
import config_manager  # type: ignore
from pathlib import Path

def test_config_manager_exists():
    assert hasattr(config_manager, "load_config")
    assert hasattr(config_manager, "save_config")

def test_get_config_path(mocker):
    mock_home = mocker.patch("config_manager.Path.home")
    mock_home.return_value = Path("/mock/home")
    expected_path = Path("/mock/home") / config_manager.CONFIG_FILE_NAME
    assert config_manager.get_config_path() == expected_path

def test_load_config_not_found(mocker, tmp_path):
    mocker.patch("config_manager.get_config_path", return_value=tmp_path / "nonexistent.json")
    assert config_manager.load_config() == {}

def test_load_config_success(mocker, tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text('{"api_key": "12345"}')
    mocker.patch("config_manager.get_config_path", return_value=config_file)
    
    data = config_manager.load_config()
    assert data["api_key"] == "12345"

def test_save_config(mocker, tmp_path):
    config_file = tmp_path / "config.json"
    mocker.patch("config_manager.get_config_path", return_value=config_file)
    
    config_manager.save_config({"api_key": "abc"})
    assert config_file.exists()
    assert config_file.read_text() == '{\n  "api_key": "abc"\n}'

