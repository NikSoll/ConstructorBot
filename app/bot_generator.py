import os
import shutil
import json
import logging
import subprocess
import sys
from typing import Dict, Any, Tuple, Optional
from pathlib import Path


class BotGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_dir = Path(__file__).parent.parent
        self.generated_dir = self.base_dir / 'bots' / 'generated'
        self.core_dir = self.base_dir / 'core'
        self.platforms_dir = self.base_dir / 'platforms'
        os.makedirs(self.generated_dir, exist_ok=True)

    def _normalize_platform(self, platform: str) -> str:
        mapping = {
            'tg': 'telegram',
            'telegram': 'telegram',
            'vk': 'vk',
            'max': 'max'
        }
        return mapping.get(platform, platform)

    def get_template_info(self, platform: str, bot_type: str) -> Dict:
        return {
            'platform': platform,
            'bot_type': bot_type,
            'name': f'{platform}_{bot_type}',
            'has_config': True,
            'has_database': True
        }
    #тут все копируется, собирается, чистится
    def generate_bot(self, platform: str, bot_type: str, bot_id: int, config: Dict[str, Any]) -> Tuple[bool, str, str]:
        try:
            bot_folder = f"{platform}_{bot_id}"
            bot_path = self.generated_dir / bot_folder

            if bot_path.exists():
                shutil.rmtree(bot_path)

            os.makedirs(bot_path, exist_ok=True)

            self._copy_core(bot_path, bot_type)
            self._copy_platform_adapter(bot_path, platform)
            self._copy_creds(bot_path, platform, bot_type)
            self._generate_config(bot_path, platform, bot_type, config)
            self._create_main_py(bot_path, platform, bot_type)
            self._create_requirements(bot_path, platform)

            exe_path = self._build_exe(bot_path, platform, bot_type)

            self._cleanup_source(bot_path)

            self.logger.info(f"Бот собран в .exe: {exe_path}")
            return True, "Бот создан", str(exe_path)

        except Exception as e:
            self.logger.error(f"Ошибка при создании бота: {e}")
            return False, str(e), ""
#пайинсталер вызывается
    def _build_exe(self, bot_path: Path, platform: str, bot_type: str) -> Path:
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'PyInstaller', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise Exception("PyInstaller не найден.")
            self.logger.info(f"PyInstaller версия: {result.stdout.strip()}")
        except Exception as e:
            raise Exception("PyInstaller не установлен.")

        bot_path_str = str(bot_path).replace('\\', '/')
        gui_py_path = bot_path / 'platforms' / platform / 'gui.py'

        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['{bot_path_str}/main.py'],
    pathex=['{bot_path_str}'],
    binaries=[],
    datas=[
        ('{bot_path_str}/config.json', '.'),
        ('{str(gui_py_path).replace(chr(92), "/")}', 'platforms/vk'),
    ],
    hiddenimports=[
        'vk_api',
        'vk_api.bot_longpoll',
        'vk_api.keyboard',
        'gspread',
        'google.auth',
        'google.oauth2.service_account',
        'googleapiclient',
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='bot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)
'''

        spec_path = bot_path / 'bot.spec'
        with open(spec_path, 'w', encoding='utf-8') as f:
            f.write(spec_content)

        self.logger.info("Начинаю сборку .exe (это может занять 1-2 минуты)...")
        result = subprocess.run([
            sys.executable, '-m', 'PyInstaller',
            str(spec_path)
        ], capture_output=True, text=True, cwd=bot_path)

        if result.returncode != 0:
            self.logger.error(f"Ошибка сборки: {result.stderr}")
            if result.stdout:
                self.logger.error(f"stdout: {result.stdout}")
            raise Exception(f"Ошибка PyInstaller: {result.stderr}")

        exe_file = bot_path / 'dist' / 'bot.exe'
        if not exe_file.exists():
            alt_exe = bot_path / 'bot.exe'
            if alt_exe.exists():
                exe_file = alt_exe
            else:
                raise Exception(f"Не найден собранный .exe")

        self.logger.info(f".exe собран: {exe_file}")
        return exe_file

#ут нужно удалить временные файлы типа всех паев. остается только 3 файла
    def _cleanup_source(self, bot_path: Path):
        exe_in_dist = bot_path / 'dist' / 'bot.exe'
        if exe_in_dist.exists():
            shutil.move(str(exe_in_dist), str(bot_path / 'bot.exe'))
            self.logger.info(f".exe перемещён в корень: {bot_path / 'bot.exe'}")

        keep_files = ['bot.exe', 'config.json', 'creds_*.json', 'bot.ico']
        for item in bot_path.iterdir():
            should_keep = False
            for pattern in keep_files:
                if item.name == pattern or item.name.endswith('.json'):
                    should_keep = True
                    break
            if not should_keep:
                if item.is_dir():
                    shutil.rmtree(item)
                    self.logger.info(f"Удалена папка: {item}")
                else:
                    item.unlink()
                    self.logger.info(f"Удалён файл: {item}")

#копирую ядро
    def _copy_core(self, bot_path: Path, bot_type: str):
        target_core = bot_path / 'core'
        os.makedirs(target_core, exist_ok=True)

        shutil.copy2(self.core_dir / 'base_bot.py', target_core / 'base_bot.py')
        shutil.copy2(self.core_dir / '__init__.py', target_core / '__init__.py')



        handlers_src = self.core_dir / 'handlers'
        handlers_dst = target_core / 'handlers'
        os.makedirs(handlers_dst, exist_ok=True)

        shutil.copy2(handlers_src / f'{bot_type}.py', handlers_dst / f'{bot_type}.py')

        handlers_init_content = f'''from .{bot_type} import {bot_type.capitalize()}Handlers

__all__ = [
    "{bot_type.capitalize()}Handlers"
]
        '''
        with open(handlers_dst / '__init__.py', 'w', encoding='utf-8') as f:
            f.write(handlers_init_content)

        db_src = self.core_dir / 'database'
        db_dst = target_core / 'database'
        os.makedirs(db_dst, exist_ok=True)

        shutil.copy2(db_src / 'base.py', db_dst / 'base.py')
        shutil.copy2(db_src / f'{bot_type}_db.py', db_dst / f'{bot_type}_db.py')

        db_init_content = f'''from .base import BaseDatabase
from .{bot_type}_db import {bot_type.capitalize()}Database

def get_db_for_type(bot_type: str, config: dict):
    dbs = {{
        "{bot_type}": {bot_type.capitalize()}Database
    }}
    db_class = dbs.get(bot_type)
    if db_class:
        return db_class(config)
    return None

__all__ = [
    "BaseDatabase",
    "{bot_type.capitalize()}Database",
    "get_db_for_type"
]
        '''
        with open(db_dst / '__init__.py', 'w', encoding='utf-8') as f:
            f.write(db_init_content)

        utils_src = self.core_dir / 'utils'
        utils_dst = target_core / 'utils'
        shutil.copytree(utils_src, utils_dst, dirs_exist_ok=True)
#опируею адаптер от нужной платформы
    def _copy_platform_adapter(self, bot_path: Path, platform: str):
        normalized = self._normalize_platform(platform)
        platform_src = self.platforms_dir / normalized

        if not platform_src.exists():
            self.logger.error(f"Файл платформы не найден: {platform_src}")
            return

        platform_dst = bot_path / 'platforms' / platform
        os.makedirs(platform_dst, exist_ok=True)

        #копируем adapter.py
        src_adapter = platform_src / 'adapter.py'
        if src_adapter.exists():
            shutil.copy2(src_adapter, platform_dst / 'adapter.py')
            self.logger.info(f"Адаптер скопирован в {platform_dst / 'adapter.py'}")
        else:
            self.logger.error(f"adapter.py не найден в {platform_src}")

        #опируем __init__.py
        src_init = platform_src / '__init__.py'
        if src_init.exists():
            shutil.copy2(src_init, platform_dst / '__init__.py')
            self.logger.info(f"Скопировано __init__.py в {platform_dst / '__init__.py'}")

        #копируем GUI
        src_gui = platform_src / 'gui.py'
        if src_gui.exists():
            shutil.copy2(src_gui, platform_dst / 'gui.py')
            self.logger.info(f"GUI скопирован в {platform_dst / 'gui.py'}")
        else:
            self.logger.warning(f"gui.py не найден в {src_gui}")

    #копируем creds.json
    def _copy_creds(self, bot_path: Path, platform: str, bot_type: str):
        creds_src = self.base_dir / 'creds.json'
        if creds_src.exists():
            creds_dst = bot_path / f'creds_{platform}_{bot_type}.json'
            shutil.copy2(creds_src, creds_dst)
            self.logger.info(f"Файл creds скопирован в {creds_dst}")
        else:
            self.logger.warning(f"creds.json не найден в {self.base_dir}")

    #создаем config.json из форм в креете
    def _generate_config(self, bot_path: Path, platform: str, bot_type: str, config: Dict[str, Any]):
        config_file = bot_path / 'config.json'
        config['platform'] = platform
        config['bot_type'] = bot_type
        config['created_at'] = str(bot_path.name)
        config['_config_path'] = str(bot_path)

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Конфигурация сохранена в {config_file}")
#создаем точку входа
    def _create_main_py(self, bot_path: Path, platform: str, bot_type: str):
        main_content = f'''#!/usr/bin/env python3
"""
{platform.upper()} бот типа {bot_type}
Сгенерировано TheMomBot
"""
import sys
from pathlib import Path
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))
from platforms.{platform}.gui import main
if __name__ == "__main__":
    main()
'''
        with open(bot_path / 'main.py', 'w', encoding='utf-8') as f:
            f.write(main_content)

#ут зависимости
    def _create_requirements(self, bot_path: Path, platform: str):
        normalized = self._normalize_platform(platform)

        requirements_map = {
            'telegram': '''aiogram==3.3.0
gspread==5.11.0
google-auth==2.23.0
python-dotenv==1.0.0''',
'vk': '''vk-api==11.9.9
gspread==5.11.0
google-auth==2.23.0
python-dotenv==1.0.0''',
'max': '''gspread==5.11.0
google-auth==2.23.0
python-dotenv==1.0.0'''
        }
        req = requirements_map.get(normalized, '# requirements')

        with open(bot_path / 'requirements.txt', 'w', encoding='utf-8') as f:
            f.write(req)

    def _get_adapter_class(self, platform: str) -> str:
        classes = {
            'telegram': 'TelegramBot',
            'tg': 'TelegramBot',
            'vk': 'VKBot',
            'max': 'MaxBotAdapter'
        }
        return classes.get(platform, 'BaseBot')