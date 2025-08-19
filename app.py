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

# Tabs definition
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
    uploaded_file = st.file_uploader("📤 Upload .srt file", type=["srt"], key="converter")

    if uploaded_file:
        raw = uploaded_file.read()
        det = chardet.detect(raw)
        enc = det.get("encoding", "Unknown")
        conf = det.get("confidence", 0)
        st.write(f"**Detected Encoding:** `{enc}` (Confidence: {conf:.2f})")
        if enc and enc.lower() not in ("utf-8","utf-8-sig"):
            st.warning("File is not UTF-8.")
            if st.button("🔁 Convert to UTF-8"):
                try:
                    dec = raw.decode(enc)
                except Exception:
                    st.warning(f"Decoding {enc} failed, using ISO-8859-1 fallback.")
                    dec = raw.decode("iso-8859-1", errors="replace")
                b = dec.encode("utf-8")
                out = io.BytesIO(b)
                out.name = uploaded_file.name.replace(".srt","_utf8.srt")
                st.success("Converted to UTF-8")
                st.download_button("📥 Download UTF-8 .srt", data=out, file_name=out.name)
        else:
            st.success("Already UTF-8")

# === Tab 2: Timestamp Shifter ===
with tabs[1]:
    st.header("Subtitle Timestamp Shifter")
    st.markdown("Upload an `.srt` file, calculate or enter a delta, then apply shift.")
    uploaded_shift = st.file_uploader("📤 Upload .srt to shift", type=["srt"], key="shifter")

    calc_col1, calc_col2 = st.columns(2)
    with calc_col1:
        time_a = st.text_input("Time A (HH:MM:SS,mmm)", key="timeA")
    with calc_col2:
        time_b = st.text_input("Time B (HH:MM:SS,mmm)", key="timeB")

    if time_a and time_b:
        try:
            dt_a = datetime.strptime(time_a, "%H:%M:%S,%f")
            dt_b = datetime.strptime(time_b, "%H:%M:%S,%f")
            dlt_calc = dt_b - dt_a
            sign = "+" if dlt_calc >= timedelta(0) else "-"
            dlt_abs = abs(dlt_calc)
            hrs, rem = divmod(dlt_abs.seconds, 3600)
            mins, secs = divmod(rem, 60)
            millis = dlt_abs.microseconds // 1000
            calc_str = f"{hrs:02}:{mins:02}:{secs:02},{millis:03}"
            st.session_state.dir = sign
            st.session_state.delta = calc_str
            st.info(f"Calculated shift: {sign} {calc_str}")
        except ValueError:
            st.warning("Invalid time format in calculator. Use HH:MM:SS,mmm.")

    shift_col1, shift_col2 = st.columns([1, 3])
    with shift_col1:
        direction = st.selectbox("Shift", ["+", "-"], key="dir")
    with shift_col2:
        default_delta = st.session_state.get("delta", "00:00:01,000")
        delta_str = st.text_input("Time delta (HH:MM:SS,mmm)", default_delta, key="delta")

    def parse_srt_time(t): return datetime.strptime(t, "%H:%M:%S,%f")
    def format_srt_time(dt): return dt.strftime("%H:%M:%S,%f")[:-3]

    def shift_srt(content, direction, delta):
        pattern = re.compile(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})")
        new_lines = []
        for line in content.splitlines():
            m = pattern.match(line)
            if m:
                start, end = m.groups()
                sd, ed = parse_srt_time(start), parse_srt_time(end)
                sd = sd + delta if direction == "+" else sd - delta
                ed = ed + delta if direction == "+" else ed - delta
                zero = parse_srt_time("00:00:00,000")
                sd, ed = max(sd, zero), max(ed, zero)
                new_lines.append(f"{format_srt_time(sd)} --> {format_srt_time(ed)}")
            else:
                new_lines.append(line)
        return "\n".join(new_lines)

    if uploaded_shift and st.button("↔️ Shift Timestamps", key="shftbtn"):
        try:
            text = uploaded_shift.read().decode("utf-8-sig")
        except Exception:
            st.error("Error reading file. Ensure it's UTF-8 or UTF-8-SIG.")
            st.stop()
        try:
            h, m, s_ms = delta_str.split(":")
            s, ms = s_ms.split(",")
            delta = timedelta(hours=int(h), minutes=int(m), seconds=int(s), milliseconds=int(ms))
        except Exception:
            st.error("Invalid delta format. Use HH:MM:SS,mmm.")
            st.stop()
        shifted = shift_srt(text, direction, delta)
        out = io.BytesIO(shifted.encode("utf-8"))
        out.name = uploaded_shift.name.replace(".srt", f"_shifted_{direction}{delta_str.replace(':','').replace(',','')}.srt")
        st.success("Timestamps shifted!")
        st.download_button("📥 Download shifted .srt", data=out, file_name=out.name, mime="text/plain")

# === Tab 3: VTT to SRT ===
with tabs[2]:
    st.header("Convert VTT to SRT")
    st.markdown("Upload a `.vtt` file to convert to `.srt`.")
    uploaded_vtt = st.file_uploader("📤 Upload .vtt file", type=["vtt"], key="vttsrt")

    def convert_vtt_to_srt(vtt_text):
        lines = vtt_text.splitlines()
        srt_lines = []
        counter = 1
        buffer = []
        for line in lines:
            if re.match(r"\d{2}:\d{2}:\d{2}\.\d{3} --> ", line):
                if buffer:
                    srt_lines.extend(buffer)
                    srt_lines.append("")
                    buffer = []
                start, end = line.split(" --> ")
                start = start.replace(".", ",")
                end = end.replace(".", ",")
                buffer.append(str(counter))
                buffer.append(f"{start} --> {end}")
                counter += 1
            elif line.strip() in ("WEBVTT", ""):
                continue
            else:
                buffer.append(line)
        if buffer:
            srt_lines.extend(buffer)
            srt_lines.append("")
        return "\n".join(srt_lines)

    if uploaded_vtt:
        try:
            content = uploaded_vtt.read().decode("utf-8-sig")
        except Exception:
            st.error("Error reading .vtt file.")
            st.stop()
        srt_content = convert_vtt_to_srt(content)
        srt_file = io.BytesIO(srt_content.encode("utf-8"))
        srt_file.name = uploaded_vtt.name.replace(".vtt", ".srt")
        st.success("Converted to .srt")
        st.download_button("📥 Download .srt", data=srt_file, file_name=srt_file.name, mime="text/plain")

# === Tab 4: SSA/ASS to SRT ===
with tabs[3]:
    st.header("Convert SSA/ASS to SRT")
    st.markdown("Upload a `.ssa` or `.ass` file and convert it to `.srt`.")
    uploaded_ssa_file = st.file_uploader("📤 Upload .ssa/.ass file", type=["ssa", "ass"], key="ssasrt")

    def convert_ssa_to_srt(txt):
        lines = txt.splitlines()
        in_events = False
        format_fields = []
        idx_start = idx_end = idx_text = None
        srt_lines = []
        counter = 1
        for raw in lines:
            l = raw.strip()
            if not in_events:
                if l.lower() == "[events]":
                    in_events = True
                continue
            if l.lower().startswith("format:"):
                fmt = l.split(":", 1)[1].strip()
                format_fields = [f.strip() for f in fmt.split(",")]
                lfields = [f.lower() for f in format_fields]
                try:
                    idx_start = lfields.index("start")
                    idx_end = lfields.index("end")
                    idx_text = lfields.index("text")
                except ValueError:
                    st.error("Could not locate Start/End/Text in format fields.")
                    return ""
                continue
            if l.lower().startswith("dialogue:"):
                content = raw.split(":", 1)[1].lstrip()
                parts = content.split(",", len(format_fields) - 1)
                start = parts[idx_start]
                end = parts[idx_end]
                text = parts[idx_text]
                text = re.sub(r"\{.*?\}", "", text)
                text = text.replace("\\N", "\n").replace("\\n", "\n")
                def ssa_time_to_srt(t):
                    hh, mm, ss_cs = t.split(":", 2)
                    ss, cs = ss_cs.split(".", 1)
                    ms = int(cs.ljust(3, "0")[:3])
                    return f"{int(hh):02}:{int(mm):02}:{int(ss):02},{ms:03}"
                srt_lines.append(str(counter))
                srt_lines.append(f"{ssa_time_to_srt(start)} --> {ssa_time_to_srt(end)}")
                srt_lines.extend(text.split("\n"))
                srt_lines.append("")
                counter += 1
        return "\n".join(srt_lines)

    if uploaded_ssa_file:
        try:
            content = uploaded_ssa_file.read().decode("utf-8")
        except UnicodeDecodeError:
            uploaded_ssa_file.seek(0)
            content = uploaded_ssa_file.read().decode("utf-8-sig")
        srt_content = convert_ssa_to_srt(content)
        if srt_content:
            srt_file = io.BytesIO(srt_content.encode("utf-8"))
            srt_file.name = uploaded_ssa_file.name.rsplit(".", 1)[0] + ".srt"
            st.success("Converted SSA/ASS to .srt!")
            st.download_button("📥 Download .srt", data=srt_file, file_name=srt_file.name, mime="text/plain")

# === Tab 5: Splitter ===
with tabs[4]:
    st.header("Split SRT File")
    st.markdown("Upload a `.srt` file and specify a split index. Generates two reindexed .srt files.")
    uploaded_split_file = st.file_uploader("📤 Upload .srt to split", type=["srt"], key="splitter")
    split_index = st.number_input("Split after block number", min_value=1, step=1, key="splitidx")

    if uploaded_split_file and st.button("✂️ Split File", key="splitbtn"):
        text = uploaded_split_file.read().decode("utf-8-sig")
        blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
        part1 = blocks[:split_index]
        part2 = blocks[split_index:]
        def build_srt(blocks):
            lines = []
            for i, b in enumerate(blocks, 1):
                ps = b.splitlines()
                times = ps[1]
                content = ps[2:]
                lines.append(str(i))
                lines.append(times)
                lines.extend(content)
                lines.append("")
            return "\n".join(lines)
        s1 = build_srt(part1)
        s2 = build_srt(part2)
        f1 = io.BytesIO(s1.encode("utf-8"))
        f1.name = uploaded_split_file.name.replace(".srt", "_part1.srt")
        f2 = io.BytesIO(s2.encode("utf-8"))
        f2.name = uploaded_split_file.name.replace(".srt", "_part2.srt")
        st.success("Split complete!")
        st.download_button("📥 Download Part 1", data=f1, file_name=f1.name, mime="text/plain")
        st.download_button("📥 Download Part 2", data=f2, file_name=f2.name, mime="text/plain")

# === Ko-Fi Donation Panel (replaces Buy Me A Coffee) ===
st.markdown(
    """
    <div style="display:flex;justify-content:center;margin-top:3em;">
      <div style="max-width:700px;width:100%;">
        <iframe id="kofiframe"
                src="https://ko-fi.com/bacalhaunabrisa/?hidefeed=true&widget=true&embed=true&preview=true"
                style="border:none;width:100%;padding:4px;background:transparent;"
                height="712"
                title="bacalhaunabrisa">
        </iframe>
      </div>
    </div>
    """,
    unsafe_allow_html=True
)
