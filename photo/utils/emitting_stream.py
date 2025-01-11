import sys
from PyQt5.QtCore import QObject, pyqtSignal

class EmittingStream(QObject):
    """自定义输出流，用于将终端输出重定向到 QTextBrowser"""
    text_written = pyqtSignal(str)  # 定义信号，传递字符串

    def write(self, text):
        if text.strip():  # 避免处理空行
            self.text_written.emit(text)

    def flush(self):
        pass  # 必须实现但可以为空