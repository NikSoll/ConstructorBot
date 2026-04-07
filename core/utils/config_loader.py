import json
import os
from typing import Dict, Any, Optional
import logging


def load_config(config_path: str) -> Optional[Dict[str, Any]]:
    try:
        if not os.path.exists(config_path):
            logging.error(f"Файл конфигурации не найден: {config_path}")
            return None

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        for key in ['token', 'admin_id', 'sheet_url']:#их парсит
            if key in config and config[key].startswith('${') and config[key].endswith('}'):
                env_var = config[key][2:-1]
                config[key] = os.getenv(env_var, config[key])
        return config

    except Exception as e:
        logging.error(f"Ошибка загрузки конфигурации: {e}")
        return None


def save_config(config: Dict[str, Any], config_path: str) -> bool:
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.error(f"Ошибка сохранения конфигурации: {e}")
        return False