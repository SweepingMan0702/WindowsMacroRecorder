"""
單一執行個體管理器
使用 Windows Named Mutex 偵測是否已有執行中的程序，
並透過本地 Socket 將「喚醒」指令傳送給已存在的執行個體。
"""
import socket
import threading
import ctypes
from utils.logger import logger

# 唯一標識符（應用程式固定使用此 Port，同一機器上不應衝突）
_IPC_PORT = 47823
_IPC_HOST = "127.0.0.1"
_WAKE_MSG = b"WAKE_UP"


def _is_port_in_use(port: int) -> bool:
    """檢查指定 Port 是否已被佔用（即已有執行個體在監聽）"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        try:
            s.connect((_IPC_HOST, port))
            return True
        except (ConnectionRefusedError, OSError):
            return False


def try_bring_existing_to_front() -> bool:
    """
    嘗試通知已存在的執行個體跳出到前景。
    回傳 True 表示已有執行個體並成功傳送喚醒訊號；
    回傳 False 表示沒有已存在的執行個體。
    """
    if not _is_port_in_use(_IPC_PORT):
        return False

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            s.connect((_IPC_HOST, _IPC_PORT))
            s.sendall(_WAKE_MSG)
        return True
    except OSError as e:
        logger.warning(f"SingleInstance: 無法傳送喚醒訊號: {e}")
        return False


class SingleInstanceServer:
    """
    在背景執行的 IPC Socket 伺服器，監聽喚醒指令。
    當收到喚醒訊號時，呼叫 on_wake_up 回呼（在主執行緒中透過 Qt Signal 執行）。
    """

    def __init__(self, on_wake_up_callback):
        self._callback = on_wake_up_callback
        self._server_sock = None
        self._thread = None
        self._running = False

    def start(self):
        """啟動 IPC 伺服器（在背景執行緒中監聽）"""
        try:
            self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_sock.bind((_IPC_HOST, _IPC_PORT))
            self._server_sock.listen(5)
            self._server_sock.settimeout(1.0)
            self._running = True

            self._thread = threading.Thread(target=self._serve, daemon=True, name="SingleInstanceIPC")
            self._thread.start()
            logger.info(f"SingleInstanceServer: 已在 Port {_IPC_PORT} 啟動監聽")
        except OSError as e:
            logger.error(f"SingleInstanceServer: 無法綁定 Port {_IPC_PORT}: {e}")

    def _serve(self):
        """背景執行緒：持續接受連線並處理喚醒指令"""
        while self._running:
            try:
                conn, _ = self._server_sock.accept()
                with conn:
                    conn.settimeout(1.0)
                    data = conn.recv(64)
                    if data.strip() == _WAKE_MSG:
                        logger.info("SingleInstanceServer: 收到喚醒訊號，將視窗帶到前景")
                        self._callback()
            except socket.timeout:
                continue
            except OSError:
                break

    def stop(self):
        """停止 IPC 伺服器"""
        self._running = False
        if self._server_sock:
            try:
                self._server_sock.close()
            except OSError:
                pass
