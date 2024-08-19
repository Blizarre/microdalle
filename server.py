import json
import os
import random
import string
import logging
from pathlib import Path
from threading import Thread
from typing import Optional
from datetime import datetime

import requests
from flask import Flask, request, send_file, jsonify
from openai import OpenAI
from openai import OpenAIError


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def generate_save_file_name(directory: Path) -> Path:
    current_time = datetime.now().strftime('%Y%m%d-%H%M%S')
    return directory / Path(
        f"{current_time}-{''.join(random.choices(string.ascii_letters, k=3))}.jpg"
    )


def api_key() -> Optional[str]:
    if os.path.isfile("key"):
        with open("key", encoding="utf=8") as fd:
            return fd.readline().strip()
    return None


def save_file(file_path: Path, metadata: dict, url: str):
    log.info("Saving file to %s", file_path)
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in r.iter_content():
                f.write(chunk)
    with open(file_path.with_suffix(".json"), "w", encoding='utf-8') as f:
        f.writelines(json.dumps(metadata, indent=4))

    log.info("File saved successfully %s", file_path)


def get_save_dir() -> Optional[Path]:
    directory_env = os.environ.get("SAVE_DIR")
    if directory_env:
        directory = Path(directory_env)
        log.info("Saving files to %s", directory)
        return directory

    log.info("Do not save files")
    return None

save_dir = get_save_dir()

client = OpenAI(api_key=api_key())

app = Flask(__name__)


@app.route("/generate", methods=["POST"])
def generate():
    # Get the text from the user
    prompt = request.json["prompt"]
    quality = request.json["quality"]
    size = request.json["size"]
    style = request.json["style"]

    log.info("Sending request to OpenAI with prompt: %s", prompt)

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            style=style,
            n=1,
        )
    except OpenAIError as e:
        return e.message, 500

    log.info("Response received: %s", response)
    url = response.data[0].url

    # Fire and Forget, It will download the file in the background. It is not production-ready, but that should
    # be enough for now
    if save_dir:
        file_path = generate_save_file_name(save_dir)
        metadata = {**response.data[0].model_dump(), "prompt":prompt}
        Thread(target=save_file, args=(file_path, metadata, url)).start()

    return jsonify(response.data[0].model_dump())


@app.route("/", methods=["GET"])
def index():
    return send_file("index.html", mimetype="text/html")


@app.route("/inprogress.gif", methods=["GET"])
def inprogress():
    return send_file("inprogress.gif", mimetype="image/gif")


if __name__ == "__main__":
    app.run(debug=True)
