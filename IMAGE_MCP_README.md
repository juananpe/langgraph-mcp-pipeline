# Image Generation MCP Server

This MCP (Model Context Protocol) server provides AI image generation capabilities using OpenAI's DALL-E models. It allows Claude Desktop (or other MCP clients) to generate, list, and inspect AI-generated images.

## Features

### Available Tools:

1. **`generate_image`** - Generate images using DALL-E
   - **Parameters:**
     - `prompt` (required): Text description of the image
     - `model` (optional): "dall-e-2" or "dall-e-3" (default: "dall-e-3")
     - `size` (optional): Image dimensions (default: "1024x1024")
     - `quality` (optional): "standard" or "hd" for DALL-E 3

2. **`list_generated_images`** - List all generated images in the directory
   - No parameters required
   - Shows filenames and file sizes

3. **`get_image_info`** - Get detailed information about a specific image
   - **Parameters:**
     - `filename` (required): Name of the image file to inspect

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration
Make sure your `.env` file contains your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Run the MCP Server
```bash
uv run main.py
```

The server will start and wait for MCP client connections (like Claude Desktop).

## Testing

### Standalone Testing
You can test the functionality without Claude by running:
```bash
python test_server.py
```

This will test all three tools and generate a sample image.

## Claude Desktop Integration

### 1. Add to Claude Configuration
Add the server configuration to your Claude Desktop config:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "image-generator": {
      "command": "uv",
      "args": ["run", "main.py"],
      "cwd": "/opt/agentes/langgraph-mcp-pipeline"
    }
  }
}
```

### 2. Restart Claude Desktop

### 3. Use the Tools
Once connected, you can ask Claude things like:

- "Generate an image of a sunset over mountains"
- "Create a picture of a futuristic city with flying cars"
- "List all the images I've generated"
- "Show me information about the latest generated image"

## Example Usage

```
You: "Generate an image of a cute robot painting a landscape"

Claude: I'll generate that image for you using the DALL-E 3 model.

[Claude calls generate_image tool with your prompt]

Result: Image successfully generated and saved as '/path/to/generated_A_cute_robot_painting_a_landscape.png'
```

## File Structure

```
├── server.py              # MCP server instance
├── main.py               # Server entry point
├── tools/
│   ├── __init__.py
│   └── image_tools.py    # Image generation tools
├── test_server.py        # Standalone testing script
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
└── claude_config.json    # Example Claude configuration
```

## Supported Image Formats

- **DALL-E 3:** 1024x1024, 1792x1024, 1024x1792
- **DALL-E 2:** 256x256, 512x512, 1024x1024

## Notes

- Generated images are saved with descriptive filenames based on the prompt
- All generated images are saved as PNG files
- The server requires an active OpenAI API key with DALL-E access
- Image generation costs apply based on OpenAI's pricing
