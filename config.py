# ============================================================
#   SAATHI AI — Configuration
# ============================================================

DECISION_TIMER = 12

CALLER = {
    "name":   "Rahul",
    "number": "+91 98765 43210",
    "tier":   "Tier 2 - Friend"
}

EMOTION_MAP = {
    "Happiness": "happy",
    "Anger":     "angry",
    "Sadness":   "sad",
    "Neutral":   "neutral",
    "Surprise":  "surprise",
    "Fear":      "fear",
    "Disgust":   "disgust",
    "Contempt":  "disgust",
}

emotion_actions = {
    "happy":    ("ACCEPT CALL",   (0, 255, 0)),
    "sad":      ("SEND MESSAGE",  (255, 100, 0)),
    "angry":    ("REJECT CALL",   (0, 0, 255)),
    "neutral":  ("CONFIRM FIRST", (255, 255, 0)),
    "surprise": ("CHECK CALLER",  (0, 255, 255)),
    "fear":     ("SEND MESSAGE",  (128, 0, 128)),
    "disgust":  ("REJECT CALL",   (0, 0, 255)),
}

emotion_messages = {
    "happy":    "You look happy! Accepting call...",
    "sad":      "You seem sad. Sending: I'll call you later",
    "angry":    "You seem angry. Rejecting call...",
    "neutral":  "Neutral mood. Asking confirmation...",
    "surprise": "You look surprised! Checking caller...",
    "fear":     "You seem busy. Sending message...",
    "disgust":  "Rejecting call...",
}

VOICE_COMMANDS = {
    "accept":    "happy",
    "haan":      "happy",
    "yes":       "happy",
    "ok":        "happy",
    "okay":      "happy",
    "reject":    "angry",
    "nahi":      "angry",
    "no":        "angry",
    "cut":       "angry",
    "busy":      "angry",
    "message":   "sad",
    "msg":       "sad",
    "later":     "sad",
    "baad mein": "sad",
    "who":       "surprise",
    "kaun":      "surprise",
    "check":     "surprise",
}

ACTION_MESSAGES = {
    "SEND MESSAGE": [
        "I'll call you back soon 📞",
        "In a meeting, text me 🤝",
        "Can't talk right now 😔",
        "Will call back in 10 mins ⏱️",
    ],
    "REJECT CALL": [
        "Please don't call me 🚫",
        "Not the right time, bye 👋",
        "I'm busy, don't disturb 😤",
        "Wrong number, stop calling ❌",
    ],
}

# App phases
PHASE_DETECTING  = "detecting"
PHASE_DECIDED    = "decided"
PHASE_MSG_SELECT = "msg_select"
PHASE_MSG_SENT   = "msg_sent"
