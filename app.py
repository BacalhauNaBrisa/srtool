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

tabs = st.tabs(["🧪 Converter", "⏱ Shifter", "🔁 VTTtoSRT", "📜 SSAtoSRT"])


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
            if st.button("🔁 Convert to UTF-8"):
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
    st.markdown("Upload an `.srt` file, choose shift direction and delta (HH:MM:SS,mmm).")
    uploaded_shift_file = st.file_uploader("📤 Upload .srt for shifting", type=["srt"], key="shifter")

    col1, col2 = st.columns([1, 3])
    with col1:
        direction = st.selectbox("Shift", ["+", "-"])
    with col2:
        delta_str = st.text_input("Time delta (HH:MM:SS,mmm)", "00:00:01,000")

    def parse_srt_time(t):
        return datetime.strptime(t, "%H:%M:%S,%f")

    def format_srt_time(dt):
        return dt.strftime("%H:%M:%S,%f")[:-3]

    def shift_srt(content, direction, delta):
        pattern = re.compile(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})")
        new_lines = []
        for line in content.splitlines():
            m = pattern.match(line)
            if m:
                start, end = m.groups()
                sd = parse_srt_time(start)
                ed = parse_srt_time(end)
                sd = sd + delta if direction == "+" else sd - delta
                ed = ed + delta if direction == "+" else ed - delta
                sd = max(sd, datetime.strptime("00:00:00,000","%H:%M:%S,%f"))
                ed = max(ed, datetime.strptime("00:00:00,000","%H:%M:%S,%f"))
                new_lines.append(f"{format_srt_time(sd)} --> {format_srt_time(ed)}")
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
            st.error("❌ Please convert to UTF-8 first.")
            st.stop()

        try:
            h, m, s_ms = delta_str.split(":")
            s, ms = s_ms.split(",")
            delta = timedelta(hours=int(h), minutes=int(m), seconds=int(s), milliseconds=int(ms))
        except:
            st.error("⚠️ Invalid format. Use HH:MM:SS,mmm.")
            st.stop()

        shifted = shift_srt(raw_text, direction, delta)
        out = io.BytesIO(shifted.encode("utf-8"))
        out.name = uploaded_shift_file.name.replace(".srt", f"_shifted_{direction}{delta_str.replace(':','').replace(',','')}.srt")
        st.success("✅ Timestamps shifted!")
        st.download_button("📥 Download shifted .srt", data=out, file_name=out.name, mime="text/plain")

# === Tab 3: VTT to SRT ===
with tabs[2]:
    st.header("Convert VTT to SRT")
    st.markdown("Upload a `.vtt` file to convert to `.srt`.")
    uploaded_vtt_file = st.file_uploader("📤 Upload .vtt file", type=["vtt"], key="vttsrt")

    def convert_vtt_to_srt(vtt_text):
        lines = vtt_text.splitlines()
        srt_lines = []
        counter = 1
        buffer = []
        for line in lines:
            if re.match(r"\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}", line):
                if buffer:
                    srt_lines.extend(buffer)
                    srt_lines.append("")
                    buffer = []
                start, end = line.split(" --> ")
                start = start.replace('.', ',')
                end = end.replace('.', ',')
                buffer.append(str(counter))
                buffer.append(f"{start} --> {end}")
                counter += 1
            elif line.strip() in ("WEBVTT", ""): continue
            else:
                buffer.append(line)
        if buffer:
            srt_lines.extend(buffer)
            srt_lines.append("")
        return "\n".join(srt_lines)

    if uploaded_vtt_file:
        try:
            txt = uploaded_vtt_file.read().decode("utf-8")
        except UnicodeDecodeError:
            uploaded_vtt_file.seek(0)
            txt = uploaded_vtt_file.read().decode("utf-8-sig")
        srt = convert_vtt_to_srt(txt)
        out = io.BytesIO(srt.encode("utf-8"))
        out.name = uploaded_vtt_file.name.replace(".vtt", ".srt")
        st.success("✅ Converted to .srt!")
        st.download_button("📥 Download .srt", data=out, file_name=out.name, mime="text/plain")

# === Tab 4: SSA/ASS to SRT ===
with tabs[3]:
    st.header("Convert SSA/ASS to SRT")
    st.markdown("Upload a `.ssa` or `.ass` file to convert to `.srt`.")
    uploaded_ssa_file = st.file_uploader("📤 Upload .ssa/.ass file", type=["ssa", "ass"], key="ssasrt")

    def convert_ssa_to_srt(text):
        lines = text.splitlines()
        in_events = False
        format_fields = []
        idx_start = idx_end = idx_text = None
        srt_lines = []
        counter = 1
        for raw in lines:
            line = raw.strip()
            if not in_events:
                if line.lower() == "[events]":
                    in_events = True
                continue
            if line.lower().startswith("format:"):
                fmt = line.split(":",1)[1].strip()
                format_fields = [f.strip() for f in fmt.split(",")]
                lfields = [f.lower() for f in format_fields]
                idx_start = lfields.index("start")
                idx_end = lfields.index("end")
                idx_text = lfields.index("text")
                continue
            if line.lower().startswith("dialogue:"):
                content = line.split(":",1)[1].lstrip()
                parts = content.split(",", len(format_fields)-1)
                start = parts[idx_start]
                end = parts[idx_end]
                txt = parts[idx_text]
                txt = re.sub(r"\{.*?\}", "", txt)
                txt = txt.replace("\\N","\n").replace("\\n","\n")
                def a2s(t):
                    hh,mm,ss_cs = t.split(":",2)
                    ss,cs = ss_cs.split(".",1)
                    ms = int(cs.ljust(3,'0')[:3])
                    return f"{int(hh):02}:{int(mm):02}:{int(ss):02},{ms:03}"
                srt_lines.append(str(counter))
                srt_lines.append(f"{a2s(start)} --> {a2s(end)}")
                srt_lines.append(txt)
                srt_lines.append("")
                counter +=1
        return "\n".join(srt_lines)

    if uploaded_ssa_file:
        try:
            content = uploaded_ssa_file.read().decode("utf-8")
        except UnicodeDecodeError:
            uploaded_ssa_file.seek(0)
            content = uploaded_ssa_file.read().decode("utf-8-sig")
        srt_content = convert_ssa_to_srt(content)
        out = io.BytesIO(srt_content.encode("utf-8"))
        out.name = uploaded_ssa_file.name.rsplit('.',1)[0] + '.srt'
        st.success("✅ Converted SSA/ASS to .srt!")
        st.download_button("📥 Download .srt", data=out, file_name=out.name, mime="text/plain")
