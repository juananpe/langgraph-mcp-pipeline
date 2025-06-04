#!/usr/bin/env python3
"""
Simple test script to verify the MCP server tools work correctly.
This can be run independently to test the image generation functionality.
"""

import os
from dotenv import load_dotenv
from tools.image_tools import generate_image, list_generated_images, get_image_info

def test_image_generation():
    """Test the image generation functionality."""
    print("Testing Image Generation MCP Server Tools")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    # Test 1: Generate an image
    print("\n1. Testing image generation...")
    result = generate_image(
        prompt="A cute robot holding a paintbrush",
        model="dall-e-3", 
        size="1024x1024"
    )
    print(result)
    
    # Test 2: List generated images
    print("\n2. Listing generated images...")
    images_list = list_generated_images()
    print(images_list)
    
    # Test 3: Get info about the most recent image
    print("\n3. Getting info about generated images...")
    import glob
    generated_files = glob.glob("generated_*.png")
    if generated_files:
        latest_file = max(generated_files, key=os.path.getmtime)
        info = get_image_info(latest_file)
        print(info)
    else:
        print("No generated images found to inspect.")

if __name__ == "__main__":
    test_image_generation()
