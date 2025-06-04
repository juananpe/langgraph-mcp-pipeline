import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import requests

# Set your OpenAI API key

# Define your prompt
prompt = "A futuristic cityscape at sunset"

# Generate the image
response = client.images.generate(model="dall-e-3",
prompt=prompt,
n=1,
size="1024x1024")

# Extract the image URL from the response
image_url = response.data[0].url

# Download and save the image
image_data = requests.get(image_url).content
with open("generated_image.png", "wb") as f:
    f.write(image_data)

print("Image successfully generated and saved as 'generated_image.png'")
