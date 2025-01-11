from PyQt5 import QtWidgets, QtWebEngineWidgets, QtWebChannel, QtCore
from PyQt5.QtWidgets import QMessageBox
import requests

class MapDialog(QtWidgets.QDialog):
    """
    地图选点对话框，允许用户在地图上点击选择坐标或通过搜索地名定位。
    """
    coordinates_selected = QtCore.pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("地图选点")
        self.setGeometry(200, 200, 900, 650)
        self.setStyleSheet("background-color: #f4f4f4; font-family: Arial, sans-serif;")  # 设置整体背景和字体

        # 主布局
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # WebEngineView 用于显示地图
        self.web_view = QtWebEngineWidgets.QWebEngineView()
        self.channel = QtWebChannel.QWebChannel()
        self.web_view.page().setWebChannel(self.channel)
        self.channel.registerObject("qt", self)

        self.load_map()
        layout.addWidget(self.web_view)

        # 搜索框和按钮
        search_layout = QtWidgets.QHBoxLayout()
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("输入地名进行搜索")
        self.search_bar.setStyleSheet("padding: 10px; border-radius: 15px; border: 1px solid #ddd; background-color: #fff;")
        self.search_button = QtWidgets.QPushButton("搜索")
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border-radius: 15px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.search_button.clicked.connect(self.search_location)
        search_layout.addWidget(self.search_bar)
        search_layout.addWidget(self.search_button)

        layout.addLayout(search_layout)

        # 选定坐标按钮
        self.select_button = QtWidgets.QPushButton("选定坐标")
        self.select_button.setStyleSheet("""
            QPushButton {
                background-color: #34C759;
                color: white;
                border-radius: 15px;
                padding: 12px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #28a745;
            }
        """)
        self.select_button.clicked.connect(self.select_coordinates)
        layout.addWidget(self.select_button)

    @QtCore.pyqtSlot(float, float)
    def coordinatesSelected(self, lon, lat):
        """
        JavaScript 回调时调用，用于接收选定的坐标。
        """
        print(f"选取坐标: 经度={lon}, 纬度={lat}")
        self.coordinates_selected.emit(lon, lat)

    @QtCore.pyqtSlot()
    def closeDialog(self):
        """
        关闭对话框的方法，供 JavaScript 调用。
        """
        self.close()

    def load_map(self):
        """
        加载高德地图 HTML 页面，嵌入到 WebEngineView 中。
        """
        api_key = "3ae19a6382bf7b93aff090e8691e62b2"  # 替换为实际的高德地图API密钥
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>地图选点</title>
            <style>
                html, body, #container {{
                    width: 100%;
                    height: 100%;
                    margin: 0;
                    padding: 0;
                }}
            </style>
            <script src="https://webapi.amap.com/maps?v=1.4.15&key={api_key}&callback=initMap"></script>
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
        </head>
        <body>
            <div id="container"></div>
            <script>
                var map;
                var marker;

                function initMap() {{
                    // 初始化地图
                    map = new AMap.Map('container', {{
                        zoom: 12,
                        center: [121.4737, 31.2304] // 默认定位上海
                    }});

                    marker = new AMap.Marker();
                    map.add(marker);

                    // 地图点击事件，用于选择坐标
                    map.on('click', function(e) {{
                        marker.setPosition(e.lnglat);  // 在地图上放置标记
                        map.add(marker);

                        // 调用 PyQt 注册的方法传递坐标
                        if (window.qt && typeof window.qt.coordinatesSelected === 'function') {{
                            window.qt.coordinatesSelected(e.lnglat.lng, e.lnglat.lat);
                        }} else {{
                            console.error("qt.coordinatesSelected 方法不可用");
                        }}
                    }});
                }}

                // 初始化 Qt WebChannel
                new QWebChannel(qt.webChannelTransport, function(channel) {{
                    window.qt = channel.objects.qt;
                }});
            </script>
        </body>
        </html>
        """
        self.web_view.setHtml(html)

    def search_location(self):
        """
        搜索地名并在地图上定位。
        """
        query = self.search_bar.text().strip()
        if query:
            api_key = "3ae19a6382bf7b93aff090e8691e62b2"  # 替换为实际的高德地图API密钥
            url = f"https://restapi.amap.com/v3/place/text?key={api_key}&keywords={query}&city=""&output=JSON"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("pois"):
                    location = data["pois"][0]["location"]
                    lon, lat = map(float, location.split(","))

                    self.web_view.page().runJavaScript(f"""
                        map.setCenter([{lon}, {lat}]);
                        if (!marker) {{
                            marker = new AMap.Marker();
                        }}
                        marker.setPosition([{lon}, {lat}]);
                        map.add(marker);
                    """)
                else:
                    QMessageBox.warning(self, "提示", "未找到相关位置！")
            else:
                QMessageBox.critical(self, "错误", "地图API请求失败！")

    def select_coordinates(self):
        """
        从 JavaScript 获取当前选定的坐标，判断是否已选择坐标。
        """
        self.web_view.page().runJavaScript("""
            var pos = marker.getPosition();
            if (pos) {
                // 调用 PyQt 注册的 method 传递坐标
                window.qt.coordinatesSelected(pos.lng, pos.lat);
                // 关闭对话框
                window.qt.closeDialog();
            } else {
                // 提示用户先点击选点
                alert("请先在地图上点击选点！");
            }
        """)
