import os
from PIL import Image
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QDateTime, Qt
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QGraphicsScene, QSizePolicy
from geopy.geocoders import Nominatim
import piexif
import pillow_heif

from utils import messages

def set_photo_date_and_gps(img, date, gps_coords=None, note=""):
    """
    修改图片的日期和GPS信息。
    
    参数：
        image_path (str): 图片文件路径（支持JPEG和HEIC格式）。
        date (datetime): 新的日期时间对象。
        gps_coords (str, 可选): GPS坐标字符串，格式为 "纬度,经度"（例如 "30.0,120.0"）。
        need_gps (bool): 是否需要添加GPS信息。
        note(str): 图片备注。

    异常：
        如果出现任何错误，抛出异常。
    """

    exif_dict = get_exif_data(img)
    
    try:
        # 设置新的日期时间信息
        date_str = date.strftime("%Y:%m:%d %H:%M:%S")
        exif_dict['0th'][piexif.ImageIFD.DateTime] = date_str
        exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = date_str
        exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = date_str

        # 如果需要更新GPS信息
        if gps_coords != "无 GPS 数据":
            # 分割并解析GPS坐标字符串
            lat, lon = map(float, gps_coords.split(', '))
            gps_ifd = {
                piexif.GPSIFD.GPSLatitudeRef: 'N' if lat >= 0 else 'S',
                piexif.GPSIFD.GPSLatitude: _convert_to_deg_min_sec(abs(lat)),
                piexif.GPSIFD.GPSLongitudeRef: 'E' if lon >= 0 else 'W',
                piexif.GPSIFD.GPSLongitude: _convert_to_deg_min_sec(abs(lon)),
            }
            exif_dict['GPS'] = gps_ifd  # 添加到EXIF的GPS字段中
        
        # 如果备注存在，添加到 EXIF 的 UserComment 字段
        if note != "":
            exif_dict['Exif'][piexif.ExifIFD.UserComment] = note.encode('utf-8')  # 保存备注信息
        
        # 转换EXIF字典为字节
        exif_bytes = piexif.dump(exif_dict)
        return exif_bytes
    
    except Exception as e:
        # 抛出任何捕获的异常
        raise e
    

def convert_heic_to_jpeg(image_path):
    """
    将HEIC格式的图片转换为Pillow支持的JPEG格式。

    参数：
        image_path (str): HEIC文件路径。

    返回：
        Image: 转换后的Pillow Image对象。
    """
    heif_file = pillow_heif.read_heif(image_path)  # 读取HEIC文件
    image = Image.frombytes(
        heif_file.mode,
        heif_file.size,
        heif_file.data,
        "raw",
        heif_file.mode,
        heif_file.stride,
    )
    return image


def _convert_to_deg_min_sec(value):
    """
    将GPS坐标的十进制表示转换为度、分、秒的格式。

    参数：
        value (float): 十进制表示的坐标值。

    返回：
        list: 转换后的度、分、秒格式（元组表示分子和分母）。
    """
    deg = int(value)  # 度
    min = int((value - deg) * 60)  # 分
    sec = (value - deg - min / 60) * 3600  # 秒
    return [(deg, 1), (min, 1), _convert_to_rational(sec)]


def _convert_to_rational(number):
    """
    将浮点数转换为分数表示。

    参数：
        number (float): 待转换的数值。

    返回：
        tuple: 分子和分母的元组表示。
    """
    denominator = 1000000  # 固定分母以确保高精度
    numerator = int(number * denominator)
    return (numerator, denominator)

def convert_image_format(image_path):
    """
        通用图片格式转换方法。

        参数：
            image_path (str): 输入图片路径（支持 HEIC、JPEG 等格式）。
            
        返回：
            img。

        异常：
            如果转换失败，抛出异常。
    """
    try:
        # 检查文件格式并处理HEIC文件
        if image_path.lower().endswith('.heic'):
            # 将HEIC文件转换为JPEG格式
            img = convert_heic_to_jpeg(image_path)
            img = img.convert('RGB')
        else:
            # 打开其他格式的图片
            img = Image.open(image_path)

        # 如果图片模式是RGBA（带透明通道），转换为RGB
        if img.mode == 'RGBA':
            img = img.convert('RGB')

        # 确保图片格式为JPEG，必要时转换
        if img.format != 'JPEG':
            img = img.convert('RGB')
            img = img.copy()  # 复制图片以移除潜在的只读限制
        return img
    
    except Exception as e:
        print(f"图片格式转换失败：{e}")
        raise e

#设置图片到 QGraphicsView
def load_image_to_graphics_view(window, image_path):
    pixmap = QPixmap(image_path)
    if pixmap.isNull():
        # QMessageBox.critical(window, "错误", "无法加载图片，请选择有效的图片文件")
        return False
    else:
        # 设置图片到 QGraphicsView
        scene = QGraphicsScene()
        scene.addPixmap(pixmap)
        return scene

def get_exif_data(img):
    """
    获取图片的 EXIF 数据。
    
    参数：
        img (PIL.Image): 打开的 PIL.Image 对象。
    
    返回：
        dict: 图片的 EXIF 数据字典。如果图片没有 EXIF 数据，返回空字典结构。
    """
    try:
        # 尝试加载 EXIF 数据
        exif_dict = piexif.load(img.info.get('exif', b''))
        return exif_dict
    except Exception as e:
        print(f"EXIF 数据为空, 已自动新建。")
        # 返回一个空的 EXIF 数据结构
        return {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}
    

def parse_exif_info(window,image_path):
    """
    提取文件名称、存储位置、拍摄日期、拍摄地点以及备注。
    
    参数：
        image_path (str): 图片的文件路径。
        
    返回：
        dict: 提取的必要信息。
    """

    required_info = {}

    # 获取文件名称
    required_info["FileName"] = os.path.basename(image_path)

    # 获取存储位置
    file_path = os.path.dirname(image_path)
    MAX_LENGTH = 30
    if len(file_path) > MAX_LENGTH:
        file_path = file_path[:MAX_LENGTH] + "..."  # 截取并加上省略号
    required_info["FilePath"] = file_path

    # 打开图片并获取 EXIF 信息
    try:
        # 尝试加载 EXIF 数据
        img = Image.open(image_path)
        exif_data = piexif.load(img.info.get('exif', b''))  # 获取 EXIF 数据
    except Exception as e:
        # print(f"EXIF 数据为空, 已自动新建。")
        window.append_text_to_browser(messages.EXIF_EMPTY)
        exif_data = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "thumbnail": None}

    # 提取拍摄日期
    try:
        # EXIF 标签 36867 对应拍摄日期 (DateTimeOriginal)
        datetime_original = exif_data.get("Exif", {}).get(piexif.ExifIFD.DateTimeOriginal, b"").decode()
        if datetime_original:
            date_time = QDateTime.fromString(datetime_original, "yyyy:MM:dd hh:mm:ss")
            required_info["DateTime"] = date_time if date_time.isValid() else QDateTime()
        else:
            # 默认设置为 1901 年
            default_date = QDateTime.fromString("1901:01:01 00:00:00", "yyyy:MM:dd hh:mm:ss")
            required_info["DateTime"] = default_date
    except Exception as e:
        # window.append_text_to_browser(messages.DATE_ERROR)
        default_date = QDateTime.fromString("1901:01:01 00:00:00", "yyyy:MM:dd hh:mm:ss")
        required_info["DateTime"] = default_date

    # 提取 GPS 信息
    try:
        gps_info = exif_data.get("GPS", {})
        if gps_info:
            # 提取纬度和经度
            lat = gps_info.get(piexif.GPSIFD.GPSLatitude)
            lat_ref = gps_info.get(piexif.GPSIFD.GPSLatitudeRef, b"N").decode()
            lon = gps_info.get(piexif.GPSIFD.GPSLongitude)
            lon_ref = gps_info.get(piexif.GPSIFD.GPSLongitudeRef, b"E").decode()

            if lat and lon:
                latitude = _convert_gps_to_decimal(lat, lat_ref)
                longitude = _convert_gps_to_decimal(lon, lon_ref)

                # 使用 Geopy 获取地名
                geolocator = Nominatim(user_agent="photo_exif_app")
                location = geolocator.reverse((latitude, longitude), timeout=10)
                required_info["Location"] = f"{latitude}, {longitude}"
                required_info["LocationName"] = location.address if location else "未知位置"
            else:
                required_info["Location"] = "无 GPS 数据"
                required_info["LocationName"] = "未知位置"
        else:
            required_info["Location"] = "无 GPS 数据"
            required_info["LocationName"] = "未知位置"
    except Exception as e:
        # window.append_text_to_browser(messages.GPS_ERROR)
        required_info["Location"] = "无 GPS 数据"
        required_info["LocationName"] = "未知位置"

 # 提取备注信息
    try:
        # 尝试从 EXIF 的 UserComment 字段获取备注
        user_comment = exif_data.get("Exif", {}).get(piexif.ExifIFD.UserComment, b"").decode(errors="ignore").strip()
        required_info["Note"] = user_comment if user_comment else ""
    except Exception as e:
        # print(f"解析备注信息时发生错误: {e}")
        required_info["Note"] = ""

    return required_info


def _convert_gps_to_decimal(gps_data, ref):
    """
    将 EXIF GPS 数据转换为十进制格式。

    参数：
        gps_data (list): EXIF GPS 数据（度、分、秒格式）。
        ref (str): 坐标参考（N, S, E, W）。

    返回：
        float: GPS 坐标的十进制表示。
    """
    try:
        degrees = gps_data[0][0] / gps_data[0][1]
        minutes = gps_data[1][0] / gps_data[1][1]
        seconds = gps_data[2][0] / gps_data[2][1]

        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

        # 如果是南半球或西经，需要取负值
        if ref in ['S', 'W']:
            decimal = -decimal

        return decimal
    except Exception as e:
        print(f"GPS 数据转换错误: {e}")
        return 0.0

def display_image_in_view(view, scene):
    """
    在指定的 QGraphicsView 中显示图片，自动等比缩放并填充视图区域，支持窗口大小调整。
    :param view: QGraphicsView 对象
    :param scene: QGraphicsScene 对象
    """
    # 设置场景到视图
    view.setScene(scene)

    # 清空样式表，移除背景样式
    view.setStyleSheet("border:none;")
    
    # 设置居中对齐
    view.setAlignment(Qt.AlignCenter)
    
    view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)


    # 调整视图以适应场景大小
    def fit_image():
        """调整视图以适应场景"""
        view.fitInView(scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    # 重写 QGraphicsView 的 resizeEvent 方法
    def resize_event(event):
        """在窗口调整大小时更新视图内容"""
        fit_image()  # 确保图片大小根据窗口大小动态调整
        super(view.__class__, view).resizeEvent(event)  # 调用原始的 resizeEvent 方法

    view.resizeEvent = resize_event  # 替换为新的 resizeEvent 方法

    # 初次调用以适应视图
    fit_image()
