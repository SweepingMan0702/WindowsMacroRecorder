import ctypes, sys
from utils.logger import logger

def enable_dpi_awareness():
    if sys.platform == 'win32':
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2) # PROCESS_PER_MONITOR_DPI_AWARE
            logger.info("DPI 感知能力增強成功 (Per-Monitor v2)")
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception as e:
                logger.warning(f"無法設定 DPI 感知: {e}")

def is_admin() -> bool:
    """檢查目前應用程式是否以系統管理員權限執行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def get_screen_resolution():
    """取得主要螢幕的真實物理像素解析度 (寬, 高)"""
    try:
        user32 = ctypes.windll.user32
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        return width, height
    except Exception as e:
        logger.error(f"取得螢幕解析度失敗: {e}")
        return 1920, 1080

def release_all_keys(keyboard_controller=None, mouse_controller=None):
    try:
        from pynput.keyboard import Controller, Key
        kb = keyboard_controller if keyboard_controller else Controller()
        special_keys = [
            Key.shift, Key.shift_r,
            Key.ctrl, Key.ctrl_r,
            Key.alt, Key.alt_r,
            Key.cmd, Key.cmd_r
        ]
        for key in special_keys:
            try:
                kb.release(key)
            except Exception:
                pass
        logger.info("已安全發送關鍵組合鍵釋放訊號")
    except Exception as e:
        logger.error(f"釋放按鍵失敗: {e}")