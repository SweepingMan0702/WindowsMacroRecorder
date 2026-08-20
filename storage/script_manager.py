import json, os
from typing import Optional
from models.script import MacroScript
from utils.logger import logger

class ScriptManager:
    def __init__(self, scripts_dir: Optional[str] = None):
        self.scripts_dir = scripts_dir or os.path.join(os.getcwd(), "scripts")
        os.makedirs(self.scripts_dir, exist_ok=True)

    @staticmethod
    def save_script(script: MacroScript, file_path: str) -> bool:
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(script.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"腳本成功儲存至: {file_path}")
            return True
        except Exception as e:
            logger.error(f"儲存腳本失敗 ({file_path}): {e}")
            return False

    @staticmethod
    def load_script(file_path: str) -> MacroScript:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            script = MacroScript.from_dict(data)
            logger.info(f"腳本成功載入: {file_path}")
            return script
        except Exception as e:
            logger.error(f"載入腳本失敗 ({file_path}): {e}")
            raise