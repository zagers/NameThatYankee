# ABOUTME: One-off utility to process 4th of July tribute images.
# ABOUTME: Converts screenshot and answer photos to optimized WEBP format.
import urllib.request
from pathlib import Path
from PIL import Image

def process():
    # 1. Process screenshot clue
    screenshot_path = Path("/Users/zagers/Downloads/Screenshot 2026-07-04 at 4.40.19 PM.png")
    clue_out = Path("images/clue-2026-07-04.webp")
    with Image.open(screenshot_path) as img:
        # Convert to RGB and save as optimized webp
        img.convert("RGB").save(clue_out, "WEBP", quality=85)
        print("Saved clue-2026-07-04.webp")

    # 2. Download and process answer photo
    answer_url = "https://upload.wikimedia.org/wikipedia/commons/d/da/George_Steinbrenner_-_New_York_Yankees_owner.jpg"
    temp_jpg = Path("temp_steinbrenner.jpg")
    answer_out = Path("images/answer-2026-07-04.webp")
    
    print("Downloading George Steinbrenner image...")
    req = urllib.request.Request(
        answer_url,
        headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    with urllib.request.urlopen(req) as response:
        with open(temp_jpg, "wb") as out_file:
            out_file.write(response.read())
    
    with Image.open(temp_jpg) as img:
        # Convert to RGB and save as optimized webp
        img.convert("RGB").save(answer_out, "WEBP", quality=85)
        print("Saved answer-2026-07-04.webp")
        
    if temp_jpg.exists():
        temp_jpg.unlink()

if __name__ == "__main__":
    process()
