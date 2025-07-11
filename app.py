import streamlit as st
import chardet
import io
import re
from datetime import timedelta, datetime

st.set_page_config(page_title="SRTool", layout="centered")

# Logo at top
st.markdown(
    """
    <div style="text-align: center;">
        <img src="https://github.com/BacalhauNaBrisa/srt_encoding_converter/raw/main/assets/logo.png" alt="App Logo" width="200"/>
    </div>
    """,
    unsafe_allow_html=True
)

st.title("SRTool")

tabs = st.tabs(["🧪 Converter", "⏱ Shifter", "🔁 VTTtoSRT"])


# === Tab 1: Encoding Converter ===
with tabs[0]:
    st.header("Encoding Detection & Conversion")

    st.markdown("Upload a `.srt` subtitle file and this app will detect its encoding. If it's not in UTF-8, you'll be able to convert and download it.")

    uploaded_file = st.file_uploader("📤 Upload your .srt file", type=["srt"], key="converter")

    if uploaded_file:
        raw_data = uploaded_file.read()
        detection = chardet.detect(raw_data)
        detected_encoding = detection.get("encoding", "Unknown")
        confidence = detection.get("confidence", 0)

        st.write(f"**Detected Encoding:** `{detected_encoding}` (Confidence: {confidence:.2f})")

        if detected_encoding.lower() not in ("utf-8", "utf-8-sig"):
            st.warning("The file is not in UTF-8 encoding.")
            
            if st.button("🔁 Convert to UTF-8"):
                try:
                    decoded_text = raw_data.decode(detected_encoding)
                except UnicodeDecodeError:
                    st.warning(f"⚠️ Failed to decode with `{detected_encoding}`. Trying fallback ISO-8859-1...")
                    try:
                        decoded_text = raw_data.decode("iso-8859-1")
                        st.info("✅ Successfully decoded with ISO-8859-1 as fallback.")
                    except Exception as e:
                        st.error(f"❌ Fallback decoding failed too: {e}")
                        st.stop()
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


# === Tab 2: Timestamp Shifter ===
with tabs[1]:
    st.header("Subtitle Timestamp Shifter")

    st.markdown("Upload a `.srt` file, select the shift direction and enter a time delta (format: `HH:MM:SS,mmm`).")

    uploaded_shift_file = st.file_uploader("📤 Upload your .srt file", type=["srt"], key="shifter")

    col1, col2 = st.columns([1, 3])
    with col1:
        direction = st.selectbox("Shift", ["+", "-"])
    with col2:
        delta_str = st.text_input("Time to shift (HH:MM:SS,mmm)", value="00:00:01,000")

    def parse_srt_time(t):
        return datetime.strptime(t, "%H:%M:%S,%f")

    def format_srt_time(dt):
        return dt.strftime("%H:%M:%S,%f")[:-3]  # drop last 3 digits of microseconds

    def shift_srt(content, direction, delta):
        pattern = re.compile(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})")
        lines = content.splitlines()
        new_lines = []

        for line in lines:
            match = pattern.match(line)
            if match:
                start, end = match.groups()
                start_dt = parse_srt_time(start)
                end_dt = parse_srt_time(end)

                if direction == "+":
                    start_dt += delta
                    end_dt += delta
                else:
                    start_dt -= delta
                    end_dt -= delta

                start_dt = max(start_dt, datetime.strptime("00:00:00,000", "%H:%M:%S,%f"))
                end_dt = max(end_dt, datetime.strptime("00:00:00,000", "%H:%M:%S,%f"))

                new_line = f"{format_srt_time(start_dt)} --> {format_srt_time(end_dt)}"
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        return "\n".join(new_lines)

    if uploaded_shift_file and st.button("↔️ Shift Timestamps"):
        try:
            try:
                raw_text = uploaded_shift_file.read().decode("utf-8")
            except UnicodeDecodeError:
                uploaded_shift_file.seek(0)
                raw_text = uploaded_shift_file.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            st.error("❌ File is not UTF-8 or UTF-8-SIG. Please convert it first using the Converter tab.")
            st.stop()

        try:
            hours, minutes, seconds_millis = delta_str.strip().split(":")
            seconds, millis = seconds_millis.split(",")
            delta = timedelta(
                hours=int(hours),
                minutes=int(minutes),
                seconds=int(seconds),
                milliseconds=int(millis)
            )
        except Exception:
            st.error("⚠️ Invalid time format. Use `HH:MM:SS,mmm`.")
            st.stop()

        shifted_content = shift_srt(raw_text, direction, delta)

        shifted_file = io.BytesIO(shifted_content.encode("utf-8"))
        shifted_file.name = uploaded_shift_file.name.replace(".srt", f"_shifted_{direction}{delta_str.replace(':', '').replace(',', '')}.srt")

        st.success("✅ Subtitle timestamps shifted!")

        st.download_button(
            label="📥 Download Shifted .srt File",
            data=shifted_file,
            file_name=shifted_file.name,
            mime="text/plain"
        )


# === Tab 3: VTT to SRT ===
with tabs[2]:
    st.header("Convert .vtt to .srt")

    st.markdown("Upload a `.vtt` subtitle file and this tool will convert it to `.srt` format.")

    uploaded_vtt_file = st.file_uploader("📤 Upload your .vtt file", type=["vtt"])

    def convert_vtt_to_srt(vtt_text):
        lines = vtt_text.splitlines()
        srt_lines = []
        counter = 1
        buffer = []

        for line in lines:
            if re.match(r"\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}", line):
                if buffer:
                    srt_lines.extend(buffer)
                    srt_lines.append("")  # blank line between blocks
                    buffer = []

                start, end = line.split(" --> ")
                start = start.replace(".", ",")
                end = end.replace(".", ",")
                buffer.append(str(counter))
                buffer.append(f"{start} --> {end}")
                counter += 1
            elif line.strip() == "WEBVTT" or line.strip() == "":
                continue
            else:
                buffer.append(line)

        # Add final block
        if buffer:
            srt_lines.extend(buffer)
            srt_lines.append("")

        return "\n".join(srt_lines)

    if uploaded_vtt_file:
        try:
            vtt_content = uploaded_vtt_file.read().decode("utf-8")
        except UnicodeDecodeError:
            uploaded_vtt_file.seek(0)
            vtt_content = uploaded_vtt_file.read().decode("utf-8-sig")

        srt_content = convert_vtt_to_srt(vtt_content)

        srt_file = io.BytesIO(srt_content.encode("utf-8"))
        srt_file.name = uploaded_vtt_file.name.replace(".vtt", ".srt")

        st.success("✅ VTT file successfully converted to SRT!")

        st.download_button(
            label="📥 Download .srt File",
            data=srt_file,
            file_name=srt_file.name,
            mime="text/plain"
        )
