import os
import sys
import traceback

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QFont

from app.main_window import MainWindow
from utils.windows import enable_dpi_awareness
from utils.logger import logger
from utils.single_instance import SingleInstanceServer, try_bring_existing_to_front


def global_exception_hook(exctype, value, tb):
    err_msg = "".join(traceback.format_exception(exctype, value, tb))
    logger.critical(f"未捕獲的嚴重例外狀況:\n{err_msg}")

    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle("應用程式錯誤")
    msg_box.setText("發生未預期的系統錯誤！")
    msg_box.setInformativeText("請確認系統權限或檢視日誌檔 (logs/macro_recorder.log) 以取得詳細資訊。")
    msg_box.setDetailedText(err_msg)
    msg_box.exec()


def main():
    enable_dpi_awareness()
    sys.excepthook = global_exception_hook

    # ── 單一執行個體檢查 ────────────────────────────────────────
    # 若已有執行中的實例，傳送喚醒訊號後直接退出
    if try_bring_existing_to_front():
        logger.info("偵測到程式已在執行，已喚醒原視窗，本次啟動結束。")
        sys.exit(0)

    # ── 正常啟動 ────────────────────────────────────────────────
    app = QApplication(sys.argv)
    app.setApplicationName("WindowsMacroRecorder")

    font = QFont("Microsoft JhengHei UI", 10)
    app.setFont(font)

    logger.info("Windows 巨集錄製器應用程式啟動")
    window = MainWindow()

    # 啟動單一執行個體 IPC 伺服器，收到喚醒訊號時將視窗帶到前景
    # 使用 Qt Signal 安全地切回主執行緒執行 UI 操作
    from PySide6.QtCore import QMetaObject, Qt
    ipc_server = SingleInstanceServer(
        on_wake_up_callback=lambda: QMetaObject.invokeMethod(
            window, "show_normal_and_raise", Qt.ConnectionType.QueuedConnection
        )
    )
    ipc_server.start()

    # 程式退出時停止 IPC 伺服器
    app.aboutToQuit.connect(ipc_server.stop)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()