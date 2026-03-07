#!/usr/bin/env python3
"""
Quick test to verify the image search fix works.
"""

import sys
from pathlib import Path

# Add the page-generator directory to the path
sys.path.insert(0, str(Path(__file__).parent / "page-generator"))

def test_image_search():
    """Test the fixed image search."""
    try:
        from automation.player_image_search import PlayerImageSearch
        from automation.image_processor import ImageProcessor
        
        print("🧪 Testing fixed image search...")
        
        # Initialize components
        image_processor = ImageProcessor()
        player_search = PlayerImageSearch(image_processor)
        
        # Test search for Duke Ellis
        print("🔍 Searching for 'Duke Ellis mlb player'...")
        results = player_search.search_player_images("Duke Ellis", max_results=5)
        
        print(f"📊 Found {len(results)} results")
        
        if results:
            print("✅ Sample results:")
            for i, result in enumerate(results[:3]):
                url = result['url']
                print(f"  [{i}] {url[:80]}...")
                print(f"      Relevance: {result['relevance_score']}")
                print(f"      Is card: {result['is_card']}")
            
            # Test downloading first result
            print("\n📥 Testing image download...")
            first_result = results[0]
            print(f"   Testing URL: {first_result['url'][:100]}...")
            
            success = player_search._download_and_validate_image(first_result)
            
            if success:
                print("✅ Image download successful!")
                if 'temp_file' in first_result:
                    temp_path = first_result['temp_file']
                    if temp_path.exists():
                        size = temp_path.stat().st_size
                        print(f"   File size: {size} bytes")
                        # Cleanup
                        temp_path.unlink()
                else:
                    print("   No temp file found")
            else:
                print("❌ Image download failed")
                # Debug the data URI issue
                print(f"   URL type: {'data URI' if first_result['url'].startswith('data:') else 'HTTP'}")
                if first_result['url'].startswith('data:'):
                    data_uri = first_result['url']
                    print(f"   Data URI length: {len(data_uri)}")
                    if ',' in data_uri:
                        header, data = data_uri.split(',', 1)
                        print(f"   Header: {header}")
                        print(f"   Data length: {len(data)}")
                        
                        # Try manual base64 decode to see if that's the issue
                        try:
                            import base64
                            decoded_data = base64.b64decode(data)
                            print(f"   Decoded data length: {len(decoded_data)}")
                            
                            # Try to save manually
                            temp_file = Path("/tmp/test_decode.jpg")
                            with open(temp_file, 'wb') as f:
                                f.write(decoded_data)
                            print(f"   Manual save successful: {temp_file}")
                            
                            # Try to validate manually
                            try:
                                from PIL import Image
                                img = Image.open(temp_file)
                                print(f"   Image size: {img.size}")
                                print(f"   Image format: {img.format}")
                                
                                # Check if it meets new validation criteria (100x100)
                                if img.width >= 100 and img.height >= 100:
                                    print("   ✅ Meets new validation criteria (100x100)")
                                else:
                                    print(f"   ❌ Too small for validation: {img.size} < 100x100")
                                    
                                temp_file.unlink()
                            except Exception as img_e:
                                print(f"   Image validation failed: {img_e}")
                                
                        except Exception as decode_e:
                            print(f"   Base64 decode failed: {decode_e}")
                    else:
                        print("   No comma found in data URI")
                
                # Try the second result (data URI)
                if len(results) > 1:
                    print("🔄 Trying second result (data URI)...")
                    second_result = results[1]
                    print(f"   Testing URL: {second_result['url'][:100]}...")
                    success2 = player_search._download_and_validate_image(second_result)
                    if success2:
                        print("✅ Data URI download successful!")
                        if 'temp_file' in second_result:
                            temp_path = second_result['temp_file']
                            if temp_path.exists():
                                size = temp_path.stat().st_size
                                print(f"   File size: {size} bytes")
                                temp_path.unlink()
                    else:
                        print("❌ Data URI download also failed")
        else:
            print("❌ No results found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_image_search()
