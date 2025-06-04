import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
from server import mcp

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@mcp.tool()
def generate_image(prompt: str, model: str = "dall-e-3", size: str = "1024x1024", quality: str = "standard") -> str:
    """
    Generate an image using OpenAI's DALL-E model and save it locally.
    
    Args:
        prompt: Text description of the image to generate
        model: Model to use ("dall-e-2" or "dall-e-3", default: "dall-e-3")
        size: Image size ("256x256", "512x512", "1024x1024", "1792x1024", "1024x1792" for DALL-E 3)
        quality: Image quality ("standard" or "hd" for DALL-E 3)
    
    Returns:
        A string describing the result and saved file path
    """
    try:
        # Generate the image
        response = client.images.generate(
            model=model,
            prompt=prompt,
            n=1,
            size=size,
            quality=quality if model == "dall-e-3" else "standard"
        )
        
        # Extract the image URL from the response
        image_url = response.data[0].url
        
        # Create a safe filename from the prompt
        safe_filename = "".join(c for c in prompt if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_filename = safe_filename.replace(' ', '_')[:50]  # Limit filename length
        filename = f"generated_{safe_filename}.png"
        
        # Download and save the image
        image_data = requests.get(image_url).content
        filepath = os.path.abspath(filename)
        
        with open(filepath, "wb") as f:
            f.write(image_data)
        
        return f"Image successfully generated and saved as '{filepath}'\nPrompt: {prompt}\nModel: {model}\nSize: {size}\nQuality: {quality}"
        
    except Exception as e:
        return f"Error generating image: {str(e)}"

@mcp.tool()
def list_generated_images() -> str:
    """
    List all generated image files in the current directory.
    
    Returns:
        A string listing all PNG files that start with 'generated_'
    """
    try:
        current_dir = os.getcwd()
        image_files = [f for f in os.listdir(current_dir) if f.startswith('generated_') and f.endswith('.png')]
        
        if not image_files:
            return "No generated images found in the current directory."
        
        result = "Generated image files:\n"
        for i, filename in enumerate(image_files, 1):
            filepath = os.path.join(current_dir, filename)
            size = os.path.getsize(filepath)
            result += f"{i}. {filename} ({size:,} bytes)\n"
        
        return result
        
    except Exception as e:
        return f"Error listing images: {str(e)}"

@mcp.tool()
def get_image_info(filename: str) -> str:
    """
    Get information about a specific image file.
    
    Args:
        filename: Name of the image file to inspect
    
    Returns:
        A string with file information including size, dimensions if possible
    """
    try:
        if not os.path.exists(filename):
            return f"File '{filename}' not found."
        
        file_size = os.path.getsize(filename)
        abs_path = os.path.abspath(filename)
        
        # Try to get image dimensions using PIL if available
        try:
            from PIL import Image
            with Image.open(filename) as img:
                width, height = img.size
                mode = img.mode
                return f"File: {filename}\nPath: {abs_path}\nSize: {file_size:,} bytes\nDimensions: {width}x{height}\nMode: {mode}"
        except ImportError:
            return f"File: {filename}\nPath: {abs_path}\nSize: {file_size:,} bytes\n(Install Pillow to see image dimensions)"
        except Exception:
            return f"File: {filename}\nPath: {abs_path}\nSize: {file_size:,} bytes\n(Could not read image dimensions)"
            
    except Exception as e:
        return f"Error getting image info: {str(e)}"
