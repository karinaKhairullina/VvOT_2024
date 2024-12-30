import os

TG_API_KEY = os.getenv("TG_API_KEY")
IAM_TOKEN = os.getenv("IAM_TOKEN")
FOLDER_ID = os.getenv("FOLDER_ID")
MOUNT_POINT = os.getenv("MOUNT_POINT")
BUCKET_OBJECT_KEY = os.getenv("BUCKET_OBJECT")

TELEGRAM_API_HOST = "https://api.telegram.org"
TELEGRAM_API_URL = f"{TELEGRAM_API_HOST}/bot{TG_API_KEY}"
TELEGRAM_FILE_URL = f"{TELEGRAM_API_HOST}/file/bot{TG_API_KEY}"
YC_API_OCR_URL = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText"
YC_API_GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

FUNC_RESPONSE = {"statusCode": 200, "body": ""}