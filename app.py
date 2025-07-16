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
    st.markdown("Upload an `.srt` file, choose shift direction and delta (HH:MM:SS,mmm).")
    uploaded_shift_file = st.file_uploader("📤 Upload .srt for shifting", type=["srt"], key="shifter")

    col1, col2 = st.columns([1, 3])
    with col1:
        direction = st.selectbox("Shift", ["+", "-"], key="dir")
    with col2:
        delta_str = st.text_input("Time delta (HH:MM:SS,mmm)", "00:00:01,000", key="delta")

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
                if direction == "+": sd,ed = sd+delta, ed+delta
                else: sd,ed = sd-delta, ed-delta
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
            h,m,sm = delta_str.split(":"); s,ms=sm.split(",")
            delta=timedelta(hours=int(h),minutes=int(m),seconds=int(s),milliseconds=int(ms))
        except:
            st.error("⚠️ Invalid format. Use HH:MM:SS,mmm.")
            st.stop()
        res = shift_srt(txt,direction,delta)
        out=io.BytesIO(res.encode("utf-8"))
        out.name=uploaded_shift_file.name.replace(".srt",f"_shifted_{direction}{delta_str.replace(':','').replace(',','')}.srt")
        st.success("✅ Timestamps shifted!")
        st.download_button("📥 Download shifted .srt",data=out,file_name=out.name,mime="text/plain")

# === Tab 3: VTT to SRT ===
with tabs[2]:
    st.header("Convert VTT to SRT")
    st.markdown("Upload a `.vtt` file to convert to `.srt`.")
    uploaded_vtt=st.file_uploader("📤 Upload .vtt file",type=["vtt"],key="vttsrt")
    def vtt2srt(txt):
        lines=txt.splitlines();out=[];cnt=1;buf=[]
        for l in lines:
            if re.match(r"\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}",l):
                if buf: out+=buf+[''];buf=[]
                s,e=l.split(" --> ");out_buf=[str(cnt),f"{s.replace('.',',')} --> {e.replace('.',',')}"];cnt+=1;buf=out_buf
            elif l.strip() not in ("WEBVTT","\n","",): buf.append(l)
        if buf: out+=buf+['']
        return "\n".join(out)
    if uploaded_vtt:
        try:txt=uploaded_vtt.read().decode("utf-8")
        except:uploaded_vtt.seek(0);txt=uploaded_vtt.read().decode("utf-8-sig")
        res=vtt2srt(txt)
        out=io.BytesIO(res.encode("utf-8"));out.name=uploaded_vtt.name.replace(".vtt",".srt")
        st.success("✅ Converted to .srt!");st.download_button("📥 Download .srt",out,out.name,"text/plain")

# === Tab 4: SSA/ASS to SRT ===
with tabs[3]:
    st.header("Convert SSA/ASS to SRT")
    st.markdown("Upload a `.ssa` or `.ass` file to convert to `.srt`.")
    uploaded_ssa=st.file_uploader("📤 Upload .ssa/.ass file",type=["ssa","ass"],key="ssasrt")
    def ssa2srt(txt):
        lines=txt.splitlines();
        in_e=False;fmt=[];idx_s=idx_e=idx_t=None;out=[];cnt=1
        for raw in lines:
            l=raw.strip()
            if not in_e:
                if l.lower()=="[events]":in_e=True;continue
            if l.lower().startswith("format:"):
                fmt=[f.strip() for f in l.split(':',1)[1].split(',')]
                lf=[f.lower() for f in fmt]
                idx_s,idx_e,idx_t=lf.index("start"),lf.index("end"),lf.index("text");continue
            if l.lower().startswith("dialogue:"):
                parts=raw.split(',',len(fmt)-1)[1:]
                s,e,txt=parts[idx_s],parts[idx_e],parts[idx_t]
                txt=re.sub(r"\{.*?\}","",txt).replace("\\N","\n")
                def a2s(t):hh,mm,ss_cs=t.split(':');ss,cs=ss_cs.split('.');ms=int(cs.ljust(3,'0')[:3]);return f"{int(hh):02}:{int(mm):02}:{int(ss):02},{ms:03}"
                out+=[str(cnt),f"{a2s(s)} --> {a2s(e)}",txt,''];cnt+=1
        return "\n".join(out)
    if uploaded_ssa:
        try:txt=uploaded_ssa.read().decode("utf-8")
        except:uploaded_ssa.seek(0);txt=uploaded_ssa.read().decode("utf-8-sig")
        res=ssa2srt(txt)
        out=io.BytesIO(res.encode("utf-8"));out.name=uploaded_ssa.name.rsplit('.',1)[0]+'.srt'
        st.success("✅ Converted SSA/ASS to .srt!");st.download_button("📥 Download .srt",out,out.name,"text/plain")

# === Tab 5: Splitter ===
with tabs[4]:
    st.header("Split SRT File")
    st.markdown("Upload a `.srt` file and specify a split index. Generates two reindexed .srt files.")
    uploaded_split=st.file_uploader("📤 Upload .srt to split",type=["srt"],key="splitter")
    split_index=st.number_input("Split after block number",min_value=1,step=1,key="splitidx")
    if uploaded_split and st.button("✂️ Split File",key="splitbtn"):
        text=uploaded_split.read().decode("utf-8-sig")
        blocks=[b.strip() for b in text.split("\n\n") if b.strip()]
        part1=blocks[:split_index]
        part2=blocks[split_index:]
        def build_srt(blocks):
            lines=[]
            for i,b in enumerate(blocks,1):
                parts=b.splitlines()
                times,content=parts[1],parts[2:]
                lines.append(str(i));lines.append(times);lines.extend(content);lines.append("")
            return "\n".join(lines)
        s1=build_srt(part1);s2=build_srt(part2)
        f1=io.BytesIO(s1.encode("utf-8"));f1.name=uploaded_split.name.replace(".srt","_part1.srt")
        f2=io.BytesIO(s2.encode("utf-8"));f2.name=uploaded_split.name.replace(".srt","_part2.srt")
        st.success("✅ Split complete!")
        st.download_button("📥 Download Part 1",data=f1,file_name=f1.name,mime="text/plain")
        st.download_button("📥 Download Part 2",data=f2,file_name=f2.name,mime="text/plain")
