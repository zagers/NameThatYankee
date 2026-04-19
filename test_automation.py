#!/usr/bin/env python3
"""
Test script for the automation workflow.

This script tests the basic functionality of the automation modules.
"""

import sys
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Add the page-generator directory to the path
sys.path.insert(0, str(Path(__file__).parent / "page-generator"))

def create_test_image(path: Path, size: tuple = (400, 300), text: str = "Test Image"):
    """Create a test image for testing purposes."""
    img = Image.new('RGB', size, color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw some text
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    draw.text((50, 50), text, fill='black', font=font)
    
    # Save as PNG
    img.save(path, 'PNG')
    print(f"Created test image: {path}")

def test_image_processor():
    """Test the image processor module."""
    print("\n--- Testing Image Processor ---")
    
    try:
        from automation.image_processor import ImageProcessor
        
        # Create test image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            test_png_path = Path(tmp.name)
        
        create_test_image(test_png_path)
        
        # Test processor
        processor = ImageProcessor()
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            images_dir = Path(tmp_dir)
            
            # Test conversion
            webp_path = images_dir / "test.webp"
            success = processor.convert_to_webp(test_png_path, webp_path)
            
            if success and webp_path.exists():
                print("✅ Image conversion successful")
                
                # Test image info
                info = processor.get_image_info(webp_path)
                if info:
                    print(f"✅ Image info: {info['width']}x{info['height']}, {info['size_bytes']} bytes")
                
                # Test validation
                if processor.validate_image_quality(webp_path):
                    print("✅ Image validation passed")
                else:
                    print("❌ Image validation failed")
            else:
                print("❌ Image conversion failed")
        
        # Cleanup
        test_png_path.unlink(missing_ok=True)
        
    except ImportError as e:
        print(f"❌ Could not import ImageProcessor: {e}")
    except Exception as e:
        print(f"❌ Error testing ImageProcessor: {e}")

def test_automation_config():
    """Test the automation config module."""
    print("\n--- Testing Automation Config ---")
    
    try:
        from config.automation_config import AutomationConfig
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            config_file = Path(tmp.name)
        
        # Test config creation
        config = AutomationConfig(config_file)
        
        # Test getting values
        quality = config.get('image_processing.quality')
        print(f"✅ Default image quality: {quality}")
        
        # Test setting values
        success = config.set('image_processing.quality', 90)
        if success:
            new_quality = config.get('image_processing.quality')
            print(f"✅ Updated image quality: {new_quality}")
        else:
            print("❌ Failed to update config")
        
        # Test validation
        validation = config.validate_config()
        if validation['valid']:
            print("✅ Configuration validation passed")
        else:
            print(f"❌ Configuration validation failed: {validation['issues']}")
        
        # Cleanup
        config_file.unlink(missing_ok=True)
        
    except ImportError as e:
        print(f"❌ Could not import AutomationConfig: {e}")
    except Exception as e:
        print(f"❌ Error testing AutomationConfig: {e}")

def test_git_integration():
    """Test the git integration module."""
    print("\n--- Testing Git Integration ---")
    
    try:
        from automation.git_integration import GitIntegration
        
        # Test with current directory
        git_integration = GitIntegration(Path.cwd())
        
        if git_integration.is_git_repo:
            print("✅ Git repository detected")
            
            # Test getting status
            status = git_integration.get_status()
            if status:
                print(f"✅ Current branch: {status['current_branch']}")
                print(f"✅ Has changes: {status['has_changes']}")
            else:
                print("❌ Failed to get git status")
        else:
            print("⚠️ Not a git repository - git tests skipped")
        
    except ImportError as e:
        print(f"❌ Could not import GitIntegration: {e}")
    except Exception as e:
        print(f"❌ Error testing GitIntegration: {e}")

def test_automated_workflow_import():
    """Test importing the automated workflow module."""
    print("\n--- Testing Automated Workflow Import ---")
    
    try:
        from automation.automated_workflow import AutomatedWorkflow
        print("✅ AutomatedWorkflow imported successfully")
        
        # Test initialization (without running full workflow)
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir)
            config = {"gemini_api_key": "test_key"}
            
            workflow = AutomatedWorkflow(project_dir, config)
            print("✅ AutomatedWorkflow initialized successfully")
            
    except ImportError as e:
        print(f"❌ Could not import AutomatedWorkflow: {e}")
    except Exception as e:
        print(f"❌ Error testing AutomatedWorkflow: {e}")

def main():
    """Run all tests."""
    print("🧪 Testing Automation Modules")
    print("=" * 50)
    
    test_image_processor()
    test_automation_config()
    test_git_integration()
    test_automated_workflow_import()
    
    print("\n" + "=" * 50)
    print("🏁 Testing completed!")

import json
import html_generator

def test_rebuild_index_generates_stats_summary(tmp_path):
    # Setup mock project structure
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    images_dir = project_dir / "images"
    images_dir.mkdir()
    
    # Create a dummy index.html
    (project_dir / "index.html").write_text('<div class="gallery"></div><footer id="last-updated"></footer>', encoding='utf-8')
    
    # Create a dummy clue and puzzle page
    date_str = "2026-04-18"
    (images_dir / f"clue-{date_str}.webp").write_text("fake image data")
    puzzle_html = f'''
    <html>
        <body>
            <h2>Fran Healy</h2>
            <div id="search-data">{{"teams": ["NYY", "KCR"], "years": ["1971", "1972"]}}</div>
        </body>
    </html>
    '''
    (project_dir / f"{date_str}.html").write_text(puzzle_html, encoding='utf-8')
    
    html_generator.rebuild_index_page(project_dir)
    
    stats_file = project_dir / "stats_summary.json"
    assert stats_file.exists()
    
    with open(stats_file, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 1
    assert data[0]['date'] == date_str
    assert data[0]['name'] == "Fran Healy"
    assert "NYY" in data[0]['teams']

if __name__ == "__main__":
    main()
