# ![Logótipo](https://github.com/BacalhauNaBrisa/srt_encoding_converter/raw/main/assets/logo.png)

# 🎬 SRTool

A free, open-source Streamlit Cloud web app for `.srt` subtitle manipulation.  
Built to help you:

- ✅ **Detect and convert subtitle encoding to UTF-8**
- ⏱ **Shift subtitle timestamps forward or backward**

---

## 🚀 Live App

👉 [Launch the Web App](https://srtool.streamlit.app)

---

## 📂 Features

### 🧪 1. Encoding Converter

- Upload any `.srt` file
- Detects common encodings like:
  - `ASCII`, `Windows-1252`, `ISO-8859-1`, `UTF-8`, `UTF-8-SIG`, etc.
- Converts file to UTF-8 if needed
- Downloads the converted version

### ⏱ 2. Timestamp Shifter

- Upload a `.srt` file encoded in UTF-8 or UTF-8-SIG
- Choose direction:
  - ➕ Shift timestamps **forward**
  - ➖ Shift timestamps **backward**
- Input time in the format: `HH:MM:SS,mmm` (e.g., `00:00:01,000`)
- Downloads the new shifted file

---

## 🛠️ Local Installation

```bash
git clone https://github.com/BacalhauNaBrisa/srt_encoding_converter.git
cd srt_encoding_converter
pip install -r requirements.txt
streamlit run app.py
