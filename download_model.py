"""
Script to download and extract the Vosk English model (en-us-0.22)
"""

import os
import sys
import zipfile
import argparse
import requests
from tqdm import tqdm

MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip"
MODEL_DIR = "assets/models"
MODEL_PATH = os.path.join(MODEL_DIR, "vosk-model-en-us-0.22")
ZIP_PATH = os.path.join(MODEL_DIR, "vosk-model-en-us-0.22.zip")


def download_file(url, destination):
    """Download a file with progress bar"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))

    with open(destination, 'wb') as file, tqdm(
        desc=os.path.basename(destination),
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)


def download_model():
    """Download and extract the Vosk model"""
    os.makedirs(MODEL_DIR, exist_ok=True)

    if os.path.exists(MODEL_PATH):
        print(f"Model already exists at {MODEL_PATH}")
        return True

    print(f"Downloading Vosk model from {MODEL_URL}")
    try:
        download_file(MODEL_URL, ZIP_PATH)
        print("Extracting model...")

        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            bad = zip_ref.testzip()
            if bad:
                raise zipfile.BadZipFile(f"Corrupt file detected: {bad}")
            zip_ref.extractall(MODEL_DIR)

        os.remove(ZIP_PATH)
        print(f"Model successfully downloaded and extracted to {MODEL_PATH}")
        return True

    except Exception as e:
        print(f"Error downloading model: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Vosk English model")
    parser.add_argument("--url", help="Custom model URL", default=MODEL_URL)
    args = parser.parse_args()

    success = download_model()
    sys.exit(0 if success else 1)