from datetime import datetime
import sys
from utils import messages
from utils.emitting_stream import EmittingStream
from ui.main_window import Ui_MainWindow
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QPoint
from utils.button_events import ButtonEvents
from utils.exif_editor import ExifEditorApp  # Add this import statement
from geopy.geocoders import Nominatim  # Import Nominatim

class InterfaceWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)  # 启用鼠标追踪
        self.lastPosition = QPoint(0, 0)  # 初始化最后的位置
        self.current_page_index = 0 # 初始化变量，记录当前页面索引
        # 初始化地理编码服务
        self.geolocator = Nominatim(user_agent="geo_app")


        # 连接按钮事件
        self.ui.pushButton_4.clicked.connect(self.close)
        self.ui.pushButton_2.clicked.connect(self.showMinimized)
        self.ui.pushButton_3.clicked.connect(lambda: ButtonEvents.restore_or_maximize_window(self))
        self.ui.pushButton_5.clicked.connect(lambda: ButtonEvents.select_image(self))
        self.ui.pushButton_6.clicked.connect(lambda: ButtonEvents.toggle_page(self))  # 绑定切换页面事件
        self.ui.pushButton_8.clicked.connect(lambda: ButtonEvents.open_aliyun_drive_link(self)) # 绑定打开阿里云盘链接事件
        self.ui.pushButton_11.clicked.connect(lambda: ButtonEvents.save(self))  # 绑定保存Exif信息事件
        self.ui.pushButton_20.clicked.connect(lambda: ButtonEvents.open_map_dialog(self))  # 绑定打开Exif编辑器事件


        # 创建输出流对象
        self.output_stream = EmittingStream()
        self.output_stream.text_written.connect(self.append_text_to_browser)
        # 重定向标准输出和错误输出
        sys.stdout = self.output_stream
        sys.stderr = self.output_stream

        # 显示初始提示信息
        self.append_text_to_browser(messages.INITIAL_WARNING)


    def mousePressEvent(self, event):
        """处理鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.lastPosition = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """处理鼠标移动事件"""
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.lastPosition)
            event.accept()

    def showEvent(self, event):
        """处理窗口显示事件"""
        super().showEvent(event)
        self.activateWindow()  # 激活窗口，确保它在顶层
    
    def append_text_to_browser(self, text):
        """将文本追加到 QTextBrowser"""
        # 根据内容类别添加样式
        if "错误" in text or "Error" in text:
            styled_text = f'<span style="color: #FF3B30; font-weight: bold;">{text}</span>'  # 红色加粗
        elif "警告" in text or "提示" in text or "Warning" in text:
            styled_text = f'<span style="color: #FF9500;">{text}</span>'  # 橙色
        else:
            styled_text = f'<span style="color: white;">{text}</span>'  # 白色

        # 获取时间戳并拼接完整 HTML
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_html = (
            f'<div>'
            f'<span style="color: #A0A0A0;">[{timestamp}]</span> {styled_text}'  # 时间戳和内容
            f'<hr style="border: 1px solid #E0E0E0; margin: 0;">'  # 分割线
            f'</div>'
        )

        # 插入内容
        self.ui.textBrowser.append(full_html)
        self.ui.textBrowser.verticalScrollBar().setValue(self.ui.textBrowser.verticalScrollBar().maximum())

    def closeEvent(self, event):
        """窗口关闭事件，恢复默认输出"""
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InterfaceWindow()
    window.show()
    sys.exit(app.exec_())