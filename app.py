import streamlit as st
import chardet
import io

st.set_page_config(page_title="SRT Encoding Converter", layout="centered")

# Logo
st.markdown(
    """
    <div style="text-align: center;">
        <img src="https://github.com/BacalhauNaBrisa/srt_encoding_converter/raw/main/assets/logo.png" alt="App Logo" width="200"/>
    </div>
    """,
    unsafe_allow_html=True
)

st.title("SRT Encoding Converter")

st.markdown("Upload a `.srt` subtitle file and this app will detect its encoding. If it's not in UTF-8, you'll be able to convert and download it.")

uploaded_file = st.file_uploader("📤 Upload your .srt file", type=["srt"])

if uploaded_file:
    # Read a sample of the file to detect encoding
    raw_data = uploaded_file.read()
    detection = chardet.detect(raw_data)
    detected_encoding = detection.get("encoding", "Unknown")
    confidence = detection.get("confidence", 0)

    st.write(f"**Detected Encoding:** `{detected_encoding}` (Confidence: {confidence:.2f})")

    #if detected_encoding.lower() != "utf-8":
    if detected_encoding.lower() not in ("utf-8", "utf-8-sig"):

        st.warning("The file is not in UTF-8 encoding.")
        
        if st.button("🔁 Convert to UTF-8"):
            try:
                decoded_text = raw_data.decode(detected_encoding)
                utf8_bytes = decoded_text.encode("utf-8")
                utf8_file = io.BytesIO(utf8_bytes)
                utf8_file.name = uploaded_file.name.replace(".srt", "_utf8.srt")

                st.success("File converted to UTF-8!")

                st.download_button(
                    label="📥 Download UTF-8 .srt file",
                    data=utf8_file,
                    file_name=utf8_file.name,
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"Conversion failed: {e}")
    else:
        st.success("✅ This file is already in UTF-8 encoding.")
