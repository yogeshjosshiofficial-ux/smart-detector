# 🟢 Smart Detector V1.0 - By GSMYOGESH

A professional USB device detection and auto-driver installation utility for mobile repairing technicians. Developed by **Joshi Yogesh Gopal**.

## 🛠 Features
- **Instant Detection:** Scans USB ports for ADB, Fastboot, Qualcomm, and MediaTek devices.
- **Auto-Driver Install:** Automatically detects missing drivers (like QHSUSB_BULK) and installs them silently.
- **Smart Pop-ups:** Beautiful Light/Dark mode notifications on connection.
- **Deep WMI Scanning:** Catches MTP and Unknown devices that don't get COM ports.
- **Taskbar Integration:** Runs in the background with a custom GSMYOGESH icon.

## 🚀 Getting Started
1. **Clone the repo:** `git clone https://github.com/yourusername/smart-detector.git`
2. **Install requirements:** `pip install -r requirements.txt`
3. **Run:** `python smart_detector.py` (Must run as Administrator).

## 📦 Building the EXE
To pack this tool with its icon, use:
```bash
pyinstaller --onefile --windowed --icon "gsmyogesh.ico" --add-data "gsmyogesh.ico;." --name "Smart_Detector_V1" "smart_detector.py"
