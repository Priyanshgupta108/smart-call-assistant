# ============================================================
#   SAATHI AI — Main Entry Point
# ============================================================

import cv2
import time

from config import (
    DECISION_TIMER, CALLER, emotion_actions, emotion_messages,
    ACTION_MESSAGES,
    PHASE_DETECTING, PHASE_DECIDED, PHASE_MSG_SELECT, PHASE_MSG_SENT
)
from emotion_engine import EmotionEngine, HSEMOTION_AVAILABLE
from voice_engine   import VoiceEngine, SharedState, SR_AVAILABLE
from ui             import draw_ui, draw_message_box, draw_message_sent


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

    # ── Init engines ──
    emotion_engine = EmotionEngine()
    shared_state   = SharedState()
    voice_engine   = VoiceEngine(shared_state)
    voice_engine.start()

    # ── Camera ──
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Camera not found!")
        return
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # ── State ──
    phase            = PHASE_DETECTING
    final_action     = ""
    final_color      = (255, 255, 255)
    decision_made    = False
    decision_source  = None
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

        # ── Check voice decision ──
        with shared_state.lock:
            voice_status_txt = shared_state.voice_status
            voice_pending    = shared_state.voice_pending

            if (shared_state.voice_triggered
                and shared_state.decision_source == "voice"
                and decision_source != "voice"):
                decision_made   = True
                phase           = PHASE_DECIDED
                decision_source = "voice"
                emotion_engine.current_emotion = shared_state.final_emotion
                action_info  = emotion_actions.get(
                    shared_state.final_emotion, ("CONFIRM FIRST", (255,255,255)))
                final_action = action_info[0]
                final_color  = action_info[1]

        # ── Emotion detection ──
        if phase == PHASE_DETECTING:
            emotion_engine.process_frame(frame)

        current_emotion    = emotion_engine.current_emotion
        current_confidence = emotion_engine.current_confidence

        # ── Auto decision: timer ends ──
        # IMPORTANT: if voice is pending (processing speech), wait for it
        if time_left <= 0 and not decision_made:
            if voice_pending:
                # Give voice up to 3 extra seconds to respond
                pass
            else:
                decision_made   = True
                phase           = PHASE_DECIDED
                decision_source = "emotion"
                action_info     = emotion_actions.get(
                    current_emotion, ("CONFIRM FIRST", (255, 255, 255)))
                final_action    = action_info[0]
                final_color     = action_info[1]
                with shared_state.lock:
                    shared_state.decision_made = True
                print(f"\n⏱️  Timer ended!")
                print(f"😊 Emotion  : {current_emotion.upper()}")
                print(f"📋 Action   : {final_action}")
                print(f"💬 Message  : {emotion_messages.get(current_emotion,'')}")

        # ── Draw ──
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

            # Show "waiting for voice..." if pending after timer
            if time_left <= 0 and voice_pending and not decision_made:
                voice_status_txt = "🎤 Processing your command..."

            draw_ui(frame, CALLER, time_left,
                    current_emotion, current_confidence,
                    display_action, display_color, phase,
                    voice_status_txt, display_source)

        cv2.imshow("Saathi AI", frame)
        cv2.setWindowProperty("Saathi AI", cv2.WND_PROP_TOPMOST, 1)

        # ── Keyboard ──
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            print("\n👋 Dismissed!")
            with shared_state.lock:
                shared_state.decision_made = True
            break

        elif key == ord('m') and phase == PHASE_DECIDED:
            if final_action in ACTION_MESSAGES:
                phase            = PHASE_MSG_SELECT
                selected_msg_idx = 0
                print("\n📨 Message selection opened")

        elif phase == PHASE_MSG_SELECT:
            messages = ACTION_MESSAGES.get(final_action, [])
            if key in [ord('1'), ord('2'), ord('3'), ord('4')]:
                idx = key - ord('1')
                if idx < len(messages):
                    selected_msg_idx = idx
            elif key == 13:  # Enter
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
