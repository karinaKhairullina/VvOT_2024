data "archive_file" "content" {
  type        = "zip"
  source_dir  = var.source_dir  # Директория для архивации
  output_path = "./build/hash.zip"  # Путь для сохранения архива
}

resource "local_file" "user_hash_file" {
  content  = data.archive_file.content.output_sha512  # Хэш архива
  filename = "../src/build/hash/user_hash.txt"  # Путь для хранения хэша
}

resource "yandex_function" "telegram_bot_function" {
  name               = "telegram-bot-function"
  description        = "Функция для обработки сообщений от Telegram бота"
  entrypoint         = "index.handler"
  memory             = "128"
  runtime            = "python312"
  service_account_id = yandex_iam_service_account.sa_telegram_bot.id
  user_hash          = data.archive_file.content.output_sha512
  execution_timeout  = "30"
  environment = {
    TELEGRAM_BOT_TOKEN = var.tg_bot_key
    FOLDER_ID          = var.folder_id
  }
  content {
    zip_filename = data.archive_file.content.output_path
  }
}

resource "telegram_bot_webhook" "telegram_bot_webhook" {
  url = "https://functions.yandexcloud.net/${yandex_function.telegram_bot_function.id}"
}

resource "yandex_storage_bucket" "telegram_bot_bucket" {
  bucket = "telegram-bot-bucket"
}

resource "yandex_storage_object" "yandexgpt_instruction" {
  bucket = yandex_storage_bucket.telegram_bot_bucket.id
  key    = "instruction.txt"
  source = "instruction.txt"
}

resource "yandex_iam_service_account" "sa_telegram_bot" {
  name = "sa-telegram-bot"
}

resource "yandex_resourcemanager_folder_iam_member" "sa_telegram_bot_storage_viewer_iam" {
  folder_id = var.folder_id
  role      = "storage.viewer"
  member    = "serviceAccount:${yandex_iam_service_account.sa_telegram_bot.id}"
}

resource "null_resource" "delete_webhook" {
  triggers = {
    tg_bot_key = var.tg_bot_key
  }

  provisioner "local-exec" {
    command = "curl -s -X POST https://api.telegram.org/bot${var.tg_bot_key}/deleteWebhook"
  }

  lifecycle {
    prevent_destroy = false
  }
}
