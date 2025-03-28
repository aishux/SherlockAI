from io import BytesIO
from openai import AzureOpenAI
from PIL import Image
from moviepy import VideoFileClip, CompositeVideoClip, ImageSequenceClip
import requests
import json
import os
from langchain_openai import AzureChatOpenAI
from openai import AzureOpenAI
from avatarGeneration import main as generate_avatar
import shutil

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = "https://aishu-m8q3ed4m-swedencentral.cognitiveservices.azure.com/"
AZURE_OPENAI_KEY = "028qDuTdd4Z5y0nsdbVns8ZesZeQxt4NEQmW33BObOs7cLO9gIteJQQJ99BCACfhMk5XJ3w3AAAAACOGWE1L"
AZURE_DEPLOYMENT_NAME = "gpt-4o"

# Initialize the Azure Chat Model in LangChain
llm = AzureChatOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    openai_api_version="2025-01-01-preview",
    azure_deployment=AZURE_DEPLOYMENT_NAME,
    api_key=AZURE_OPENAI_KEY,
)

client = AzureOpenAI(
    api_version="2025-01-01-preview",  
    api_key="30GVlMjbtF3pTphG8eJ6a7eXLJ3BbasyZZnRS1YRSLRR0qilthcYJQQJ99BCACfhMk5XJ3w3AAAAACOGj4uE",  
    azure_endpoint="https://nikhi-m8q67l88-swedencentral.openai.azure.com/"
)

# Step 1: Scene Breakdown using GPT-4o
def breakdown_scene(scene_description):
    system_prompt = """You are a cinematic storyboard assistant. Your task is to break down the given natural language crime scene into a maximum of 5 brief frame descriptions suitable for image generation. Make it consistent and use repetetive desriptions to maintain consistency in image generation.

    Rules:
    - All frames must be visually descriptive and adhere strictly to responsible AI guidelines.
    - Avoid any content that may be considered inappropriate or offensive. Rephrase violent or sensitive terms: 
    - Use "red liquid" instead of "blood"
    - Do not mention words like "kill", "murder", or "victim"
    - Do not label people as "criminal", "suspect", or "victim"
    - Create a storyline with named characters. Use names like Alex, Jamie, or Taylor to refer to characters consistently across frames.
    - Use a single consistent background and mention it in every scene in full text so as to provide these images to dalle-3 can generate consistent backgrounds.
    - Each scene description must be detailed, but concise (1 to 2 sentences), and separated by `///`.
    - Avoid meta-language, just list the scenes."""

    response = llm.invoke(f"{system_prompt}\n\n{scene_description}")
    content = response.content
    return content.split("\n")

# Generate Crime Scene Video
def generate_crime_video(scene_description, log_placeholder):
    try:
        scenes = [scene.strip() for scene in "".join(breakdown_scene(scene_description)).split("///") if scene.strip()]

        image_paths = []
        counter = 1

        # Step 2: Generate images for each scene
        for scene in scenes:
            log_placeholder.info(f"🎨 Generating image {counter}/{len(scenes)}...")
            try:
                result = client.images.generate(
                    model="dall-e-3",
                    prompt=f"Hand-drawn watercolor sketch style. Scene: {scene.strip()}",
                    n=1
                )
                json_response = json.loads(result.model_dump_json())
                image_url = json_response["data"][0]["url"]

                image_dir = os.path.join(os.curdir, 'generated_content')

                # If the directory doesn't exist, create it
                if not os.path.isdir(image_dir):
                    os.mkdir(image_dir)

                image_name = f"generated_image_{counter}.png"

                # Initialize the image path (note the filetype should be png)
                image_path = os.path.join(image_dir, image_name)

                # Retrieve the generated image
                image_url = json_response["data"][0]["url"]  # extract image URL from response
                generated_image = requests.get(image_url).content  # download the image
                with open(image_path, "wb") as image_file:
                    image_file.write(generated_image)

                image_paths.append(image_path)
            except Exception as e:
                continue

            counter += 1

        log_placeholder.info("🗣️ Generating narration...")

        # Step 3: Generate narration text
        narration_response = llm.invoke(f"This is For educational purpose. Summarize the scene in speech with tone of describing. The text should not result in audio output more than 30-40 secs. {scene_description}. JUST PURE TEXT NO EXPLANATIONS").content

        # Avatar generation logic can go here if needed (optional)
        log_placeholder.info("👤 Generating avatar...")
        avatar_video_name = generate_avatar(narration_response)

        avatar_clip = VideoFileClip(avatar_video_name).resized(0.25)
        avatar_clip_duration = avatar_clip.duration
        avatar_clip = avatar_clip.with_position(("right", "bottom"))

        log_placeholder.info("🎬 Stitching video...")

        # Step 4: Create video from images
        video_blob = BytesIO()
        fps_value = len(image_paths) / avatar_clip_duration

        scene_clip = ImageSequenceClip(image_paths, fps=fps_value)

        scene_clip.write_videofile("generated_content/scene_enact.mp4", codec="libx264", audio=False)

        scene_clip_video = VideoFileClip("generated_content/scene_enact.mp4")

        final_video = CompositeVideoClip([scene_clip_video, avatar_clip])
        final_video.write_videofile("generated_content/final_pip_output.mp4", codec="libx264")

        with open("generated_content/final_pip_output.mp4", "rb") as video_file:
            video_blob.write(video_file.read())

        video_blob.seek(0)
        shutil.rmtree("generated_content")  # Clean up directory

        return video_blob

    except Exception as e:
        log_placeholder.error(f"❌ Error: {str(e)}")
        return None
