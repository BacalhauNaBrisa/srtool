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

# Define tabs including the new Splitter
tabs = st.tabs([
    "🧪 Converter",
    "⏱ Shifter",
    "🔁 VTTtoSRT",
    "📜 SSAtoSRT",
    "✂️ Splitter"
])

# === Tab 1: Encoding Converter ===
with tabs[0]:
    st.header("Encoding Detection & Conversion")
    st.markdown("Upload a `.srt` subtitle file and detect/convert its encoding to UTF-8.")
    uploaded_file = st.file_uploader("📤 Upload your .srt file", type=["srt"], key="converter")

    if uploaded_file:
        raw_data = uploaded_file.read()
        detection = chardet.detect(raw_data)
        detected_encoding = detection.get("encoding", "Unknown")
        confidence = detection.get("confidence", 0)
        st.write(f"**Detected Encoding:** `{detected_encoding}` (Confidence: {confidence:.2f})")

        if detected_encoding.lower() not in ("utf-8", "utf-8-sig"):
            st.warning("The file is not in UTF-8 encoding.")
            if st.button("🔁 Convert to UTF-8", key="convbtn"):
                try:
                    decoded_text = raw_data.decode(detected_encoding)
                except UnicodeDecodeError:
                    st.warning(f"⚠️ Failed to decode with `{detected_encoding}`. Trying ISO-8859-1 fallback...")
                    try:
                        decoded_text = raw_data.decode("iso-8859-1")
                        st.info("✅ Decoded with ISO-8859-1 fallback.")
                    except Exception as e:
                        st.error(f"❌ Fallback decoding failed: {e}")
                        st.stop()
                utf8_bytes = decoded_text.encode("utf-8")
                utf8_file = io.BytesIO(utf8_bytes)
                utf8_file.name = uploaded_file.name.replace(".srt", "_utf8.srt")
                st.success("File converted to UTF-8!")
                st.download_button(
                    label="📥 Download UTF-8 .srt",
                    data=utf8_file,
                    file_name=utf8_file.name,
                    mime="text/plain"
                )
        else:
            st.success("✅ Already in UTF-8 encoding.")

# === Tab 2: Timestamp Shifter ===
with tabs[1]:
    st.header("Subtitle Timestamp Shifter")
    st.markdown("Upload an `.srt` file, optionally calculate shift, then choose shift direction and delta (HH:MM:SS,mmm)." )
    uploaded_shift_file = st.file_uploader("📤 Upload .srt for shifting", type=["srt"], key="shifter")

    # Time calculator inputs
    col_a, col_b = st.columns(2)
    with col_a:
        time_a = st.text_input("Time A (Original, HH:MM:SS,mmm)", key="timeA")
    with col_b:
        time_b = st.text_input("Time B (New, HH:MM:SS,mmm)", key="timeB")

    calculated = False
    if time_a and time_b:
        try:
            dt_a = datetime.strptime(time_a, "%H:%M:%S,%f")
            dt_b = datetime.strptime(time_b, "%H:%M:%S,%f")
            delta_calc = dt_b - dt_a
            sign = "+" if delta_calc >= timedelta(0) else "-"
            delta_abs = abs(delta_calc)
            hours, remainder = divmod(delta_abs.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            millis = delta_abs.microseconds // 1000
            calc_str = f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"
            # Auto-fill direction and delta fields
            st.session_state.dir = sign
            st.session_state.delta = calc_str
            st.info(f"Calculated shift: {sign} {calc_str}")
            calculated = True
        except ValueError:
            st.warning("⚠️ Invalid time format in calculator. Use HH:MM:SS,mmm.")

    # Existing shift inputs
    col1, col2 = st.columns([1, 3])
    with col1:
        direction = st.selectbox("Shift", ["+", "-"], key="dir")
    with col2:
        default_delta = st.session_state.get("delta", "00:00:01,000")
        delta_str = st.text_input("Time delta (HH:MM:SS,mmm)", default_delta, key="delta")

    def parse_srt_time(t): return datetime.strptime(t, "%H:%M:%S,%f")
    def format_srt_time(dt): return dt.strftime("%H:%M:%S,%f")[:-3]

    def shift_srt(content, direction, delta):
        pattern = re.compile(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})")
        out = []
        for line in content.splitlines():
            m = pattern.match(line)
            if m:
                s,e = m.groups()
                sd,ed = parse_srt_time(s), parse_srt_time(e)
                sd = sd + delta if direction == "+" else sd - delta
                ed = ed + delta if direction == "+" else ed - delta
                zero = datetime.strptime("00:00:00,000","%H:%M:%S,%f")
                sd,ed = max(sd,zero), max(ed,zero)
                out.append(f"{format_srt_time(sd)} --> {format_srt_time(ed)}")
            else:
                out.append(line)
        return "\n".join(out)

    if uploaded_shift_file and st.button("↔️ Shift Timestamps", key="shftbtn"):
        try:
            txt = uploaded_shift_file.read().decode("utf-8")
        except UnicodeDecodeError:
            uploaded_shift_file.seek(0)
            txt = uploaded_shift_file.read().decode("utf-8-sig")
        try:
            h,m,sm = delta_str.split(":")
            s,ms = sm.split(",")
            delta = timedelta(hours=int(h), minutes=int(m), seconds=int(s), milliseconds=int(ms))
        except:
            st.error("⚠️ Invalid format. Use HH:MM:SS,mmm.")
            st.stop()
        res = shift_srt(txt, direction, delta)
        out = io.BytesIO(res.encode("utf-8"))
        out.name = uploaded_shift_file.name.replace(
            ".srt",
            f"_shifted_{direction}{delta_str.replace(':','').replace(',','')}.srt"
        )
        st.success("✅ Timestamps shifted!")
        st.download_button("📥 Download shifted .srt",data=out,file_name=out.name,mime="text/plain")

# === Tab 3: VTT to SRT ===
with tabs[2]:
    st.header("Convert VTT to SRT")
    st.markdown("Upload a `.vtt` file to convert to `.srt`.")
    uploaded_vtt = st.file_uploader("📤 Upload .vtt file", type=["vtt"], key="vttsrt")

    def vtt2srt(txt):
        lines = txt.splitlines(); out=[]; cnt=1; buf=[]
        for l in lines:
            if re.match(r"\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}", l):
                if buf: out += buf + ['']; buf=[]
                s,e = l.split(" --> "); buf=[str(cnt),f"{s.replace('.',',')} --> {e.replace('.',',')}"
