import os
import datetime
import sys
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from utils.map_dialog import MapDialog  # 导入地图选点对话框
from utils.exif_utils import set_photo_date_and_gps  # 导入用于修改Exif信息的工具


class ExifEditorApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        
           # 获取当前工作路径
        if getattr(sys, 'frozen', False):  # 如果是打包后的应用
            # 通过 sys._MEIPASS 获取打包后的临时路径
            icon_path = sys._MEIPASS + "\\photo\\icon.png"
        else:
            # 在开发环境中使用相对路径
            icon_path = "photo/icon.png"
        self.setWindowTitle("Exif信息修改工具")  # 设置窗口标题
        self.setGeometry(100, 100, 800, 600)  # 设置窗口大小和位置
        self.setWindowIcon(QtGui.QIcon(icon_path))  # 设置窗口图标
        self.setStyleSheet("background-color: #F4F4F4;")  # 设置背景色

        # 创建垂直布局
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)  # 增加整体间距，提升美观

        # 图片选择
        self.image_path_label = self.create_label("选择图片：")
        self.image_path_input = self.create_input()
        self.image_path_button = self.create_button("浏览", "#007AFF", self.select_image)

        image_layout = QtWidgets.QHBoxLayout()
        image_layout.addWidget(self.image_path_label)
        image_layout.addWidget(self.image_path_input)
        image_layout.addWidget(self.image_path_button)

        # 日期时间选择
        self.date_label = self.create_label("设置日期时间：")
        self.date_input = QtWidgets.QDateTimeEdit()
        self.date_input.setDateTime(datetime.datetime.now())
        self.date_input.setCalendarPopup(True)
        self.date_input.setStyleSheet("padding: 5px; font-size: 14px; border: 1px solid #ccc; border-radius: 5px;")

        date_layout = QtWidgets.QHBoxLayout()
        date_layout.addWidget(self.date_label)
        date_layout.addWidget(self.date_input)

        # GPS坐标选择
        self.gps_label = self.create_label("设置GPS坐标：")
        self.gps_input = self.create_input()
        self.map_button = self.create_button("地图选点", "#007AFF", self.open_map_dialog)

        gps_layout = QtWidgets.QHBoxLayout()
        gps_layout.addWidget(self.gps_label)
        gps_layout.addWidget(self.gps_input)
        gps_layout.addWidget(self.map_button)

        # 选择导出目录
        self.dest_label = self.create_label("选择导出目录：")
        self.dest_input = self.create_input()
        self.dest_button = self.create_button("浏览", "#007AFF", self.select_dest)

        dest_layout = QtWidgets.QHBoxLayout()
        dest_layout.addWidget(self.dest_label)
        dest_layout.addWidget(self.dest_input)
        dest_layout.addWidget(self.dest_button)

        # 执行修改按钮
        self.execute_button = self.create_button("应用修改", "#34C759", self.modify_exif)
        self.execute_button.setStyleSheet("background-color: #34C759; color: white; border-radius: 8px; padding: 15px;")

        # 将各布局添加到主布局中
        layout.addLayout(image_layout)
        layout.addLayout(date_layout)
        layout.addLayout(gps_layout)
        layout.addLayout(dest_layout)
        layout.addWidget(self.execute_button)

    def create_label(self, text):
        """创建标签控件"""
        label = QtWidgets.QLabel(text)
        label.setStyleSheet("font-size: 14px; color: #333;")
        return label

    def create_input(self):
        """创建输入框"""
        input_field = QtWidgets.QLineEdit()
        input_field.setStyleSheet("padding: 5px; font-size: 14px; border: 1px solid #ccc; border-radius: 5px;")
        return input_field

    def create_button(self, text, color, on_click_func):
        """创建按钮控件"""
        button = QtWidgets.QPushButton(text)
        button.setStyleSheet(f"background-color: {color}; color: white; border-radius: 8px; padding: 10px;")
        button.clicked.connect(on_click_func)
        return button

    def select_image(self):
        """选择图片文件"""
        image_path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Images (*.jpg *.jpeg *.png *.heic)")
        if image_path:
            self.image_path_input.setText(image_path)

    def select_dest(self):
        """选择导出目录"""
        dest_dir = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if dest_dir:
            self.dest_input.setText(dest_dir)

    def modify_exif(self):
        """应用修改Exif信息"""
        image_path = self.image_path_input.text()
        dest_dir = self.dest_input.text()
        date = self.date_input.dateTime().toPyDateTime()
        gps_coords = self.gps_input.text()
        need_gps = bool(gps_coords)

        if not os.path.isfile(image_path):
            QMessageBox.critical(self, "错误", "请选择有效的图片文件！")
            return

        if not os.path.isdir(dest_dir):
            QMessageBox.critical(self, "错误", "请选择有效的导出目录！")
            return

        try:
            set_photo_date_and_gps(image_path, date, gps_coords, need_gps, dest_dir)
            QMessageBox.information(self, "成功", "Exif信息修改完成！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发生错误：{e}")

    def open_map_dialog(self):
        """打开地图选点对话框"""
        self.map_dialog = MapDialog(self)
        self.map_dialog.coordinates_selected.connect(self.update_gps_input)
        self.map_dialog.exec_()

    def update_gps_input(self, lon, lat):
        """更新GPS输入框"""
        self.gps_input.setText(f"{lon}, {lat}")
