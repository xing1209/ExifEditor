import webbrowser
import requests
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFontMetrics
from utils import messages
from utils.map_dialog import MapDialog
from utils.exif_utils import *

class ButtonEvents:
    @staticmethod
    def restore_or_maximize_window(window):
        """处理最大化/恢复按钮点击事件"""
        if window.isMaximized():
            window.showNormal()  # 窗口如果不是最大化则显示为正常状态
            window.ui.pushButton_3.setIcon(QIcon(":/icons/iconPark-full-screen-two@1x.png"))  # 更新按钮图标为恢复图标
        else:
            window.showMaximized()  # 窗口如果不是最大化则最大化
            window.ui.pushButton_3.setIcon(QIcon(":/icons/iconPark-off-screen-two 1@1x.png"))  # 更新按钮图标为最小化图标
    
    @staticmethod
    def select_image(window):
        """选择图片文件"""
        try:
            window.append_text_to_browser(messages.FILE_LOADING) # 显示加载状态
            image_path, _ = QFileDialog.getOpenFileName(window, "选择图片", "", "Images (*.jpg *.jpeg *.png *.heic)")
            if image_path:  # 成功加载
                window.original_file_path = image_path  # 保存原始路径
                window.append_text_to_browser(messages.FILE_SUCCESS.format(image_path=image_path))
            elif image_path=="":    # 用户取消
                window.append_text_to_browser(messages.FILE_CANCELLED)
                return
            else: # 加载失败
                window.append_text_to_browser(messages.FILE_FAILURE)
                return
            
           # 加载图片并设置到 QGraphicsView
            scene = load_image_to_graphics_view(window, image_path)
            if not scene:   #图片显示失败
                window.append_text_browser(messages.IMAGE_SHOW_FAILURE)
                return
            
            #预览框显示
            display_image_in_view(window.ui.graphicsView_2, scene)

            #图片视图显示
            display_image_in_view(window.ui.graphicsView, scene)
            
            # 绑定EXIF信息
            info = parse_exif_info(window, image_path)
            window.ui.lineEdit.setText(info.get("FileName"))
            window.ui.label_3.setText(info.get("FilePath"))
            window.ui.dateTimeEdit.setDateTime(info.get("DateTime"))
            window.ui.label_4.setText(info.get("LocationName", "未知位置"))
            window.original_gps_coords = info.get("Location", "无 GPS 数据")
            window.ui.textEdit.setPlainText(info.get("Note", ""))

        except Exception as e:
            window.append_text_to_browser(messages.EXIF_ERROR.format(e=e))

    @staticmethod
    def select_dest(window):
        """选择导出目录"""
        dest_dir = QFileDialog.getExistingDirectory(window, "选择导出目录")
        return dest_dir
    

    def toggle_page(window):
        """在页面 0 和 1 之间切换"""
        try:
            # 切换页面
            if window.current_page_index == 0:
                window.ui.stackedWidget.setCurrentIndex(1)
                window.current_page_index = 1
                window.ui.pushButton_6.setIcon(QIcon(":/icons/视图菜单_空心@1x.png"))  # 更新按钮图标为空心图标
                window.append_text_to_browser(messages.VIEW_PHOTO)                                               
            else:
                window.ui.stackedWidget.setCurrentIndex(0)
                window.current_page_index = 0
                window.ui.pushButton_6.setIcon(QIcon(":/icons/视图菜单@1x.png"))  # 更新按钮图标为实心图标
                window.append_text_to_browser(messages.VIEW_EDITOR)

        except Exception as e:
                print(f"错误", f"切换页面失败：{e}")
                
    def open_map_dialog(window):
        """打开地图选点对话框"""
        # 先检查是否已打开图片
        if not hasattr(window, 'original_file_path'):
            QMessageBox.critical(window, "错误", "请先选择有效的图片！")
            return
        else: 
            try:
                window.map_dialog = MapDialog(window)
                # 连接对话框的信号到更新 GPS 的槽
                window.map_dialog.coordinates_selected.connect(
                    lambda lon, lat: ButtonEvents.update_gps_input(window, lon, lat)
                )
                window.map_dialog.exec_()
                window.append_text_to_browser(messages.POSITION_SELECTED.format(position = window.original_position_coords))

            except Exception as e:
                window.append_text_to_browser(messages.GPS_ERROR.format(e=e))


    def update_gps_input(window, lon, lat):
        """更新GPS输入框，显示地名"""

        # 将经纬度转换为地名
        try:
            location = window.geolocator.reverse((lat, lon), language="ch")
            if location:
                # 解析 location.raw 并重新拼接格式
                address_components = location.raw.get("address", {})
                # country = address_components.get("country", "")
                state = address_components.get("state", "")
                city = address_components.get("city", address_components.get("town", ""))
                suburb = address_components.get("suburb", "")
                road = address_components.get("road", "")
                house_number = address_components.get("house_number", "")

                # 重新拼接格式
                address = f"{state}, {city}, {suburb}, {road} {house_number}".strip(", ").replace(" ,", ",")
            else:
                address = "未知位置"
        except Exception as e:
            address = "地名获取失败"

        # 更新 GPS 坐标
        window.original_gps_coords = f"{lon}, {lat}"

        # 更新到 search_bar，显示完整地址
        window.map_dialog.search_bar.setText(f"{address}")

        # 更新到 label_4，限制显示长度
        label = window.ui.label_4
        font_metrics = QFontMetrics(label.font())
        max_width = label.width()
        
        # 计算适合的文本
        truncated_address = font_metrics.elidedText(address, Qt.ElideRight, max_width)

        # 设置到标签
        label.setText(truncated_address)
        window.original_position_coords = address

    def check_network():
        """检查网络连接"""
        try:
            response = requests.get('https://www.aliyundrive.com', timeout=5)
            return response.status_code == 200
        except requests.ConnectionError:
            return False
        
    def open_aliyun_drive_link(window):
        """跳转到阿里云盘的网页"""
        if ButtonEvents.check_network():
            webbrowser.open("https://www.aliyundrive.com/drive/home")
            window.append_text_to_browser(messages.OPEN_ALIYUN_DRIVE)
        else:
            window.append_text_to_browser(messages.NET_ERROR)

    def save(window):
        """保存 Exif 信息"""
        # 保存前检查是否已打开图片
        if not hasattr(window, 'original_file_path'):
            QMessageBox.critical(window, "错误", "请先选择有效的图片！")
            return
        else: 
            try:
                file_name = window.ui.lineEdit.text()
                image_path = window.original_file_path  # 使用存储的原始路径
                date = window.ui.dateTimeEdit.dateTime().toPyDateTime()
                gps_coords = window.original_gps_coords
                note = window.ui.textEdit.toPlainText()

                # 修改 Exif 信息
                img = convert_image_format(image_path)
                exif_bytes = set_photo_date_and_gps(img, date, gps_coords, note)

                #选择导出目录
                dest_dir = ButtonEvents.select_dest(window)
                if not dest_dir:
                    QMessageBox.warning(window, "警告", "未选择导出目录！")
                    return
                
                # 弹出确认是否保存的对话框
                save_confirm = QMessageBox.question(
                    window,
                    "确认保存",
                    "是否保存？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )

                # 判断用户选择
                if save_confirm == QMessageBox.Yes:
                    # 执行保存操作
                    dest_path = os.path.join(dest_dir, os.path.splitext(file_name)[0] + '.jpg')

                    # 保存图片并应用修改后的EXIF数据
                    img.save(dest_path, "jpeg", exif=exif_bytes, quality=100)
                    window.append_text_to_browser(messages.SAVE_SUCCESS.format(path=dest_path))
                else:
                    window.append_text_to_browser(messages.SAVE_CANCELLED)
            except Exception as e:
                window.append_text_to_browser(messages.SAVE_ERROR.format(e=e))

    # def open_aliyun_drive(window):
    #         """尝试自动查找并打开本地阿里云盘客户端或跳转到网页"""
    #         aliyun_drive_path = ButtonEvents.find_aliyun_drive_path()

    #         if aliyun_drive_path and os.path.exists(aliyun_drive_path):
    #             try:
    #                 subprocess.Popen(aliyun_drive_path)
    #             except Exception as e:
    #                 print(f"无法启动阿里云盘客户端：{e}")
    #                 webbrowser.open("https://www.aliyundrive.com/drive/home")
    #         else:
    #             # 如果未找到本地客户端，跳转到网页
    #             webbrowser.open("https://www.aliyundrive.com/drive/home")

    #     def find_aliyun_drive_path(window):
    #         """自动查找阿里云盘客户端安装路径"""
    #         # 尝试从注册表获取路径
    #         try:
    #             with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall") as key:
    #                 for i in range(winreg.QueryInfoKey(key)[0]):
    #                     subkey_name = winreg.EnumKey(key, i)
    #                     with winreg.OpenKey(key, subkey_name) as subkey:
    #                         try:
    #                             display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
    #                             if "阿里云盘" in display_name:  # 查找阿里云盘的注册表项
    #                                 install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
    #                                 return os.path.join(install_location, "AliyunDrive.exe")
    #                         except FileNotFoundError:
    #                             continue
    #         except Exception:
    #             pass

    #         # 常见安装路径扫描
    #         common_paths = [
    #             r"C:\Program Files\Aliyun\AliyunDrive\AliyunDrive.exe",
    #             r"C:\Program Files (x86)\Aliyun\AliyunDrive\AliyunDrive.exe",
    #             os.path.expanduser(r"~\AppData\Local\Programs\AliyunDrive\AliyunDrive.exe"),
    #         ]
    #         for path in common_paths:
    #             if os.path.exists(path):
    #                 return path

    #         # 如果未找到，返回 None
    #         return None