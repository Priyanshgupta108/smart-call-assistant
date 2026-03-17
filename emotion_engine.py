# ============================================================
#   SAATHI AI — Emotion Engine (HSEmotion ONNX)
# ============================================================

import cv2
import numpy as np
import collections
from config import EMOTION_MAP, emotion_actions

try:
    from hsemotion_onnx.facial_emotions import HSEmotionRecognizer
    HSEMOTION_AVAILABLE = True
except ImportError:
    HSEMOTION_AVAILABLE = False
    print("⚠️  Install hsemotion-onnx: pip install hsemotion-onnx")


class EmotionEngine:
    def __init__(self, model_name='enet_b0_8_best_vgaf',
                 history_size=5, confidence_threshold=40):

        if not HSEMOTION_AVAILABLE:
            raise ImportError("hsemotion-onnx not installed.")

        print("⏳ Loading emotion model...")
        self.recognizer = HSEmotionRecognizer(model_name=model_name)
        print("✅ Model loaded!\n")

        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        self.history    = collections.deque(maxlen=history_size)
        self.threshold  = confidence_threshold
        self.last_print = ""

        self.current_emotion    = "neutral"
        self.current_confidence = 50.0
        self.face_detected      = False   # track if real face is visible

    def process_frame(self, frame):
        """
        Detects face with strict params to avoid false positives.
        Only updates emotion if a real face is confidently found.
        Returns (emotion, confidence).
        """
        h, w  = frame.shape[:2]
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Strict detection — minNeighbors=6 eliminates false positives
        # minSize = 15% of frame width ensures we don't detect tiny objects
        min_face = int(w * 0.15)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=6,
            minSize=(min_face, min_face)
        )

        if len(faces) == 0:
            self.face_detected = False
            # Don't update emotion — keep last known value
            return self.current_emotion, self.current_confidence

        # Use largest face
        x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])

        # Extra check: face must be reasonably proportioned (not a rectangle artifact)
        aspect = fw / fh
        if not (0.7 < aspect < 1.4):
            self.face_detected = False
            return self.current_emotion, self.current_confidence

        self.face_detected = True
        cv2.rectangle(frame, (x, y), (x+fw, y+fh), (0, 200, 255), 2)

        face_crop = frame[y:y+fh, x:x+fw]
        face_rgb  = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)

        try:
            emotion_label, scores = self.recognizer.predict_emotions(
                face_rgb, logits=True)
            e_x        = np.exp(scores - np.max(scores))
            probs      = e_x / e_x.sum()
            confidence = float(probs[np.argmax(probs)]) * 100
            mapped     = EMOTION_MAP.get(emotion_label, "neutral")

            if confidence > self.threshold:
                self.history.append(mapped)

            if self.history:
                self.current_emotion    = collections.Counter(
                    self.history).most_common(1)[0][0]
                self.current_confidence = confidence

            if self.current_emotion != self.last_print:
                self.last_print = self.current_emotion
                action_now = emotion_actions.get(
                    self.current_emotion, ("?", (255,255,255)))[0]
                print(f"→ {self.current_emotion.upper()} "
                      f"| {self.current_confidence:.1f}% | {action_now}")

        except Exception as e:
            print(f"Detection error: {e}")

        return self.current_emotion, self.current_confidence
