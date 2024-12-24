import os
import json
import requests
import boto3

FUNC_RESPONSE = {'statusCode': 200, 'body': ''}

TG_API_KEY = os.environ.get("TG_API_KEY")
YANDX_GPT_API_KEY = os.environ.get("API_KEY")
BUCKET_NAME = os.environ.get("BUCKET_NAME")
OBJECT_KEY = os.environ.get("BUCKET_OBJECT")
ACCESS_KEY = os.environ.get("ACCESS_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TG_API_KEY}"


def send_message(chat_id, text):
    try:
        payload = {'chat_id': chat_id, 'text': text}
        response = requests.post(url=f'{TELEGRAM_API_URL}/sendMessage', json=payload)
        if response.status_code != 200:
            return None
    except Exception as e:
        return None

def get_instruction_from_storage():
    s3_client = boto3.client(
        "s3",
        endpoint_url="https://storage.yandexcloud.net",
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=OBJECT_KEY)
        instruction = response['Body'].read().decode('utf-8')
        return instruction
    except Exception as e:
        return None

# Функция для запроса к YandexGPT API
def get_answer_from_yandex_gpt(prompt, instruction):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {YANDX_GPT_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": f"{instruction}\nВопрос: {prompt}",
        "temperature": 0.7,
        "max_tokens": 1000
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json().get("text", "").strip()
        else:
            return None
    except Exception as e:
        return None


def process_image_with_yandex_ocr(image_url):
    ocr_url = "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze"
    headers = {
        "Authorization": f"Api-Key {YANDX_GPT_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "analyze_specs": [{
            "content": image_url,
            "features": [{"type": "TEXT_DETECTION"}]
        }]
    }
    try:
        response = requests.post(ocr_url, headers=headers, json=payload)
        if response.status_code == 200:
            ocr_result = response.json()
            text = " ".join([annotation['description'] for annotation in ocr_result['results'][0]['textAnnotations']])
            return text
        else:
            return None
    except Exception as e:
        return None

def process_update(update):

    message = update['message']
    chat_id = message['chat']['id']

    # Обработка текстового сообщения
    if 'text' in message:
        text = message['text'].strip()

        if text == "/start" or text == "/help":
            response_text = (
                "Я помогу подготовить ответ на экзаменационный вопрос по дисциплине 'Операционные системы'. "
                "Пришлите мне фотографию с вопросом или наберите его текстом."
            )
            send_message(chat_id, response_text)
            return

        if text == "":
            send_message(chat_id, "Пожалуйста, отправьте текст вопроса.")
            return

        instruction = get_instruction_from_storage()
        if instruction is None:
            send_message(chat_id, "Не удалось получить инструкцию для обработки.")
            return

        response_text = get_answer_from_yandex_gpt(text, instruction)
        if response_text:
            send_message(chat_id, response_text)
        else:
            send_message(chat_id, "Я не смог подготовить ответ на экзаменационный вопрос.")

    # Обработка фотографии
    elif 'photo' in message:
        if len(message['photo']) > 1:
            send_message(chat_id, "Я могу обработать только одну фотографию.")
            return

        # Получаем URL фотографии
        file_id = message['photo'][-1]['file_id']
        file_url = f"https://api.telegram.org/bot{TG_API_KEY}/getFile?file_id={file_id}"
        response = requests.get(file_url)
        file_path = response.json().get('result', {}).get('file_path')
        if not file_path:
            send_message(chat_id, "Не удалось получить фотографию.")
            return

        image_url = f"https://api.telegram.org/file/bot{TG_API_KEY}/{file_path}"

        # Обработка OCR на фотографии
        text_from_image = process_image_with_yandex_ocr(image_url)
        if text_from_image:
            instruction = get_instruction_from_storage()
            if instruction is None:
                send_message(chat_id, "Не удалось получить инструкцию для обработки.")

            response_text = get_answer_from_yandex_gpt(text_from_image, instruction)
            if response_text:
                send_message(chat_id, response_text)
            else:
                send_message(chat_id, "Я не смог подготовить ответ на экзаменационный вопрос.")
        else:
            send_message(chat_id, "Я не могу обработать эту фотографию.")

    # Обработка других типов сообщений
    else:
        send_message(chat_id, "Я могу обработать только текстовое сообщение или фотографию.")

# Основная функция для работы с Webhook
def handler(event, context):
    if TG_API_KEY is None:
        return FUNC_RESPONSE

    try:
        update = json.loads(event['body'])
    except (KeyError, json.JSONDecodeError) as e:
        return FUNC_RESPONSE

    # Обработка обновления от Telegram
    process_result = process_update(update)
    print(process_result)

    return FUNC_RESPONSE
