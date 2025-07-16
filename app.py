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
        if enc.lower() not in ("utf-8","utf-8-sig"):
            st.warning("File is not UTF-8.")
            if st.button("🔁 Convert to UTF-8"):
                try:
                    dec = raw.decode(enc)
                except:
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
    st.markdown("Upload an `.srt`, calculate or enter a delta, then apply shift.")
    up = st.file_uploader("📤 Upload .srt to shift", type=["srt"], key="shifter")
    col1, col2 = st.columns(2)
    with col1:
        tA = st.text_input("Time A (HH:MM:SS,mmm)", key="tA")
    with col2:
        tB = st.text_input("Time B (HH:MM:SS,mmm)", key="tB")
    if tA and tB:
        try:
            dA = datetime.strptime(tA, "%H:%M:%S,%f")
            dB = datetime.strptime(tB, "%H:%M:%S,%f")
            dlt = dB - dA
            sign = "+" if dlt>=timedelta(0) else "-"
            ad = abs(dlt)
            h,m,s = divmod(ad.seconds,3600)[0], ad.seconds%3600//60, ad.seconds%60
            ms = ad.microseconds//1000
            calc = f"{h:02}:{m:02}:{s:02},{ms:03}"
            st.session_state.dir = sign
            st.session_state.delta = calc
            st.info(f"Calculated: {sign} {calc}")
        except:
            st.warning("Invalid time format.")
    # shift inputs
    col3, col4 = st.columns([1,3])
    with col3:
        dir = st.selectbox("Shift", ["+","-"], key="dir")
    with col4:
        default = st.session_state.get("delta","00:00:01,000")
        dstr = st.text_input("Time delta (HH:MM:SS,mmm)", default, key="delta")
    def parseT(tx): return datetime.strptime(tx, "%H:%M:%S,%f")
    def fmtT(dt): return dt.strftime("%H:%M:%S,%f")[:-3]
    def doShift(txt, dir, dlt):
        pat = re.compile(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})")
        out=[]
        for ln in txt.splitlines():
            m=pat.match(ln)
            if m:
                s,e=m.groups()
                sd,ed = parseT(s),parseT(e)
                sd = sd + dlt if dir=="+" else sd - dlt
                ed = ed + dlt if dir=="+" else ed - dlt
                zero = parseT("00:00:00,000")
                sd,ed = max(sd,zero),max(ed,zero)
                out.append(f"{fmtT(sd)} --> {fmtT(ed)}")
            else:
                out.append(ln)
        return "\n".join(out)
    if up and st.button("↔️ Shift", key="btnShift"):
        content = up.read().decode("utf-8-sig")
        try:
            hh,mm,ssmi = dstr.split(":"); ss,ms = ssmi.split(",")
            dlt = timedelta(hours=int(hh),minutes=int(mm),seconds=int(ss),milliseconds=int(ms))
        except:
            st.error("Invalid delta format.")
            st.stop()
        res = doShift(content,st.session_state.dir,dlt)
        out=io.BytesIO(res.encode("utf-8")); out.name=up.name.replace(".srt","_shifted.srt")
        st.success("Shift applied")
        st.download_button("📥 Download",data=out,file_name=out.name)

# === Tab 3: VTT to SRT ===
with tabs[2]:
    st.header("Convert VTT to SRT")
    upv = st.file_uploader("📤 Upload .vtt", type=["vtt"], key="vtt")
    def v2s(txt):
        lines=txt.splitlines(); out=[]; cnt=1; buf=[]
        for l in lines:
            if re.match(r"\d{2}:\d{2}:\d{2}\.\d{3} -->",l):
                if buf: out+=buf+['']; buf=[]
                s,e=l.split(" --> ")
                buf=[str(cnt),f"{s.replace('.',',')} --> {e.replace('.',',')}"]; cnt+=1
            elif l.strip() not in ("WEBVTT","",): buf.append(l)
        if buf: out+=buf+['']
        return "\n".join(out)
    if upv:
        txt=upv.read().decode("utf-8-sig")
        res=v2s(txt)
        out=io.BytesIO(res.encode("utf-8")); out.name=upv.name.replace(".vtt",".srt")
        st.success("Converted")
        st.download_button("📥 Download .srt",data=out,file_name=out.name)

# === Tab 4: SSA/ASS to SRT ===
with tabs[3]:
    st.header("Convert SSA/ASS to SRT")
    ups = st.file_uploader("📤 Upload .ssa/.ass", type=["ssa","ass"], key="ssa")
    def s2s(txt):
        lines=txt.splitlines(); in_e=False;fmt=[];idx=[];out=[];cnt=1
        for raw in lines:
            l=raw.strip()
            if not in_e:
                if l.lower()=="[events]": in_e=True; continue
            if l.lower().startswith("format:"):
                fmt=[f.strip() for f in l.split(':',1)[1].split(',')]
                lf=[f.lower() for f in fmt]
                idx=[lf.index(i) for i in ("start","end","text")]; continue
            if l.lower().startswith("dialogue:"):
                parts=raw.split(',',len(fmt)-1)[1:]
                s,e,t=parts[idx[0]],parts[idx[1]],parts[idx[2]]
                t=re.sub(r"\{.*?\}","",t).replace("\\N","\n")
                def a2s(tm):
                    hh,mm,cs=tm.split(':'); sec,cs=cs.split('.')
                    ms=int(cs.ljust(3,'0')[:3]); return f"{int(hh):02}:{int(mm):02}:{int(sec):02},{ms:03}"
                out+=[str(cnt),f"{a2s(s)} --> {a2s(e)}",t,'']; cnt+=1
        return "\n".join(out)
    if ups:
        txt=ups.read().decode("utf-8-sig")
        res=s2s(txt)
        out=io.BytesIO(res.encode("utf-8")); out.name=ups.name.rsplit('.',1)[0]+'.srt'
        st.success("Converted")
        st.download_button("📥 Download .srt",data=out,file_name=out.name)

# === Tab 5: Splitter ===
with tabs[4]:
    st.header("Split SRT File")
    upsrt=st.file_uploader("📤 Upload .srt to split", type=["srt"], key="split")
    idx=st.number_input("Split after block #",min_value=1,step=1,key="si")
    if upsrt and st.button("✂️ Split"):  
        txt=upsrt.read().decode("utf-8-sig")
        blks=[b.strip() for b in txt.split("\n\n") if b.strip()]
        p1, p2 = blks[:idx], blks[idx:]
        def mk(b):
            lines=[]
            for i,blk in enumerate(b,1):
                ps=blk.splitlines()
                times,cont=ps[1],ps[2:]
                lines.append(str(i)); lines.append(times); lines+=cont; lines.append('')
            return "\n".join(lines)
        s1,s2 = mk(p1), mk(p2)
        f1, f2 = io.BytesIO(s1.encode("utf-8")), io.BytesIO(s2.encode("utf-8"))
        f1.name, f2.name = upsrt.name.replace('.srt','_1.srt'), upsrt.name.replace('.srt','_2.srt')
        st.success("Split done")
        st.download_button("Part 1",data=f1,file_name=f1.name)
        st.download_button("Part 2",data=f2,file_name=f2.name)
