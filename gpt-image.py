import os
import openai
import requests

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Define your prompt
prompt = "A futuristic cityscape at sunset"

# Generate the image
response = openai.Image.create(
    model="gpt-image-1",
    prompt=prompt,
    n=1,
    size="512x512"
)

# Extract the image URL from the response
image_url = response['data'][0]['url']

# Download and save the image
image_data = requests.get(image_url).content
with open("generated_image.png", "wb") as f:
    f.write(image_data)

print("Image successfully generated and saved as 'generated_image.png'")
