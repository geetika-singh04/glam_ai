# 💄 Glam AI — Makeup Tutorial Analyzer

Upload any makeup photo and get a **20+ step pro-level replication tutorial** powered by Google Gemini Vision.

---

## ✦ Features
- Analyzes skin prep, base, eyes, lips, contour, lashes, and more
- Identifies product *types* (no brand bias)
- Mentions exact brushes, sponges, and tools for every step
- Blending techniques, layering logic, baking, cut crease, and other pro methods
- Summary overview + full sectioned breakdown
- Pro artist tips specific to each look

---

## ⚙️ Setup

### 1. Install dependencies
```bash
cd makeup_analyzer
pip install -r requirements.txt
```

### 2. Get your FREE Gemini API key
1. Go to → https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click **"Create API Key"** — it's free to start!

### 3. Set your Gemini API key

**macOS / Linux:**
```bash
export GEMINI_API_KEY="AIza..."
```

**Windows (Command Prompt):**
```cmd
set GEMINI_API_KEY=AIza...
```

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="AIza..."
```

### 4. Run the app
```bash
streamlit run app.py
```

Opens at **http://localhost:8501** 🎉

---

## 🖼️ Supported Image Formats
- JPG / JPEG
- PNG
- WebP

---

## 💡 Tips for Best Results
- Use clear, well-lit makeup photos
- Full-face shots work best (eyes, lips, and skin all visible)
- Editorial/magazine quality images give the richest tutorials
- The more visible the makeup detail, the more precise the steps

---

## 💰 Cost
Gemini 1.5 Flash has a **generous free tier** (15 requests/minute, 1M requests/day on free plan).
For personal local use, it is essentially **free**.
