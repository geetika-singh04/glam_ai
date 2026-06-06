import streamlit as st
from groq import Groq
import base64
from PIL import Image
import io
import re
import os
from collections import OrderedDict

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Glam AI · Makeup Tutorial Analyzer",
    page_icon="💄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --rose:       #D4756B;
    --blush:      #F2C4BB;
    --nude:       #E8D5C4;
    --warm-black: #1A1210;
    --cream:      #FAF6F2;
    --gold:       #C9A96E;
    --muted:      #8A7068;
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: var(--warm-black) !important;
    font-family: 'DM Sans', sans-serif;
    color: var(--cream);
}

#MainMenu, footer, header, [data-testid="stToolbar"] { visibility: hidden; display:none; }

.hero {
    text-align: center;
    padding: 2.5rem 0 2rem;
    border-bottom: 1px solid rgba(201,169,110,0.2);
    margin-bottom: 2rem;
}
.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 3rem; font-weight: 700;
    background: linear-gradient(135deg, var(--nude), var(--gold), var(--rose));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin: 0; line-height: 1.1;
}
.hero-sub {
    font-size: 0.9rem; color: var(--muted); font-weight: 300;
    margin-top: 0.5rem; letter-spacing: 0.08em; text-transform: uppercase;
}

.apikey-box {
    background: rgba(201,169,110,0.08);
    border: 1px solid rgba(201,169,110,0.3);
    border-radius: 14px; padding: 1.2rem 1.5rem; margin-bottom: 1.5rem;
}

[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1.5px dashed rgba(201,169,110,0.4) !important;
    border-radius: 16px !important; padding: 1.5rem !important;
}
[data-testid="stFileUploader"]:hover { border-color: var(--gold) !important; }

.img-frame { border-radius: 16px; overflow: hidden;
    border: 1px solid rgba(201,169,110,0.25);
    box-shadow: 0 20px 60px rgba(0,0,0,0.5); }

.stButton > button {
    background: linear-gradient(135deg, var(--rose), var(--gold)) !important;
    color: white !important; border: none !important;
    border-radius: 50px !important; padding: 0.75rem 3rem !important;
    font-family: 'DM Sans', sans-serif !important; font-weight: 500 !important;
    font-size: 1rem !important; letter-spacing: 0.05em !important;
    text-transform: uppercase !important; width: 100% !important;
    box-shadow: 0 4px 20px rgba(212,117,107,0.4) !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; }

.summary-card {
    background: linear-gradient(135deg, rgba(212,117,107,0.12), rgba(201,169,110,0.08));
    border: 1px solid rgba(201,169,110,0.3);
    border-radius: 20px; padding: 2rem 2.5rem; margin-bottom: 2rem;
}
.summary-card h2 { font-family: 'Playfair Display', serif;
    font-size: 1.4rem; color: var(--gold); margin-top: 0; }
.summary-card p { color: var(--nude); line-height: 1.8; font-size: 0.97rem; }

.section-label {
    font-family: 'Playfair Display', serif; font-size: 1.3rem; color: var(--blush);
    border-left: 3px solid var(--rose); padding-left: 1rem; margin: 2rem 0 1rem;
}
.step-card {
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px; padding: 1.2rem 1.5rem; margin-bottom: 0.75rem;
    display: flex; gap: 1.2rem; align-items: flex-start;
}
.step-card:hover { background: rgba(201,169,110,0.06); }
.step-num {
    background: linear-gradient(135deg, var(--rose), var(--gold));
    color: white; border-radius: 50%; min-width: 32px; height: 32px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.8rem; font-weight: 700; flex-shrink: 0; margin-top: 2px;
}
.step-text { color: var(--cream); line-height: 1.7; font-size: 0.95rem; }
.step-text strong { color: var(--gold); font-weight: 500; }
.tool-tag {
    display: inline-block; background: rgba(212,117,107,0.15);
    border: 1px solid rgba(212,117,107,0.3); color: var(--blush);
    border-radius: 50px; padding: 0.2rem 0.75rem; font-size: 0.78rem; margin: 0.2rem;
}
[data-testid="stImage"] img { border-radius: 14px; }
</style>
""", unsafe_allow_html=True)


# ── Prompt ─────────────────────────────────────────────────────────────────────
FULL_PROMPT = """You are a world-class professional makeup artist with 20+ years of experience on editorial shoots, runways, and celebrity red carpets.

Analyze this makeup image in extreme detail and produce a full pro-level tutorial.
Identify product *types* only (not brands). Mention exact tools, blending techniques, layering logic, and call out special effects (cut crease, strobing, baking, etc.) by name.

Return your response in this EXACT structure:

<LOOK_NAME>A creative name for this makeup look</LOOK_NAME>

<SUMMARY>
3-4 sentences: overall look, mood/vibe, color palette, finish (matte/dewy/glossy), key defining features.
</SUMMARY>

<TOOLS_NEEDED>
Comma-separated list of all brushes, sponges, and tools needed.
</TOOLS_NEEDED>

<SECTIONS>
Use only relevant sections from: SKIN PREP, BASE & COMPLEXION, CONCEALER & BAKING, BROWS, EYE PRIMER & BASE, EYESHADOW, EYELINER, LASHES, CHEEKS & BLUSH, CONTOUR & HIGHLIGHT, LIPS, SETTING & FINISHING

Format each step as:
<STEP num="N" section="SECTION_NAME">Detailed step here. Include product type, tool, technique, and pro tip.</STEP>

Number steps sequentially (1, 2, 3...) across ALL sections. Aim for 20-30 steps total. Each step: 1-3 sentences.
</SECTIONS>

<PRO_TIPS>
3-5 advanced pro tips specific to this look.
</PRO_TIPS>"""


# ── API call ───────────────────────────────────────────────────────────────────
def call_groq(image_bytes: bytes, media_type: str, api_key: str) -> str:
    client = Groq(api_key=api_key)
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{b64}"},
                    },
                    {"type": "text", "text": FULL_PROMPT},
                ],
            }
        ],
        max_tokens=4096,
        temperature=0.7,
    )
    return response.choices[0].message.content


# ── Parsers ────────────────────────────────────────────────────────────────────
def extract_tag(text: str, tag: str) -> str:
    m = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return m.group(1).strip() if m else ""

def extract_steps(text: str) -> list[dict]:
    matches = re.findall(r'<STEP\s+num="(\d+)"\s+section="([^"]+)">(.*?)</STEP>', text, re.DOTALL)
    return [{"num": int(n), "section": s.strip(), "content": c.strip()} for n, s, c in matches]

def render_step_card(num: int, content: str):
    st.markdown(f"""
    <div class="step-card">
        <div class="step-num">{num}</div>
        <div class="step-text">{content}</div>
    </div>""", unsafe_allow_html=True)


# ── UI ─────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1 class="hero-title">Glam AI</h1>
    <p class="hero-sub">Upload a makeup photo · Get a pro-level replication tutorial</p>
</div>
""", unsafe_allow_html=True)

col_upload, col_result = st.columns([1, 1.6], gap="large")

with col_upload:
    st.markdown('<div class="apikey-box">', unsafe_allow_html=True)
    preset_key = ""
    try:
        preset_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        preset_key = os.environ.get("GROQ_API_KEY", "")

    if preset_key:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:0.5rem;padding:0.5rem 0;
            color:#4caf50;font-size:0.85rem;">
            ✅ API key loaded automatically
        </div>""", unsafe_allow_html=True)
        api_key_input = preset_key
    else:
        api_key_input = st.text_input(
            "🔑 Groq API Key",
            type="password",
            placeholder="Paste your gsk_... key here",
            help="Get a free key at: https://console.groq.com/keys",
        )
        st.markdown(
            '<a href="https://console.groq.com/keys" target="_blank" '
            'style="font-size:0.78rem; color:var(--gold); text-decoration:none;">' 
            '↗ Get a free key at console.groq.com</a>',
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("#### Upload Makeup Image")
    uploaded = st.file_uploader(
        "Drop your image here",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )

    if uploaded:
        img = Image.open(uploaded)
        st.markdown('<div class="img-frame">', unsafe_allow_html=True)
        st.image(img, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_btn = st.button("✦ Analyze & Generate Tutorial", use_container_width=True)
    else:
        st.markdown("""
        <div style="text-align:center; padding:3rem 1rem; color:var(--muted); font-size:0.9rem;">
            <div style="font-size:3rem; margin-bottom:1rem;">💄</div>
            Upload any makeup photo — editorial, selfie, celebrity look —<br>
            and get a 20+ step pro tutorial to replicate it.
        </div>""", unsafe_allow_html=True)
        analyze_btn = False

with col_result:
    if uploaded and analyze_btn:
        if not api_key_input or not api_key_input.strip():
            st.error("⚠️ Please paste your Groq API key in the box on the left first.")
            st.stop()

        with st.spinner("Analyzing your look… usually takes 5–10 seconds ✨"):
            uploaded.seek(0)
            file_bytes = uploaded.read()
            ext = uploaded.name.split(".")[-1].lower()
            media_map = {"jpg":"image/jpeg","jpeg":"image/jpeg","png":"image/png","webp":"image/webp"}
            media_type = media_map.get(ext, "image/jpeg")
            try:
                raw_response = call_groq(file_bytes, media_type, api_key_input.strip())
                st.session_state["result"] = raw_response
            except Exception as e:
                err = str(e)
                if "invalid_api_key" in err.lower() or "authentication" in err.lower() or "401" in err:
                    st.error("❌ Invalid Groq API key. Get yours free at https://console.groq.com/keys")
                elif "rate_limit" in err.lower() or "429" in err:
                    st.error("⏳ Rate limit hit. Wait a few seconds and try again.")
                else:
                    st.error(f"Something went wrong: {err}")
                st.stop()

    if "result" in st.session_state:
        raw = st.session_state["result"]
        look_name = extract_tag(raw, "LOOK_NAME")
        summary   = extract_tag(raw, "SUMMARY")
        tools_raw = extract_tag(raw, "TOOLS_NEEDED")
        steps     = extract_steps(raw)
        pro_tips  = extract_tag(raw, "PRO_TIPS")

        icons = {
            "SKIN PREP":"🧴","BASE & COMPLEXION":"🫧","CONCEALER & BAKING":"✨",
            "BROWS":"〰️","EYE PRIMER & BASE":"👁️","EYESHADOW":"🎨",
            "EYELINER":"✏️","LASHES":"🦋","CHEEKS & BLUSH":"🌸",
            "CONTOUR & HIGHLIGHT":"💫","LIPS":"💋","SETTING & FINISHING":"🔒",
        }

        # ── Build plain-text version for clipboard ──────────────────────────
        sections: dict[str, list] = OrderedDict()
        for s in steps:
            sections.setdefault(s["section"], []).append(s)

        clipboard_lines = []
        if look_name:
            clipboard_lines.append(f"💄 {look_name}")
            clipboard_lines.append("=" * 50)
        if summary:
            clipboard_lines.append("\n✦ LOOK OVERVIEW")
            clipboard_lines.append(summary)
        if tools_raw:
            clipboard_lines.append("\n🪄 TOOLS NEEDED")
            clipboard_lines.append(tools_raw)
        if sections:
            clipboard_lines.append("\n📋 FULL TUTORIAL STEPS")
            for sec_name, sec_steps in sections.items():
                icon = icons.get(sec_name, "•")
                clipboard_lines.append(f"\n{icon} {sec_name}")
                clipboard_lines.append("-" * 30)
                for s in sec_steps:
                    clipboard_lines.append(f"Step {s['num']}: {s['content']}")
        if pro_tips:
            clipboard_lines.append("\n⭐ PRO ARTIST TIPS")
            tips = [t.strip() for t in re.split(r'\n+|\d+\.', pro_tips) if t.strip()]
            for i, tip in enumerate(tips, 1):
                clipboard_lines.append(f"Tip {i}: {tip}")

        clipboard_text = "\n".join(clipboard_lines)
        # escape backticks and backslashes for JS template literal
        clipboard_js = clipboard_text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")

        # ── Look name ───────────────────────────────────────────────────────
        if look_name:
            st.markdown(f"""
            <h2 style="font-family:'Playfair Display',serif;font-size:2rem;
                background:linear-gradient(135deg,var(--nude),var(--gold));
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                background-clip:text;margin-bottom:0.25rem;">{look_name}</h2>
            """, unsafe_allow_html=True)

        # ── Quick-glance cheat sheet ─────────────────────────────────────────
        if sections:
            cheat_items = "".join(
                f'<div class="cheat-item">'
                f'<span class="cheat-icon">{icons.get(sec_name,"•")}</span>'
                f'<span class="cheat-sec">{sec_name}</span>'
                f'<span class="cheat-count">{len(sec_steps)} step{"s" if len(sec_steps)!=1 else ""}</span>'
                f'</div>'
                for sec_name, sec_steps in sections.items()
            )
            st.markdown(f"""
            <style>
            .cheat-sheet {{
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(201,169,110,0.25);
                border-radius: 16px; padding: 1.2rem 1.5rem;
                margin-bottom: 1.5rem; display: flex; flex-wrap: wrap; gap: 0.5rem;
            }}
            .cheat-sheet-title {{
                width:100%; font-size:0.72rem; font-weight:600; text-transform:uppercase;
                letter-spacing:0.1em; color:var(--gold); margin-bottom:0.4rem;
            }}
            .cheat-item {{
                display:flex; align-items:center; gap:0.4rem;
                background:rgba(201,169,110,0.08); border:1px solid rgba(201,169,110,0.2);
                border-radius:50px; padding:0.3rem 0.8rem; font-size:0.8rem;
            }}
            .cheat-icon {{ font-size:0.85rem; }}
            .cheat-sec {{ color:var(--nude); }}
            .cheat-count {{ color:var(--muted); font-size:0.72rem; }}
            </style>
            <div class="cheat-sheet">
                <div class="cheat-sheet-title">✦ At a Glance — {len(steps)} total steps across {len(sections)} sections</div>
                {cheat_items}
            </div>""", unsafe_allow_html=True)

        # ── Summary card ─────────────────────────────────────────────────────
        if summary:
            st.markdown(f"""
            <div class="summary-card">
                <h2>✦ Look Overview</h2>
                <p>{summary}</p>
            </div>""", unsafe_allow_html=True)

        # ── Tools ────────────────────────────────────────────────────────────
        if tools_raw:
            tools = [t.strip() for t in tools_raw.split(",") if t.strip()]
            st.markdown("<div class='section-label'>🪄 Tools You'll Need</div>", unsafe_allow_html=True)
            tags_html = "".join(f'<span class="tool-tag">{t}</span>' for t in tools)
            st.markdown(f'<div style="margin-bottom:1rem;">{tags_html}</div>', unsafe_allow_html=True)

        # ── Copy All Steps button ────────────────────────────────────────────
        st.markdown(f"""
        <style>
        .copy-btn {{
            display: inline-flex; align-items: center; gap: 0.5rem;
            background: linear-gradient(135deg, var(--rose), var(--gold));
            color: white; border: none; border-radius: 50px;
            padding: 0.65rem 2rem; font-size: 0.9rem; font-weight: 500;
            letter-spacing: 0.05em; cursor: pointer; margin-bottom: 1.5rem;
            box-shadow: 0 4px 15px rgba(212,117,107,0.35);
            transition: all 0.2s ease; width: 100%; justify-content: center;
        }}
        .copy-btn:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(212,117,107,0.5); }}
        .copy-btn.copied {{ background: linear-gradient(135deg, #4caf50, #81c784); }}
        </style>
        <button class="copy-btn" id="copyAllBtn" onclick="
            navigator.clipboard.writeText(`{clipboard_js}`).then(() => {{
                this.innerHTML = '✅ Copied to clipboard!';
                this.classList.add('copied');
                setTimeout(() => {{
                    this.innerHTML = '📋 Copy All Steps';
                    this.classList.remove('copied');
                }}, 2500);
            }});
        ">📋 Copy All Steps</button>
        """, unsafe_allow_html=True)

        # ── Step-by-step tutorial ────────────────────────────────────────────
        if steps:
            st.markdown("<div class='section-label'>📋 Full Step-by-Step Tutorial</div>", unsafe_allow_html=True)
            for sec_name, sec_steps in sections.items():
                icon = icons.get(sec_name, "•")
                st.markdown(f"""
                <div style="font-size:0.75rem;font-weight:600;text-transform:uppercase;
                    letter-spacing:0.12em;color:var(--rose);margin:1.5rem 0 0.6rem;
                    padding-bottom:0.4rem;border-bottom:1px solid rgba(212,117,107,0.2);">
                    {icon} {sec_name}</div>""", unsafe_allow_html=True)
                for s in sec_steps:
                    render_step_card(s["num"], s["content"])

        # ── Pro tips ─────────────────────────────────────────────────────────
        if pro_tips:
            st.markdown("<div class='section-label'>⭐ Pro Artist Tips</div>", unsafe_allow_html=True)
            tips = [t.strip() for t in re.split(r'\n+|\d+\.', pro_tips) if t.strip()]
            for i, tip in enumerate(tips, 1):
                st.markdown(f"""
                <div style="background:rgba(201,169,110,0.07);border-left:3px solid var(--gold);
                    border-radius:0 12px 12px 0;padding:0.9rem 1.2rem;margin-bottom:0.6rem;
                    color:var(--cream);font-size:0.93rem;line-height:1.7;">
                    <strong style="color:var(--gold);">Tip {i}:</strong> {tip}</div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("↺ Analyze Another Image", use_container_width=True):
            del st.session_state["result"]
            st.rerun()

    elif not uploaded:
        st.markdown("""
        <div style="height:400px;display:flex;align-items:center;justify-content:center;
            color:var(--muted);font-size:0.9rem;text-align:center;line-height:2;
            border:1px dashed rgba(255,255,255,0.06);border-radius:20px;">
            Your pro-level tutorial<br>will appear here after analysis
        </div>""", unsafe_allow_html=True)
