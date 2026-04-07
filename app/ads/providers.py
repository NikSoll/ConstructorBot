from abc import ABC, abstractmethod
from typing import Dict, Any


#баааазаааа для всех провайдеров
class BaseAdProvider(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', False)

    @abstractmethod
    def get_code(self, position: str = 'default') -> str:
        pass

    @abstractmethod
    def get_script(self) -> str:
        pass


#основная рекламная сеть яндекса
class YandexRTBProvider(BaseAdProvider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.block_id = config.get('block_id', '')
        self.placement_id = config.get('placement_id', '')
        self.types = config.get('types', {
            'default': 'floorAd',
            'header': 'floorAd',
            'footer': 'floorAd'
        })

    def get_code(self, position: str = 'default') -> str:
        if not self.enabled or not self.block_id:
            return ''

        #разные размеры для разных позиций
        sizes = {
            'header': '970x250',
            'sidebar': '300x600',
            'footer': '728x90',
            'default': '300x250'
        }

        #тип рекламы
        ad_type = self.types.get(position, self.types.get('default', 'floorAd'))

        return f'''
        <div id="yandex_rtb_{self.block_id}_{position}"></div>
        <script>
            window.yaContextCb = window.yaContextCb || [];
            window.yaContextCb.push(() => {{
                Ya.Context.AdvManager.render({{
                    blockId: "{self.block_id}",
                    renderTo: "yandex_rtb_{self.block_id}_{position}",
                    type: "{ad_type}",
                    platform: "desktop"
                }});
            }});
        </script>
        '''

    def get_script(self) -> str:
        if not self.enabled:
            return ''
        return '<script src="https://yandex.ru/ads/system/context.js" async></script>'


#рекламная сеть вк
class VKAdsProvider(BaseAdProvider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.placement_id = config.get('placement_id', '')

    def get_code(self, position: str = 'default') -> str:
        if not self.enabled or not self.placement_id:
            return ''

        sizes = {
            'header': '970x250',
            'sidebar': '300x250',
            'footer': '728x90',
            'default': '300x250'
        }
        size = sizes.get(position, '300x250')

        return f'''
        <div id="vk_ads_{self.placement_id}_{position}"></div>
        <script>
            (function(d, w, id) {{
                var js = d.createElement('script');
                js.src = 'https://vk.com/js/api/xd_connection.js?' + Math.random();
                js.onload = function() {{
                    VK.Retargeting.AdUnit({{
                        id: '{self.placement_id}',
                        format: '{size}'
                    }});
                }};
                d.getElementsByTagName('head')[0].appendChild(js);
            }})(document, window, 'vk_ads_{self.placement_id}');
        </script>
        '''

    def get_script(self) -> str:
        return ''


#натив реклама
class MediaSniperProvider(BaseAdProvider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.zone_id = config.get('zone_id', '')

    def get_code(self, position: str = 'default') -> str:
        if not self.enabled or not self.zone_id:
            return ''

        return f'''
        <div class="mediasniper-zone" data-zone="{self.zone_id}" data-position="{position}"></div>
        <script>
            (function(d, w, id) {{
                var js = d.createElement('script');
                js.src = 'https://cdn.mediasniper.ru/loader.js?' + id;
                js.async = true;
                d.getElementsByTagName('head')[0].appendChild(js);
            }})(document, window, '{self.zone_id}');
        </script>
        '''

    def get_script(self) -> str:
        return ''