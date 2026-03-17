# 🤙 Smart Call Assistant

An AI-powered call assistant that detects your **real-time emotion** via webcam and **voice commands** to automatically decide whether to accept, reject, or send a message — without touching your phone.

---

## 🎯 Core Concept

When a call comes in, you're often in a situation where you can't or don't want to answer. Smart Call Assistant reads your face and listens to your voice to make that decision for you — intelligently.

---

## ✨ Features

- 😊 **Real-time Emotion Detection** — detects happy, angry, sad, fear, surprise, disgust, neutral using HSEmotion ONNX (fast, accurate, fully offline)
- 🎤 **Voice Commands** — say "accept", "reject", "message", "who" (Hindi supported: haan, nahi, baad mein, kaun)
- ⚡ **Voice Always Wins** — voice command overrides emotion detection at any point
- 💬 **Message Box** — select a preset message to send when rejecting or unavailable
- ⏱️ **Decision Timer** — auto-decides based on emotion if no command given in time
- 🏷️ **Source Badge** — shows whether decision was made by voice or emotion

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Emotion Detection | HSEmotion ONNX (`enet_b0_8_best_vgaf`) |
| Face Detection | OpenCV Haar Cascade |
| Voice Recognition | SpeechRecognition + Google SR |
| Camera Feed | OpenCV |
| Threading | Python `threading` |

---

## 📁 Project Structure

```
smart-call-assistant/
├── main.py              # Entry point
├── emotion_engine.py    # HSEmotion detection logic
├── voice_engine.py      # Mic listening thread
├── ui.py                # OpenCV draw functions
├── config.py            # All constants and mappings
└── requirements.txt
```

---

## ⚙️ Setup

**1. Clone the repo**
```bash
git clone https://github.com/Priyanshgupta108/smart-call-assistant.git
cd smart-call-assistant
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Download emotion model** (one time only)

Download `enet_b0_8_best_vgaf.onnx` from:
```
https://github.com/HSE-asavchenko/face-emotion-recognition/raw/main/models/affectnet_emotions/onnx/enet_b0_8_best_vgaf.onnx
```

Place it in:
```
C:\Users\<YourName>\.hsemotion\enet_b0_8_best_vgaf.onnx
```

**4. Run**
```bash
python main.py
```

---

## 🎮 Controls

| Key | Action |
|---|---|
| `M` | Open message selection box |
| `1` `2` `3` `4` | Select message |
| `Enter` | Confirm and send message |
| `B` | Go back |
| `Q` | Dismiss |

**Voice commands:**

| Say | Action |
|---|---|
| accept / haan / yes | ✅ Accept Call |
| reject / nahi / no / cut | ❌ Reject Call |
| message / later / baad mein | 💬 Send Message |
| who / kaun / check | 🔍 Check Caller |

---

## 🚀 Upcoming

- [ ] Phase 2 — AI Suggestion Engine
- [ ] Phase 3 — Streamlit Dashboard
- [ ] Phase 4 — Twilio Call Integration

---

## 👨‍💻 Author

**Priyansh Gupta** — [GitHub](https://github.com/Priyanshgupta108)

> BTech CSE (Data Science) | CMRCET | 2027
