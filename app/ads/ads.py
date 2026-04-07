from typing import Dict, Any
from flask import current_app
from .providers import YandexRTBProvider, VKAdsProvider, MediaSniperProvider

#менеджер рекламы
class AdsManager:
    def __init__(self, app=None):
        self.providers = {}
        self.config = {}
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.config = app.config.get('ADS_CONFIG', {})

        #инициализируем провайдеров
        if self.config.get('yandex', {}).get('enabled'):
            self.providers['yandex'] = YandexRTBProvider(self.config['yandex'])

        if self.config.get('vk_ads', {}).get('enabled'):
            self.providers['vk_ads'] = VKAdsProvider(self.config['vk_ads'])

        if self.config.get('mediasniper', {}).get('enabled'):
            self.providers['mediasniper'] = MediaSniperProvider(self.config['mediasniper'])

        app.ads_manager = self

        @app.context_processor
        def inject_ads():
            return {
                'show_ad': self.show_ad,
                'ad_scripts': self.get_all_scripts()
            }

    def show_ad(self, position: str = 'default', provider: str = None) -> str:
        if not self.config.get('enabled', False):
            return ''

        #приоритет провайдеров: yandex | vk_ads | mediasniper
        active_providers = list(self.providers.keys())
        priority = ['yandex', 'vk_ads', 'mediasniper']
        active_priority = [p for p in priority if p in active_providers]

        if provider and provider in self.providers:
            return self.providers[provider].get_code(position)

        if not active_priority:
            return self._get_placeholder(position)

        #берём первый активный провайдер по приоритету
        selected = active_priority[0]
        return self.providers[selected].get_code(position)

    def get_all_scripts(self) -> str:
        scripts = []
        for provider in self.providers.values():
            script = provider.get_script()
            if script:
                scripts.append(script)
        return '\n'.join(scripts)

    #пока заглушка
    def _get_placeholder(self, position: str) -> str:
        if not self.config.get('show_placeholder', True):
            return ''

        return f'''
        <div class="ad-placeholder" data-position="{position}">
            <div class="ad-placeholder-content">
                <span>Рекламное место</span>
                <small>Свяжитесь с нами для размещения</small>
            </div>
        </div>
        '''