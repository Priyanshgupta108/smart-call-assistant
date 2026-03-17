# ============================================================
#   SAATHI AI — UI (OpenCV draw functions)
# ============================================================

import cv2
from config import (DECISION_TIMER, ACTION_MESSAGES,
                    emotion_messages, PHASE_DETECTING, PHASE_DECIDED)


def draw_ui(frame, caller, time_left,
            emotion, confidence,
            action, color, phase,
            voice_status, decision_source):

    h, w = frame.shape[:2]

    # ── Top bar ──
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

    # ── Timer bar ──
    timer_width = int((time_left / DECISION_TIMER) * w)
    if time_left > 6:   tc = (0, 255, 0)
    elif time_left > 3: tc = (0, 165, 255)
    else:               tc = (0, 0, 255)

    cv2.rectangle(frame, (0, 135), (w, 152), (40, 40, 40), -1)
    cv2.rectangle(frame, (0, 135), (timer_width, 152), tc, -1)
    cv2.putText(frame, f"{time_left:.1f}s",
                (w - 58, 149), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (255, 255, 255), 1)

    # ── Voice status bar ──
    cv2.rectangle(frame, (0, 152), (w, 172), (30, 30, 30), -1)
    cv2.putText(frame, voice_status,
                (10, 167), cv2.FONT_HERSHEY_SIMPLEX,
                0.42, (100, 255, 200), 1)

    # ── Bottom panel ──
    if phase == PHASE_DETECTING:
        cv2.rectangle(frame, (0, h - 130), (w, h), (20, 20, 20), -1)
        cv2.putText(frame, "SAATHI READING YOUR MOOD...",
                    (20, h - 105), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (150, 150, 150), 1)
        cv2.putText(frame, emotion.upper(),
                    (20, h - 60), cv2.FONT_HERSHEY_SIMPLEX,
                    1.6, color, 3)

        bar = int((confidence / 100) * (w - 40))
        cv2.rectangle(frame, (20, h - 40), (w-20, h-24), (60, 60, 60), -1)
        cv2.rectangle(frame, (20, h - 40), (20+bar, h-24), color, -1)
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

        if action in ACTION_MESSAGES:
            cv2.putText(frame, "Press M to select message  |  Q to dismiss",
                        (20, h - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.42, (100, 255, 200), 1)
        else:
            cv2.putText(frame, "Press Q to dismiss",
                        (20, h - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.45, (100, 100, 100), 1)


def draw_message_box(frame, action, messages, selected_idx):
    h, w = frame.shape[:2]

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    box_x, box_y = 40, 140
    box_w, box_h = w - 80, h - 200
    cv2.rectangle(frame, (box_x, box_y),
                  (box_x+box_w, box_y+box_h), (30, 30, 30), -1)
    cv2.rectangle(frame, (box_x, box_y),
                  (box_x+box_w, box_y+box_h), (80, 80, 80), 2)

    title_color = (0, 0, 255) if action == "REJECT CALL" else (255, 100, 0)
    cv2.putText(frame, "SELECT MESSAGE TO SEND",
                (box_x+20, box_y+35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, title_color, 2)
    cv2.putText(frame, f"Action: {action}",
                (box_x+20, box_y+58),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1)
    cv2.line(frame,
             (box_x+15, box_y+68),
             (box_x+box_w-15, box_y+68), (60, 60, 60), 1)

    for i, msg in enumerate(messages):
        y_pos       = box_y + 100 + i * 52
        is_selected = (i == selected_idx)

        if is_selected:
            cv2.rectangle(frame,
                          (box_x+15, y_pos-22),
                          (box_x+box_w-15, y_pos+18),
                          (50, 50, 50), -1)
            cv2.rectangle(frame,
                          (box_x+15, y_pos-22),
                          (box_x+box_w-15, y_pos+18),
                          title_color, 2)

        num_color = title_color if is_selected else (100, 100, 100)
        msg_color = (255, 255, 255) if is_selected else (180, 180, 180)

        cv2.putText(frame, f"[{i+1}]",
                    (box_x+25, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, num_color, 2)
        cv2.putText(frame, msg,
                    (box_x+70, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, msg_color, 1)

    cv2.putText(frame,
                "Press 1-4 to select   |   ENTER to confirm   |   B to go back",
                (box_x+20, box_y+box_h-20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 100), 1)


def draw_message_sent(frame, action, sent_message, decision_source):
    h, w = frame.shape[:2]

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    badge_color = (100, 255, 200) if decision_source == "voice" else (100, 200, 255)
    badge_text  = "[ VOICE COMMAND ]" if decision_source == "voice" else "[ EMOTION DETECTED ]"
    cv2.putText(frame, badge_text,
                (40, h//2 - 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, badge_color, 1)

    action_color = (0, 0, 255) if action == "REJECT CALL" else (255, 100, 0)
    cv2.putText(frame, action,
                (40, h//2 - 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1.3, action_color, 3)

    cv2.putText(frame, "MESSAGE SENT",
                (40, h//2 - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 100), 2)
    cv2.putText(frame, f"\"{sent_message}\"",
                (40, h//2 + 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1)
    cv2.putText(frame, "Press Q to dismiss",
                (40, h//2 + 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 100, 100), 1)
