import asyncio
import logging
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from platforms.max.adapter import MaxBotAdapter
from core.utils.config_loader import load_config

async def main():
    logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    config = load_config(config_path)
    if not config:
        logging.error("Failed to load config")
        return
    bot = MaxBotAdapter(config)
    try:
        await bot.run()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Bot error: {e}")


if __name__ == "__main__":
    asyncio.run(main())