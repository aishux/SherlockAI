from openai import AzureOpenAI
import os
import requests
from PIL import Image
import json
from io import BytesIO

client = AzureOpenAI(
    api_version="2025-01-01-preview",  
    azure_endpoint="https://aishu-m8q3ed4m-swedencentral.cognitiveservices.azure.com/",
    api_key="" 
)

def generate_forensic_sketch(user_query: str) -> Image.Image:

    result = client.images.generate(
        model="dall-e-3", 
        prompt = f"Forensic sketch of a suspect, drawn in realistic colourful pencil sketch style, facing forward, with strictly no extra elements like pencils or brushes. The person {user_query}. The sketch should look like it was drawn by a professional forensic artist for a police investigation. No background, white paper backdrop, only the head and shoulders visible, slightly shaded pencil work. Style: colourful, hyper-realistic, official police sketch, it should be front facing",
        n=1

    )

    json_response = json.loads(result.model_dump_json())

    # Retrieve the generated image
    image_url = json_response["data"][0]["url"] 

    image_bytes = requests.get(image_url).content
    return Image.open(BytesIO(image_bytes))