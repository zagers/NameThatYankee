import pytest  # type: ignore
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import json
import user_interaction  # type: ignore

@pytest.fixture
def sample_player_data():
    """Sample player data for testing"""
    return {
        "name": "Derek Jeter",
        "nickname": "The Captain",
        "facts": [
            "Hit a home run for his 3000th hit",
            "Won 5 World Series championships",
            "Captain of the New York Yankees"
        ],
        "career_totals": {
            "WAR": "71.3",
            "AB": "11195",
            "HR": "260"
        },
        "yearly_war": [
            {"year": "1996", "display_team": "NYY", "teams": ["NYY"], "war": 3.3},
            {"year": "1997", "display_team": "NYY", "teams": ["NYY"], "war": 7.4}
        ]
    }

@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory for file operations"""
    return tmp_path

def test_review_and_edit_data_automated_mode(sample_player_data, temp_dir):
    """Test that automated mode skips review and returns data unchanged"""
    with patch('builtins.print') as mock_print:
        result = user_interaction.review_and_edit_data(
            sample_player_data, 
            temp_dir, 
            automated=True
        )
    
    assert result == sample_player_data
    mock_print.assert_called_with("  Skipping manual review in automated mode.")

def test_review_and_edit_data_manual_mode_confirm_yes(sample_player_data, temp_dir):
    """Test manual mode when user confirms data is correct"""
    with patch('builtins.input') as mock_input, \
         patch('builtins.print') as mock_print:
        
        # Simulate user entering 'y' to confirm
        mock_input.side_effect = ['y']
        
        result = user_interaction.review_and_edit_data(
            sample_player_data, 
            temp_dir, 
            automated=False
        )
    
    assert result == sample_player_data
    # Verify the confirmation message was printed
    mock_print.assert_any_call("✅ Data confirmed.")

def test_review_and_edit_data_manual_mode_confirm_no_with_edit_basic(sample_player_data, temp_dir):
    """Test basic manual mode flow without complex file mocking"""
    # Test that the function attempts to create a temp file when user wants to edit
    temp_file_path = temp_dir / "temp_player_data_to_edit.json"
    
    with patch('builtins.input') as mock_input, \
         patch('builtins.print') as mock_print, \
         patch('builtins.open', new_callable=mock_open) as mock_file, \
         patch('json.load', return_value=sample_player_data):  # Return same data for simplicity
        
        # Simulate user entering 'n' to edit, then pressing Enter
        mock_input.side_effect = ['n', '']
        
        result = user_interaction.review_and_edit_data(
            sample_player_data, 
            temp_dir, 
            automated=False
        )
    
    # Should return the data (in this case, same as input since we mocked json.load)
    assert result == sample_player_data
    
    # Verify file operations were attempted
    mock_file.assert_called()
    # Verify print messages were shown
    mock_print.assert_any_call("\n" + "="*40)
    mock_print.assert_any_call("--- Please Review the Following Data ---")

def test_review_and_edit_data_manual_mode_confirm_no_file_error(sample_player_data, temp_dir):
    """Test handling of file I/O errors during editing"""
    with patch('builtins.input') as mock_input, \
         patch('builtins.print') as mock_print, \
         patch('builtins.open', side_effect=IOError("Permission denied")):
        
        # Simulate user entering 'n' to edit
        mock_input.side_effect = ['n']
        
        result = user_interaction.review_and_edit_data(
            sample_player_data, 
            temp_dir, 
            automated=False
        )
    
    # Should return original data when file operation fails
    assert result == sample_player_data
    # Verify error message was printed
    mock_print.assert_any_call("❌ An error occurred during the editing process: Permission denied")

def test_review_and_edit_data_manual_mode_invalid_input_then_confirm(sample_player_data, temp_dir):
    """Test handling of invalid user input before valid confirmation"""
    with patch('builtins.input') as mock_input, \
         patch('builtins.print') as mock_print:
        
        # Simulate invalid input, then valid 'y'
        mock_input.side_effect = ['maybe', 'y']
        
        result = user_interaction.review_and_edit_data(
            sample_player_data, 
            temp_dir, 
            automated=False
        )
    
    assert result == sample_player_data
    # Verify error message for invalid input
    mock_print.assert_any_call("Invalid input. Please enter 'y' or 'n'.")

def test_review_and_edit_data_manual_mode_cleanup_temp_file(sample_player_data, temp_dir):
    """Test that temporary file is cleaned up even if editing fails"""
    temp_file_path = temp_dir / "temp_player_data_to_edit.json"
    
    with patch('builtins.input') as mock_input, \
         patch('builtins.print') as mock_print, \
         patch('builtins.open', side_effect=IOError("File error")) as mock_file:
        
        # Simulate user entering 'n' to edit
        mock_input.side_effect = ['n']
        
        # Create the temp file to test cleanup
        temp_file_path.write_text("test")
        
        result = user_interaction.review_and_edit_data(
            sample_player_data, 
            temp_dir, 
            automated=False
        )
    
    # Verify temp file was cleaned up
    assert not temp_file_path.exists()

def test_review_and_edit_data_display_formatting(sample_player_data, temp_dir):
    """Test that data is displayed in the correct format"""
    with patch('builtins.input') as mock_input, \
         patch('builtins.print') as mock_print:
        
        mock_input.side_effect = ['y']
        
        user_interaction.review_and_edit_data(
            sample_player_data, 
            temp_dir, 
            automated=False
        )
    
    # Check that key data elements are printed
    print_calls = [str(call.args[0]) for call in mock_print.call_args_list]
    
    # Verify header
    assert any("Please Review the Following Data" in call for call in print_calls)
    
    # Verify player info
    assert any("Player Name: Derek Jeter" in call for call in print_calls)
    assert any("Nickname: The Captain" in call for call in print_calls)
    
    # Verify facts are numbered
    assert any("1. Hit a home run for his 3000th hit" in call for call in print_calls)
    assert any("2. Won 5 World Series championships" in call for call in print_calls)
    assert any("3. Captain of the New York Yankees" in call for call in print_calls)
    
    # Verify stats data is printed as JSON
    assert any('"WAR": "71.3"' in call for call in print_calls)
    assert any('"AB": "11195"' in call for call in print_calls)

def test_review_and_edit_data_with_empty_data(temp_dir):
    """Test handling of empty or minimal player data"""
    minimal_data = {"name": "Unknown Player"}
    
    with patch('builtins.input') as mock_input, \
         patch('builtins.print') as mock_print:
        
        mock_input.side_effect = ['y']
        
        result = user_interaction.review_and_edit_data(
            minimal_data, 
            temp_dir, 
            automated=False
        )
    
    assert result == minimal_data
    
    # Check that empty fields are handled gracefully
    print_calls = [str(call.args[0]) for call in mock_print.call_args_list]
    assert any("Player Name: Unknown Player" in call for call in print_calls)
    assert any("Nickname: N/A" in call for call in print_calls)

def test_review_and_edit_data_with_malformed_json_correction(sample_player_data, temp_dir):
    """Test handling of malformed JSON in edited file"""
    # Create malformed JSON that json.load will fail to parse
    malformed_json = '{"name": "Derek Jeter", "nickname": "The Captain" '  # Missing closing brace
    
    with patch('builtins.input') as mock_input, \
         patch('builtins.print') as mock_print, \
         patch('builtins.open', new_callable=mock_open) as mock_file, \
         patch('json.load', side_effect=json.JSONDecodeError("Expecting ':'", "test", 1)):
        
        # Setup the mock file handle to return malformed data when reading
        file_handle = mock_file.return_value.__enter__.return_value
        file_handle.read.return_value = malformed_json
        mock_input.side_effect = ['n']
        
        result = user_interaction.review_and_edit_data(
            sample_player_data, 
            temp_dir, 
            automated=False
        )
    
    # Should return original data when JSON parsing fails
    assert result == sample_player_data
    # Verify error message was printed
    error_calls = [str(call) for call in mock_print.call_args_list if "error occurred" in str(call).lower()]
    assert len(error_calls) > 0

def test_review_and_edit_data_file_permissions_error(sample_player_data, temp_dir):
    """Test handling of file permission errors during cleanup"""
    temp_file_path = temp_dir / "temp_player_data_to_edit.json"
    
    with patch('builtins.input') as mock_input, \
         patch('builtins.print') as mock_print, \
         patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.unlink', side_effect=PermissionError("Cannot delete file")):
        
        mock_input.side_effect = ['n']
        
        # The PermissionError in the finally block should propagate
        with pytest.raises(PermissionError, match="Cannot delete file"):
            user_interaction.review_and_edit_data(
                sample_player_data, 
                temp_dir, 
                automated=False
            )

def test_review_and_edit_data_complex_nested_data(temp_dir):
    """Test with complex nested data structures"""
    complex_data = {
        "name": "Complex Player",
        "career_totals": {
            "advanced_stats": {
                "war": {"overall": 50.5, "batting": 45.2, "fielding": 5.3},
                "other_metrics": {"wrc_plus": 125, "wraa": 23.4}
            }
        },
        "yearly_war": [
            {
                "year": "2020",
                "teams": ["NYY", "BOS"],
                "splits": {
                    "vs_left": {"war": 2.1},
                    "vs_right": {"war": 3.2}
                }
            }
        ]
    }
    
    with patch('builtins.input') as mock_input, \
         patch('builtins.print') as mock_print:
        
        mock_input.side_effect = ['y']
        
        result = user_interaction.review_and_edit_data(
            complex_data, 
            temp_dir, 
            automated=False
        )
    
    assert result == complex_data
    
    # Verify complex JSON is printed correctly
    print_calls = [str(call.args[0]) for call in mock_print.call_args_list]
    # Check for key elements in the printed output
    output_text = ' '.join(print_calls)
    assert '"overall": 50.5' in output_text
    assert '"vs_left"' in output_text
