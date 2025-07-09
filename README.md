# ![Logótipo](https://github.com/BacalhauNaBrisa/srt_encoding_converter/raw/main/assets/logo.png)

# SRTool

A free, open-source Streamlit Cloud app to manipulate subtitles.

---

## ✅ Features

### 🧪 Encoding Converter
- Detects subtitle encoding (e.g. ASCII, Windows-1252, ISO-8859-1, etc.)
- Converts to UTF-8 if needed
- Download the converted file

### ⏱ Timestamp Shifter
- Shift timestamps in `.srt` files forward or backward
- Input shift in the format `HH:MM:SS,mmm`
- Preserves subtitle content
- Download the shifted `.srt`

### 🔁 VTT to SRT Converter
- Upload `.vtt` (WebVTT) subtitle files
- Converts them to standard `.srt` format
- Download the new `.srt` instantly

---

## 🚀 Try It Now

👉 [Launch the Web App](https://srtool.streamlit.app)

---

## 📦 Install Locally

```bash
git clone https://github.com/BacalhauNaBrisa/srt_encoding_converter.git
cd srt_encoding_converter
pip install -r requirements.txt
streamlit run app.py
