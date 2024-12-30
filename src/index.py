import os
import json
import requests
import base64
from urls import *


# Отправка POST запросов
def send_post(url, headers=None, json_data=None):
    response = requests.post(url, headers=headers, json=json_data)
    if response.status_code == 200:
        return response.json()
    return None

# Получение объекта из бакета
def get_object_from_bucket(object_key):
    with open(os.path.join(MOUNT_POINT, object_key), "r") as file:
        return file.read()

# Обработка текста через гпт
def get_answer_from_gpt(question):
    instruction = get_object_from_bucket(BUCKET_OBJECT_KEY)
    if not instruction:
        return None

    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt",
        "messages": [
            {"role": "system", "text": instruction},
            {"role": "user", "text": question},
        ],
    }
    response = send_post(YC_API_GPT_URL, headers={"Authorization": f"Bearer {IAM_TOKEN}"}, json_data=data)
    if response:
        alternatives = response["result"]["alternatives"]
        final_alternatives = [alt for alt in alternatives if alt["status"] == "ALTERNATIVE_STATUS_FINAL"]
        return final_alternatives[0]["message"].get("text") if final_alternatives else None
    return None

# Распознавание текста с фото
def recognize_text(base64_image):
    data = {
        "content": base64_image,
        "mimeType": "image/jpeg",
        "languageCodes": ["ru", "en"],
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {IAM_TOKEN}",
        "x-folder-id": FOLDER_ID,
    }
    response = send_post(YC_API_OCR_URL, headers=headers, json_data=data)
    if response:
        text = response.get("result", {}).get("textAnnotation", {}).get("fullText", "")
        return text.replace("-\n", "").replace("\n", " ") if text else None
    return None

# Получения пути файла
def get_file_path(file_id):
    file_info = send_post(f"{TELEGRAM_API_URL}/getFile?file_id={file_id}")
    return file_info["result"]["file_path"] if file_info else None

# Получения изображения по пути
def get_image(file_path):
    file_url = f"{TELEGRAM_FILE_URL}/{file_path}"
    return requests.get(file_url).content

# Обработчик
def process_update(update):

    message = update["message"]
    chat_id = message["chat"]["id"]

    if "text" in message:
        text = message["text"]
        if text == "/start" or text == "/help":
            return send_message(chat_id,
                                "Я помогу подготовить ответ на экзаменационный вопрос по дисциплине 'Операционные системы'.\nПришлите мне фотографию с вопросом или наберите его текстом.")
        answer = get_answer_from_gpt(text)
        return send_message(chat_id, answer if answer else "Я не смог подготовить ответ на экзаменационный вопрос.")

    if "photo" in message:
        file_id = message["photo"][-1]["file_id"]
        file_path = get_file_path(file_id)

        image = get_image(file_path)
        base64_image = base64.b64encode(image).decode("utf-8")
        recognized_text = recognize_text(base64_image)
        if recognized_text:
            answer = get_answer_from_gpt(recognized_text)
            return send_message(chat_id, answer if answer else "Я не смог подготовить ответ на экзаменационный вопрос.")
        return send_message(chat_id, "Я не могу обработать эту фотографию.")

    return send_message(chat_id, "Я могу обработать только текстовое сообщение или фотографию.")


# Отправка сообщения
def send_message(chat_id, text):
    send_post(f"{TELEGRAM_API_URL}/sendMessage", json_data={"chat_id": chat_id, "text": text})


def handler(event, context):
    if not TG_API_KEY:
        return FUNC_RESPONSE

    try:
        update = json.loads(event["body"])
    except (KeyError, json.JSONDecodeError):
        return FUNC_RESPONSE

    process_update(update)
    return FUNC_RESPONSE
