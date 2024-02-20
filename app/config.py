import yaml

# Настройки, необходимые для работы jwt токенов
SECRET_KEY = "AnqoxHROzzSDgrwCOUdY4SKZaD4dQB9-t2CLT5VqXbI"
ALGORITHM = "HS256"


# Загрузка файла конфигурации yaml
def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


settings = load_config()
