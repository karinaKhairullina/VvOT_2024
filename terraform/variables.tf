variable "cloud_id" {
    description = "ID облака Yandex Cloud"
    type = string
}

variable "folder_id" {
    description = "ID каталога Yandex Cloud"
    type = string
}

variable "tg_bot_key" {
    description = "Токен для доступа к Telegram Bot API"
    type = string
}

variable "key_file_path" {
  type        = string
  description = "Ключ сервисного аккаунта"
  default     = "~/.yc-keys/key.json"
}

variable "source_dir" {
  type        = string
  description = "Путь к директории для архивации"
  default     = "/Users/karina/Desktop/VvOT/src"
}

