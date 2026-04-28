import sys
import os
import time
import subprocess
import requests
import py7zr
import zipfile
import ctypes
import json
import serial.tools.list_ports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QSystemTrayIcon, QMenu, QStyle, QTabWidget, QTextEdit, QProgressBar,
                             QPushButton, QMessageBox, QInputDialog, QCheckBox, QComboBox, QFormLayout)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer

# Windows Taskbar Icon Fix
try:
    myappid = 'gsmyogesh.smartdetector.v1.0' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

CONFIG_FILE = "gsm_config.json"
DEFAULT_CONFIG = {"theme": "Dark", "popup_duration": 5000, "enable_popups": True, "auto_startup": False}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: return DEFAULT_CONFIG
    return DEFAULT_CONFIG

GLOBAL_CONFIG = load_config()

DRIVER_LINKS = {
    "QUALCOMM": "https://qdloader9008.com/wp-content/uploads/Qualcomm-HS-USB-QDLoader-9008-Driver.zip",
    "MEDIATEK": "https://dl1.infinity-box.com/00/pub/?dir=/soc-drivers/MTK/&uid=20571&file=MTK_SP_v3.0.1512.0_qcom-mtk_v4.0.1.6_cdc_pass_1111.7z",
    "SPRD": "https://dl1.infinity-box.com/00/pub/?dir=/soc-drivers/SPD-Unisoc/&uid=20571&file=SPRD_UNISOC_v4.21.39.134_pass_1111.7z",
}

MODERN_STYLESHEET = """
QMainWindow { background-color: #1e1e2e; }
QLabel { color: #cdd6f4; font-family: 'Segoe UI'; font-weight: bold; font-size: 14px;}
QTabWidget::pane { border: 1px solid #313244; background: #1e1e2e; border-radius: 5px; }
QTabBar::tab { background: #313244; color: #cdd6f4; padding: 10px 20px; font-weight: bold; border-top-left-radius: 5px; border-top-right-radius: 5px; }
QTabBar::tab:selected { background: #89b4fa; color: #11111b; }
QTableWidget { background-color: #181825; color: #cdd6f4; border: none; font-size: 13px; outline: none; }
QTableWidget::item { padding: 8px; border-bottom: 1px solid #313244; }
QHeaderView::section { background-color: #11111b; color: #a6adc8; padding: 10px; font-weight: bold; border: none; }
QTextEdit { background-color: #181825; color: #a6e3a1; border: 1px solid #313244; font-family: 'Consolas'; font-size: 13px; padding: 10px; }
QProgressBar { border: 2px solid #313244; border-radius: 6px; text-align: center; color: white; background: #181825; font-weight: bold;}
QProgressBar::chunk { background-color: #a6e3a1; border-radius: 4px; }
QPushButton { background-color: #89b4fa; color: #11111b; border-radius: 5px; padding: 10px; font-weight: bold; }
"""

class CustomToast(QWidget):
    def __init__(self, event, dev_type, port, desc):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QVBoxLayout()
        popup_bg = QWidget()
        inner_layout = QVBoxLayout(popup_bg)
        
        lbl_branding = QLabel("Smart Detector V1.0 By GSMYOGESH")
        lbl_event = QLabel(f"Device {event}")
        lbl_msg = QLabel(f"Type: {dev_type}\nPort/ID: {port}\nInfo: {desc}")
        lbl_footer = QLabel("POWER OF GSMYOGESH")
        
        lbl_msg.setWordWrap(True)
        
        if GLOBAL_CONFIG["theme"] == "Light":
            popup_bg.setStyleSheet("background-color: #f8f9fa; border: 2px solid #1e66f5; border-radius: 10px;")
            lbl_branding.setStyleSheet("font-weight: bold; font-size: 16px; color: #1e66f5;")
        else:
            popup_bg.setStyleSheet("background-color: #313244; border: 2px solid #89b4fa; border-radius: 10px;")
            lbl_branding.setStyleSheet("font-weight: bold; font-size: 16px; color: #89b4fa;")

        inner_layout.addWidget(lbl_branding, alignment=Qt.AlignmentFlag.AlignCenter)
        inner_layout.addWidget(lbl_event)
        inner_layout.addWidget(lbl_msg)
        inner_layout.addWidget(lbl_footer, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(popup_bg)
        self.setLayout(layout)
        self.setMinimumWidth(350)
        self.adjustSize()
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen.width() - self.width() - 30, screen.height() - self.height() - 70, self.width(), self.height())
        QTimer.singleShot(GLOBAL_CONFIG.get("popup_duration", 5000), self.close)

class DriverInstallerThread(QThread):
    progress = pyqtSignal(int, str) 
    log_msg = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, brand_keyword):
        super().__init__()
        self.brand = brand_keyword

    def run(self):
        url = DRIVER_LINKS.get(self.brand)
        dl_path = os.path.join(os.environ['TEMP'], f"{self.brand}_auto.zip" if ".zip" in url else f"{self.brand}_auto.7z")
        extract_path = os.path.join(os.environ['TEMP'], f"{self.brand}_ext")
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, stream=True)
            with open(dl_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk: file.write(chunk)

            os.makedirs(extract_path, exist_ok=True)
            if dl_path.endswith('.zip'):
                with zipfile.ZipFile(dl_path, 'r') as z: z.extractall(extract_path)
            else:
                with py7zr.SevenZipFile(dl_path, mode='r', password='1111') as z: z.extractall(path=extract_path)

            cmd = f'pnputil /add-driver "{extract_path}\\*.inf" /subdirs /install'
            subprocess.run(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.finished.emit(f"{self.brand} Driver Installed!")
        except Exception as e:
            self.log_msg.emit(f"Error: {str(e)}")

class DevicePoller(QThread):
    device_event = pyqtSignal(str, str, str, str)
    update_list = pyqtSignal(list)
    trigger_auto_install = pyqtSignal(str)
    unknown_device_detected = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.running = True
        self.known_devices = set()

    def run(self):
        while self.running:
            current_devices = set()
            try:
                for port in serial.tools.list_ports.comports():
                    desc = port.description.upper()
                    hwid = port.hwid.upper()
                    dev_type = "COM Port"
                    if "05C6" in hwid or "QHSUSB" in desc or "9008" in desc: dev_type = "Qualcomm EDL"
                    current_devices.add((dev_type, port.device, desc))
            except: pass
            
            added = current_devices - self.known_devices
            for dev in added: self.device_event.emit("CONNECTED", dev[0], dev[1], dev[2])
            self.known_devices = current_devices
            self.update_list.emit(list(current_devices))
            time.sleep(1.5)

class GsmResponsiveGui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Detector V1.0 - By GSMYOGESH")
        self.resize(950, 600)
        self.setStyleSheet(MODERN_STYLESHEET)
        
        self.active_toasts = []
        icon_path = resource_path("gsmyogesh.ico")
        if os.path.exists(icon_path): self.app_icon = QIcon(icon_path)
        else: self.app_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DriveNetIcon)
        self.setWindowIcon(self.app_icon)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Type", "Port", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.layout.addWidget(self.table)

        self.poller = DevicePoller()
        self.poller.device_event.connect(self.handle_event)
        self.poller.update_list.connect(self.refresh)
        self.poller.start()

    def handle_event(self, event, dev_type, port, desc):
        toast = CustomToast(event, dev_type, port, desc)
        self.active_toasts.append(toast)
        toast.show()

    def refresh(self, devices):
        self.table.setRowCount(0)
        for i, dev in enumerate(devices):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(dev[0]))
            self.table.setItem(i, 1, QTableWidgetItem(dev[1]))
            self.table.setItem(i, 2, QTableWidgetItem(dev[2]))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    window = GsmResponsiveGui()
    window.show()
    sys.exit(app.exec())
