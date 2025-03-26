from openai import AzureOpenAI
import os
import requests
from PIL import Image
import json

client = AzureOpenAI(
    api_version="2025-01-01-preview",  
    azure_endpoint="https://aishu-m8q3ed4m-swedencentral.cognitiveservices.azure.com/",
    api_key="028qDuTdd4Z5y0nsdbVns8ZesZeQxt4NEQmW33BObOs7cLO9gIteJQQJ99BCACfhMk5XJ3w3AAAAACOGWE1L" 
)

result = client.images.generate(
    model="dall-e-3", 
    prompt = "Do only as instructed. Now generate a single portrait sketch of a muscular man in his early 30s with a square jawline, stubble, and short buzzed hair. He is wearing a tank top, revealing a tattoo on his right shoulder. His eyes are focused, and his expression is serious. Plain background.",
    n=1

)

json_response = json.loads(result.model_dump_json())

# Set the directory for the stored image
image_dir = os.path.join(os.curdir, 'images')

# If the directory doesn't exist, create it
if not os.path.isdir(image_dir):
    os.mkdir(image_dir)

# Generate a unique filename by checking existing files
index = 1
while os.path.exists(os.path.join(image_dir, f"img{index}.png")):
    index += 1

image_path = os.path.join(image_dir, f"img{index}.png")

# Retrieve the generated image
image_url = json_response["data"][0]["url"]  # extract image URL from response
generated_image = requests.get(image_url).content  # download the image
with open(image_path, "wb") as image_file:
    image_file.write(generated_image)

# Display the image in the default image viewer
image = Image.open(image_path)
image.show()


'''
Prompts used: 

1. Do only as instructed. Now generate a single portrait sketch of a young woman in her early 30s with sharp facial features, high cheekbones, wavy shoulder-length hair, wearing a leather jacket. She has deep-set green eyes and a small scar on her left eyebrow. Plain background.

2. Do only as instructed. Now generate a single portrait sketch of an elderly man in his late 60s with a thin frame, sunken cheeks, and short gray hair. He has thick glasses, a neatly trimmed mustache, and wears a turtleneck sweater. His expression is thoughtful. Plain background.

3. Do only as instructed. Now generate a single portrait sketch of a teenage boy with a slim build, short curly hair, and freckles. He is wearing a baseball cap and a hoodie. His eyes are bright, and he has a slight smirk on his face. Plain background.

4. Do only as instructed. Now generate a single portrait sketch of a woman in her mid-40s with a round face, full lips, and dark brown eyes. She has long, braided hair and is wearing a patterned scarf around her neck. Her expression is calm and confident. Plain background.

5. Do only as instructed. Now generate a single portrait sketch of a muscular man in his early 30s with a square jawline, stubble, and short buzzed hair. He is wearing a tank top, revealing a tattoo on his right shoulder. His eyes are focused, and his expression is serious. Plain background.

'''