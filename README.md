# Windows 巨集錄製器 (Mouse & Keyboard Macro Recorder)

強大、極簡且精準的 Windows 滑鼠鍵盤動作錄製與重放軟體。

## 功能特點
- 🖱️ **高精度滑鼠動態紀錄**：座標、左中右鍵點擊、雙擊、拖曳與滾輪動作。
- ⌨️ **全鍵盤按鍵錄製**：組合鍵、功能鍵與長按自動解析。
- 🚀 **極速重放大師**：0.1x ~ 100x 速度調節、固定間隔重放與無限循環。
- 🛡️ **緊急安全機制**：全域 ESC 快捷鍵一鍵中斷，防呆防鎖死。
- 📦 **單一檔 .exe 打包**：內建 PyInstaller 設定，雙擊即完成打包。

## 執行與打包
1. 安裝依賴：
   ```bash
   pip install -r requirements.txt
   ```
2. 啟動程式：
   ```bash
   python main.py
   ```
3. 打包成 Windows 免安裝單檔：
   雙擊執行 `build_exe.bat`，產出檔位於 `dist/WindowsMacroRecorder/`。