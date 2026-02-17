import requests
import os
from dotenv import load_dotenv

load_dotenv()

HF_API_TOKEN = os.getenv("HF_API_TOKEN")

models = [
    "stabilityai/stable-diffusion-xl-base-1.0",
    "runwayml/stable-diffusion-v1-5",
    "black-forest-labs/FLUX.1-schnell"
]

endpoints = [
    "https://router.huggingface.co/models",
    "https://router.huggingface.co",
    "https://api.huggingface.co/models",
    "https://api-inference.huggingface.co/models"
]

print(f"Token present: {bool(HF_API_TOKEN)}")

for model in models:
    for endpoint in endpoints:
        url = f"{endpoint}/{model}"
        print(f"\nTesting {url}...")
        try:
            headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
            # Just a simple dry run request
            resp = requests.post(url, headers=headers, json={"inputs": "test"})
            print(f"Status: {resp.status_code}")
            if resp.status_code != 200:
                print(f"Error: {resp.text}")
            else:
                print("SUCCESS!")
                break
        except Exception as e:
            print(f"Exception: {e}")
