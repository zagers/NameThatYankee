import json
from pathlib import Path
import subprocess
import sys
import os

def review_and_edit_data(player_data: dict, project_dir: Path) -> dict:
    """
    Displays the AI-generated data to the user for review and allows for manual correction.
    """
    print("\n" + "="*40)
    print("--- Please Review the Following Data ---")
    print(f"Player Name: {player_data.get('name', 'N/A')}")
    print(f"Nickname: {player_data.get('nickname', 'N/A')}")
    print("Facts:")
    for i, fact in enumerate(player_data.get('facts', []), 1):
        print(f"  {i}. {fact}")
    print("Career Totals (from Baseball-Reference):")
    print(json.dumps(player_data.get('career_totals', {}), indent=2))
    print("Yearly WAR (for chart):")
    print(json.dumps(player_data.get('yearly_war', []), indent=2))
    print("="*40)

    while True:
        is_correct = input("Is all of this information correct? (y/n): ").lower().strip()
        if is_correct in ['y', 'n']:
            break
        print("Invalid input. Please enter 'y' or 'n'.")

    if is_correct == 'y':
        print("✅ Data confirmed.")
        return player_data
    else:
        temp_file_path = project_dir / "temp_player_data_to_edit.json"
        try:
            with open(temp_file_path, 'w') as f:
                json.dump(player_data, f, indent=4)
            
            print(f"\n📝 A temporary file has been created with the data.")
            print(f"   Please open this file in your preferred text editor:")
            print(f"   {temp_file_path}")
            print(f"   Correct any errors, SAVE the file, and then return to this terminal.")

            input("\nPress Enter in this terminal when you are finished editing...")

            with open(temp_file_path, 'r') as f:
                corrected_data = json.load(f)
            
            print("✅ Data updated with your corrections.")
            return corrected_data
        
        except Exception as e:
            print(f"❌ An error occurred during the editing process: {e}")
            return player_data
        finally:
            # Clean up the temporary file
            if temp_file_path.exists():
                temp_file_path.unlink()
