# Hinterview 🎡

A smart AI overlay that helps you solve LeetCode problems in real time. Press `F1` to generate tailored coding hints from Claude AI by scraping your screen and analyzing both the problem and your current code.

---

## ✨ Features

* 📸 OCR-based screen capture of LeetCode problem description and code
* 🤖 Integrates Claude 3.5 via API to generate hints without revealing full solutions
* ⌚ Always-on-top, semi-transparent overlay with keyboard shortcut
* 🔐 Secure API key handling and validation
* 🎯 No browser extensions or DOM scraping required

---

## 🚀 Quickstart

### 1. Clone the repo

```bash
git clone https://github.com/your-username/hinterview.git
cd hinterview
```

### 2. Set up a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
python hinterview.py
```

Enter your Claude API key when prompted.

---

## 🌐 Dependencies

Listed in `requirements.txt`:

```txt
requests>=2.31.0
pyautogui>=0.9.54
pyperclip>=1.8.2
pynput>=1.7.6
Pillow>=10.0.0
pytesseract>=0.3.10
opencv-python>=4.8.0
numpy>=1.24.0
```

Ensure that Tesseract-OCR is installed:

* macOS: `brew install tesseract`
* Ubuntu: `sudo apt install tesseract-ocr`
* Windows: [https://github.com/tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract)

---

## ⌨ Hotkeys

| Hotkey | Action                         |
| ------ | ------------------------------ |
| `F1`   | Toggle overlay + generate hint |

---

## 🔧 How It Works

1. Captures the screen and splits it into two regions: problem and code.
2. Extracts text using Tesseract OCR.
3. Sends the problem + code to Claude API with a structured prompt.
4. Displays a helpful hint in a Tkinter overlay.

---

## 📅 Example Use Cases

* Getting unstuck on a hard problem
* Confirming the pattern or approach
* Receiving subtle direction without spoilers

---

## 📄 License

MIT License © 2025 Andrew Huang

---

## 💡 Tips

* Run the app in one monitor while solving on another
* Debug screenshots are saved as `debug_problem_area.png` and `debug_code_area.png`
* Try changing the OCR configs in `LeetCodeScraper` if the text is misread
