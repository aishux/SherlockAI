
#!/usr/bin/env python
# coding: utf-8

import json
import logging
import sys
import time
import uuid
import time

from azure.identity import DefaultAzureCredential
import requests

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
        format="[%(asctime)s] %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p %Z")
logger = logging.getLogger(__name__)


SPEECH_ENDPOINT = "https://ai-nikhilsmankani-8903.cognitiveservices.azure.com/"
PASSWORDLESS_AUTHENTICATION = False
API_VERSION = "2024-04-15-preview"

def _create_job_id():
    return uuid.uuid4()

def _authenticate():
    if PASSWORDLESS_AUTHENTICATION:
        credential = DefaultAzureCredential()
        token = credential.get_token('https://cognitiveservices.azure.com/.default')
        return {'Authorization': f'Bearer {token.token}'}
    else:
        SUBSCRIPTION_KEY = "36bzQyzStJA86qIe0XKmW4Pa98FX3veGfSVfvnNnkK461Ek5I7JfJQQJ99BCACfhMk5XJ3w3AAAAACOGmFWa"
        return {'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY}

def submit_synthesis(job_id: str, given_content: str):
    url = f'{SPEECH_ENDPOINT}/avatar/batchsyntheses/{job_id}?api-version={API_VERSION}'
    header = {
        'Content-Type': 'application/json'
    }
    header.update(_authenticate())

    payload = {
        'synthesisConfig': {
            "voice": 'en-US-JennyNeural'
        },
        "inputKind": "plainText",
        "inputs": [
            {
                "content": given_content,
            },
        ],
        "avatarConfig": {
            "customized": False,
            "talkingAvatarCharacter": "lori",
            "talkingAvatarStyle": "formal",
            "videoFormat": "mp4",
            "videoCodec": "h264",
            "subtitleType": "soft_embedded",
            "backgroundColor": "#FFFFFFFF",
        }
    }

    response = requests.put(url, json.dumps(payload), headers=header)
    if response.status_code < 400:
        logger.info('Batch avatar synthesis job submitted successfully')
        logger.info(f'Job ID: {response.json()["id"]}')
        return True
    else:
        logger.error(f'Failed to submit batch avatar synthesis job: [{response.status_code}], {response.text}')

def get_synthesis(job_id):
    url = f'{SPEECH_ENDPOINT}/avatar/batchsyntheses/{job_id}?api-version={API_VERSION}'
    header = _authenticate()

    response = requests.get(url, headers=header)
    if response.status_code < 400:
        logger.info('Get batch synthesis job successfully')
        logger.debug(response.json())
        if response.json()['status'] == 'Succeeded':
            logger.info(f'Batch synthesis job succeeded, download URL: {response.json()["outputs"]["result"]}')
        return response.json()
    else:
        logger.error(f'Failed to get batch synthesis job: {response.text}')

def list_synthesis_jobs(skip: int = 0, max_page_size: int = 100):
    """List all batch synthesis jobs in the subscription"""
    url = f'{SPEECH_ENDPOINT}/avatar/batchsyntheses?api-version={API_VERSION}&skip={skip}&maxpagesize={max_page_size}'
    header = _authenticate()

    response = requests.get(url, headers=header)
    if response.status_code < 400:
        logger.info(f'List batch synthesis jobs successfully, got {len(response.json()["values"])} jobs')
        logger.debug(response.json())
    else:
        logger.error(f'Failed to list batch synthesis jobs: {response.text}')

def download_video(video_url):
    logger.info(f'Downloading video from: {video_url}')
    video_name = f"generated_content/avatar_video_{int(time.time())}.mp4"
    header = _authenticate()
    response = requests.get(video_url, headers=header)
    if response.status_code < 400:
        with open(video_name, 'wb') as f:
            f.write(response.content)
        logger.info(f'Video downloaded successfully: {video_name}')
        return video_name
    else:
        logger.error(f'Failed to download video: {response.text}')
        return None


def main(user_content):
    job_id = _create_job_id()
    if submit_synthesis(job_id, user_content):
        while True:
            status = get_synthesis(job_id)
            if status['status'] == 'Succeeded':
                logger.info('batch avatar synthesis job succeeded')
                return download_video(status['outputs']['result']) 
            elif status['status'] == 'Failed':
                logger.error('batch avatar synthesis job failed')
                return False
            else:
                logger.info(f'batch avatar synthesis job is still running, status [{status['status']}]')
                time.sleep(5)