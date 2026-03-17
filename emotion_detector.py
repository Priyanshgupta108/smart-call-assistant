import cv2
import numpy as np
import collections
import time
import threading

# ============================================================
#   SAATHI AI — Smart Call Assistant
#   Emotion Engine : HSEmotion ONNX
#   Voice Engine   : SpeechRecognition
#   Message Box    : For SEND MESSAGE + REJECT CALL
# ============================================================

try:
    from hsemotion_onnx.facial_emotions import HSEmotionRecognizer
    HSEMOTION_AVAILABLE = True
except ImportError:
    HSEMOTION_AVAILABLE = False
    print("⚠️  Install hsemotion-onnx: pip install hsemotion-onnx")

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    print("⚠️  Install SpeechRecognition: pip install SpeechRecognition")

DECISION_TIMER = 12

# ── Preset messages per action ──
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

# ── Voice command mappings (Hindi + English) ──
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

CALLER = {
    "name":   "Rahul",
    "number": "+91 98765 43210",
    "tier":   "Tier 2 - Friend"
}

# ── App phases ──
PHASE_DETECTING  = "detecting"
PHASE_DECIDED    = "decided"
PHASE_MSG_SELECT = "msg_select"   # message selection box
PHASE_MSG_SENT   = "msg_sent"     # message confirmed

# ── Shared state ──
class SharedState:
    def __init__(self):
        self.lock            = threading.Lock()
        self.decision_made   = False
        self.decision_source = None
        self.final_emotion   = "neutral"
        self.voice_status    = "🎤 Listening..."
        self.voice_triggered = False

state = SharedState()


# ============================================================
#   VOICE THREAD
# ============================================================
def voice_listener():
    if not SR_AVAILABLE:
        return

    recognizer_sr = sr.Recognizer()
    recognizer_sr.energy_threshold         = 300
    recognizer_sr.dynamic_energy_threshold = True
    recognizer_sr.pause_threshold          = 0.6

    mic = sr.Microphone()
    with mic as source:
        recognizer_sr.adjust_for_ambient_noise(source, duration=0.3)

    while True:
        with state.lock:
            if state.decision_made:
                break
        try:
            with mic as source:
                audio = recognizer_sr.listen(
                    source, timeout=1, phrase_time_limit=2)

            text = recognizer_sr.recognize_google(audio).lower().strip()
            print(f"🎤 Heard: '{text}'")

            matched_emotion = None
            for keyword, emotion in VOICE_COMMANDS.items():
                if keyword in text:
                    matched_emotion = emotion
                    break

            if matched_emotion:
                with state.lock:
                    if not state.decision_made:
                        state.decision_made   = True
                        state.decision_source = "voice"
                        state.final_emotion   = matched_emotion
                        state.voice_triggered = True
                        action = emotion_actions.get(
                            matched_emotion, ("?", (255,255,255)))[0]
                        print(f"\n🎤 Voice command: '{text}'  →  {action}")
                        print(f"💬 {emotion_messages.get(matched_emotion,'')}")
                break
            else:
                with state.lock:
                    state.voice_status = f"🎤 Heard: '{text}' (no match)"

        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            pass
        except sr.RequestError:
            with state.lock:
                state.voice_status = "🎤 Mic error"
            break
        except Exception:
            pass


# ============================================================
#   DRAW: Message Selection Box
# ============================================================
def draw_message_box(frame, action, messages, selected_idx):
    h, w = frame.shape[:2]

    # Dim the background
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    # Box
    box_x, box_y = 40, 140
    box_w, box_h = w - 80, h - 200
    cv2.rectangle(frame, (box_x, box_y),
                  (box_x + box_w, box_y + box_h), (30, 30, 30), -1)
    cv2.rectangle(frame, (box_x, box_y),
                  (box_x + box_w, box_y + box_h), (80, 80, 80), 2)

    # Title
    title_color = (0, 0, 255) if action == "REJECT CALL" else (255, 100, 0)
    cv2.putText(frame, f"SELECT MESSAGE TO SEND",
                (box_x + 20, box_y + 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, title_color, 2)
    cv2.putText(frame, f"Action: {action}",
                (box_x + 20, box_y + 58),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1)

    # Divider
    cv2.line(frame,
             (box_x + 15, box_y + 68),
             (box_x + box_w - 15, box_y + 68),
             (60, 60, 60), 1)

    # Message options
    for i, msg in enumerate(messages):
        y_pos       = box_y + 100 + i * 52
        is_selected = (i == selected_idx)

        # Highlight selected
        if is_selected:
            cv2.rectangle(frame,
                          (box_x + 15, y_pos - 22),
                          (box_x + box_w - 15, y_pos + 18),
                          (50, 50, 50), -1)
            cv2.rectangle(frame,
                          (box_x + 15, y_pos - 22),
                          (box_x + box_w - 15, y_pos + 18),
                          title_color, 2)

        num_color = title_color if is_selected else (100, 100, 100)
        msg_color = (255, 255, 255) if is_selected else (180, 180, 180)

        cv2.putText(frame, f"[{i+1}]",
                    (box_x + 25, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, num_color, 2)
        cv2.putText(frame, msg,
                    (box_x + 70, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, msg_color, 1)

    # Footer
    footer_y = box_y + box_h - 20
    cv2.putText(frame, "Press 1-4 to select   |   ENTER to confirm   |   B to go back",
                (box_x + 20, footer_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 100), 1)


# ============================================================
#   DRAW: Message Sent Screen
# ============================================================
def draw_message_sent(frame, action, sent_message, decision_source):
    h, w = frame.shape[:2]

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    # Source badge
    badge_color = (100, 255, 200) if decision_source == "voice" else (100, 200, 255)
    badge_text  = "[ VOICE COMMAND ]" if decision_source == "voice" else "[ EMOTION DETECTED ]"
    cv2.putText(frame, badge_text,
                (40, h // 2 - 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, badge_color, 1)

    # Action
    action_color = (0, 0, 255) if action == "REJECT CALL" else (255, 100, 0)
    cv2.putText(frame, action,
                (40, h // 2 - 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1.3, action_color, 3)

    # Sent label
    cv2.putText(frame, "MESSAGE SENT ✓",
                (40, h // 2 - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 100), 2)

    # The message
    cv2.putText(frame, f"\"{sent_message}\"",
                (40, h // 2 + 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1)

    cv2.putText(frame, "Press Q to dismiss",
                (40, h // 2 + 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 100, 100), 1)


# ============================================================
#   DRAW: Main UI
# ============================================================
def draw_ui(frame, caller, time_left,
            emotion, confidence,
            action, color, phase,
            voice_status, decision_source):

    h, w = frame.shape[:2]

    # Top bar
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 135), (15, 15, 15), -1)
    cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

    cv2.putText(frame, "INCOMING CALL",
                (20, 28), cv2.FONT_HERSHEY_SIMPLEX,
                0.65, (100, 255, 100), 2)
    cv2.putText(frame, caller["name"],
                (20, 72), cv2.FONT_HERSHEY_SIMPLEX,
                1.5, (255, 255, 255), 3)
    cv2.putText(frame, caller["number"],
                (20, 100), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (180, 180, 180), 1)
    cv2.putText(frame, caller["tier"],
                (20, 122), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (100, 200, 255), 1)

    # Timer bar
    timer_width = int((time_left / DECISION_TIMER) * w)
    if time_left > 6:   tc = (0, 255, 0)
    elif time_left > 3: tc = (0, 165, 255)
    else:               tc = (0, 0, 255)

    cv2.rectangle(frame, (0, 135), (w, 152), (40, 40, 40), -1)
    cv2.rectangle(frame, (0, 135), (timer_width, 152), tc, -1)
    cv2.putText(frame, f"{time_left:.1f}s",
                (w - 58, 149), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (255, 255, 255), 1)

    # Voice status bar
    cv2.rectangle(frame, (0, 152), (w, 172), (30, 30, 30), -1)
    cv2.putText(frame, voice_status,
                (10, 167), cv2.FONT_HERSHEY_SIMPLEX,
                0.42, (100, 255, 200), 1)

    # Bottom panel
    if phase == PHASE_DETECTING:
        cv2.rectangle(frame, (0, h - 130), (w, h), (20, 20, 20), -1)
        cv2.putText(frame, "SAATHI READING YOUR MOOD...",
                    (20, h - 105), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (150, 150, 150), 1)
        cv2.putText(frame, emotion.upper(),
                    (20, h - 60), cv2.FONT_HERSHEY_SIMPLEX,
                    1.6, color, 3)

        bar = int((confidence / 100) * (w - 40))
        cv2.rectangle(frame, (20, h - 40), (w - 20, h - 24), (60, 60, 60), -1)
        cv2.rectangle(frame, (20, h - 40), (20 + bar, h - 24), color, -1)
        cv2.putText(frame, f"{confidence:.1f}% confident",
                    (20, h - 8), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (200, 200, 200), 1)

    elif phase == PHASE_DECIDED:
        cv2.rectangle(frame, (0, h - 155), (w, h), (20, 20, 20), -1)

        badge_color = (100, 255, 200) if decision_source == "voice" else (100, 200, 255)
        badge_text  = "[ VOICE COMMAND ]" if decision_source == "voice" else "[ EMOTION DETECTED ]"

        cv2.putText(frame, badge_text,
                    (20, h - 130), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, badge_color, 1)
        cv2.putText(frame, "SAATHI DECIDED:",
                    (20, h - 108), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (150, 150, 150), 1)
        cv2.putText(frame, action,
                    (20, h - 65), cv2.FONT_HERSHEY_SIMPLEX,
                    1.2, color, 3)
        cv2.putText(frame, emotion_messages.get(emotion, ""),
                    (20, h - 35), cv2.FONT_HERSHEY_SIMPLEX,
                    0.48, (200, 200, 200), 1)

        # Prompt for message box
        if action in ACTION_MESSAGES:
            cv2.putText(frame, "Press M to select message  |  Q to dismiss",
                        (20, h - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.42, (100, 255, 200), 1)
        else:
            cv2.putText(frame, "Press Q to dismiss",
                        (20, h - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.45, (100, 100, 100), 1)


# ============================================================
#   MAIN
# ============================================================
def run_saathi():
    if not HSEMOTION_AVAILABLE:
        print("❌ hsemotion-onnx not installed.")
        return

    print("=" * 52)
    print("   SAATHI AI - Smart Call Assistant")
    print(f"   Decision Timer  : {DECISION_TIMER} seconds")
    print("   Emotion Engine   : HSEmotion ONNX")
    print(f"   Voice Engine     : {'SpeechRecognition ✅' if SR_AVAILABLE else 'Not available ❌'}")
    print("   Press Q to dismiss anytime")
    print("=" * 52)
    print(f"\n📞 Incoming call from {CALLER['name']}...\n")

    print("⏳ Loading emotion model...")
    recognizer = HSEmotionRecognizer(model_name='enet_b0_8_best_vgaf')
    print("✅ Model loaded!\n")

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Camera not found!")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Start voice thread
    if SR_AVAILABLE:
        vthread = threading.Thread(target=voice_listener, daemon=True)
        vthread.start()
        print("🎤 Voice listener started!")
        print("   Say: accept / reject / message / who")
        print("   Hindi: haan / nahi / baad mein / kaun\n")

    emotion_history    = collections.deque(maxlen=5)
    current_emotion    = "neutral"
    current_confidence = 50.0
    last_printed       = ""

    phase           = PHASE_DETECTING
    final_action    = ""
    final_color     = (255, 255, 255)
    decision_made   = False
    decision_source = None

    # Message box state
    selected_msg_idx = 0
    sent_message     = ""

    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame     = cv2.flip(frame, 1)
        elapsed   = time.time() - start_time
        time_left = max(0, DECISION_TIMER - elapsed)

        # ── Check voice thread decision ──
        with state.lock:
            voice_status_txt = state.voice_status
            if state.decision_made and not decision_made and state.decision_source == "voice":
                decision_made   = True
                phase           = PHASE_DECIDED
                decision_source = "voice"
                current_emotion = state.final_emotion
                action_info     = emotion_actions.get(current_emotion, ("CONFIRM FIRST", (255,255,255)))
                final_action    = action_info[0]
                final_color     = action_info[1]

        # ── Emotion Detection ──
        if phase == PHASE_DETECTING:
            gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=3, minSize=(50, 50)
            )

            if len(faces) > 0:
                x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
                cv2.rectangle(frame, (x, y), (x+fw, y+fh), (0, 200, 255), 2)

                face_crop = frame[y:y+fh, x:x+fw]
                face_rgb  = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)

                try:
                    emotion_label, scores = recognizer.predict_emotions(
                        face_rgb, logits=True)
                    e_x        = np.exp(scores - np.max(scores))
                    probs      = e_x / e_x.sum()
                    confidence = float(probs[np.argmax(probs)]) * 100
                    mapped     = EMOTION_MAP.get(emotion_label, "neutral")

                    if confidence > 40:
                        emotion_history.append(mapped)

                    if emotion_history:
                        current_emotion    = collections.Counter(
                            emotion_history).most_common(1)[0][0]
                        current_confidence = confidence

                    if current_emotion != last_printed:
                        last_printed = current_emotion
                        action_now   = emotion_actions.get(
                            current_emotion, ("?", (255,255,255)))[0]
                        print(f"→ {current_emotion.upper()} "
                              f"| {current_confidence:.1f}% | {action_now}")

                except Exception as e:
                    print(f"Detection error: {e}")

        # ── Auto Decision: timer ends ──
        if time_left <= 0 and not decision_made:
            decision_made   = True
            phase           = PHASE_DECIDED
            decision_source = "emotion"
            action_info     = emotion_actions.get(
                current_emotion, ("CONFIRM FIRST", (255, 255, 255)))
            final_action    = action_info[0]
            final_color     = action_info[1]
            with state.lock:
                state.decision_made = True
            print(f"\n⏱️  Timer ended!")
            print(f"😊 Emotion  : {current_emotion.upper()}")
            print(f"📋 Action   : {final_action}")

        # ── Draw based on phase ──
        if phase == PHASE_MSG_SELECT:
            messages = ACTION_MESSAGES.get(final_action, [])
            draw_ui(frame, CALLER, time_left,
                    current_emotion, current_confidence,
                    final_action, final_color, PHASE_DECIDED,
                    voice_status_txt, decision_source)
            draw_message_box(frame, final_action, messages, selected_msg_idx)

        elif phase == PHASE_MSG_SENT:
            draw_message_sent(frame, final_action, sent_message, decision_source)

        else:
            action_info    = emotion_actions.get(
                current_emotion, ("CONFIRM FIRST", (255, 255, 255)))
            display_action = final_action if decision_made else action_info[0]
            display_color  = final_color  if decision_made else action_info[1]
            display_source = decision_source if decision_made else None

            draw_ui(frame, CALLER, time_left,
                    current_emotion, current_confidence,
                    display_action, display_color, phase,
                    voice_status_txt, display_source)

        cv2.imshow("Saathi AI", frame)
        cv2.setWindowProperty("Saathi AI", cv2.WND_PROP_TOPMOST, 1)

        # ── Keyboard handling ──
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            print("\n👋 Dismissed by user!")
            with state.lock:
                state.decision_made = True
            break

        # Open message box
        elif key == ord('m') and phase == PHASE_DECIDED:
            if final_action in ACTION_MESSAGES:
                phase = PHASE_MSG_SELECT
                selected_msg_idx = 0
                print("\n📨 Message selection opened")

        # Navigate message box
        elif phase == PHASE_MSG_SELECT:
            messages = ACTION_MESSAGES.get(final_action, [])

            if key in [ord('1'), ord('2'), ord('3'), ord('4')]:
                idx = key - ord('1')
                if idx < len(messages):
                    selected_msg_idx = idx

            elif key == 13:  # Enter key
                sent_message = messages[selected_msg_idx]
                phase        = PHASE_MSG_SENT
                print(f"\n✉️  Message sent: \"{sent_message}\"")

            elif key == ord('b'):
                phase = PHASE_DECIDED
                print("↩️  Back to decision screen")

    cap.release()
    cv2.destroyAllWindows()
    print("\n✅ Saathi closed.")


if __name__ == "__main__":
    run_saathi()
