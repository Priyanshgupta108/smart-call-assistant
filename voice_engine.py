# ============================================================
#   SAATHI AI — Voice Engine (SpeechRecognition)
# ============================================================

import threading
from config import VOICE_COMMANDS, emotion_actions, emotion_messages

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    print("⚠️  Install SpeechRecognition: pip install SpeechRecognition")


class SharedState:
    """Thread-safe shared state between voice and main thread."""
    def __init__(self):
        self.lock            = threading.Lock()
        self.decision_made   = False
        self.decision_source = None       # "emotion" or "voice"
        self.final_emotion   = "neutral"
        self.voice_status    = "🎤 Listening..."
        self.voice_triggered = False
        self.voice_pending   = False      # True while Google SR is processing


class VoiceEngine:
    def __init__(self, shared_state: SharedState):
        self.state  = shared_state
        self.thread = None

    def start(self):
        if not SR_AVAILABLE:
            print("⚠️  SpeechRecognition not available — voice disabled.")
            return
        self.thread = threading.Thread(
            target=self._listen_loop, daemon=True)
        self.thread.start()
        print("🎤 Voice listener started!")
        print("   Say: accept / reject / message / who")
        print("   Hindi: haan / nahi / baad mein / kaun\n")

    def _listen_loop(self):
        recognizer_sr = sr.Recognizer()
        recognizer_sr.energy_threshold         = 300
        recognizer_sr.dynamic_energy_threshold = True
        recognizer_sr.pause_threshold          = 0.5

        mic = sr.Microphone()

        # Calibrate once at start
        print("🎤 Calibrating mic...")
        with mic as source:
            recognizer_sr.adjust_for_ambient_noise(source, duration=0.5)
        print("🎤 Mic ready!\n")

        while True:
            with self.state.lock:
                if self.state.decision_made:
                    break

            try:
                # Step 1: capture audio
                with mic as source:
                    audio = recognizer_sr.listen(
                        source, timeout=1, phrase_time_limit=2)

                # Step 2: mark as pending BEFORE sending to Google
                # This prevents emotion from auto-deciding while we wait
                with self.state.lock:
                    self.state.voice_pending = True
                    self.state.voice_status  = "🎤 Processing..."

                # Step 3: send to Google SR
                text = recognizer_sr.recognize_google(audio).lower().strip()
                print(f"🎤 Heard: '{text}'")

                # Step 4: match command
                matched_emotion = None
                for keyword, emotion in VOICE_COMMANDS.items():
                    if keyword in text:
                        matched_emotion = emotion
                        break

                if matched_emotion:
                    with self.state.lock:
                        if True:  # voice always overrides
                            self.state.decision_made   = True
                            self.state.decision_source = "voice"
                            self.state.final_emotion   = matched_emotion
                            self.state.voice_triggered = True
                            self.state.voice_pending   = False
                            action = emotion_actions.get(
                                matched_emotion, ("?", (255,255,255)))[0]
                            print(f"\n🎤 Voice command: '{text}'  →  {action}")
                            print(f"💬 {emotion_messages.get(matched_emotion,'')}")
                    break
                else:
                    # No match — clear pending, keep listening
                    with self.state.lock:
                        self.state.voice_pending = False
                        self.state.voice_status  = f"🎤 '{text}' — try: accept/reject"

            except sr.WaitTimeoutError:
                with self.state.lock:
                    self.state.voice_pending = False
            except sr.UnknownValueError:
                with self.state.lock:
                    self.state.voice_pending = False
                    self.state.voice_status  = "🎤 Listening..."
            except sr.RequestError:
                with self.state.lock:
                    self.state.voice_pending = False
                    self.state.voice_status  = "🎤 Mic error"
                break
            except Exception:
                with self.state.lock:
                    self.state.voice_pending = False
