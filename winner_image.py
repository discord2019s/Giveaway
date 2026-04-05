# winner_image.py
import json
import os

IMAGE_SETTINGS_FILE = "winner_image_settings.json"

current_image = {
    "name": None,
    "url": None,
    "type": None,
    "send_mode": "private"
}

def load_image_settings():
    global current_image
    if os.path.exists(IMAGE_SETTINGS_FILE):
        try:
            with open(IMAGE_SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                current_image = data
        except:
            pass

def save_image_settings():
    with open(IMAGE_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(current_image, f, indent=4, ensure_ascii=False)

def get_winner_image():
    return current_image

def set_winner_image(name: str, url: str, image_type: str, send_mode: str = None):
    global current_image
    current_image = {
        "name": name,
        "url": url,
        "type": image_type,
        "send_mode": send_mode if send_mode else current_image.get("send_mode", "private")
    }
    save_image_settings()

def set_send_mode(mode: str):
    global current_image
    current_image["send_mode"] = mode
    save_image_settings()

def clear_winner_image():
    global current_image
    current_image = {
        "name": None,
        "url": None,
        "type": None,
        "send_mode": "private"
    }
    save_image_settings()

load_image_settings()