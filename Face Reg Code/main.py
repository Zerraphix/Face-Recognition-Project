from picamera2 import Picamera2
import cv2
import face_recognition
import os
import numpy as np
from pathlib import Path
from datetime import datetime
import time

from api_client import login
from face_loader import load_face_images_from_api
from log_sender import send_log


KNOWN_FACES_DIR = "known_faces"
CAPTURED_LOGS_DIR = "captured_logs"

TOLERANCE = 0.55
FRAME_RESIZE = 0.25

DEVICE_NAME = "Raspberry Pi Camera"
USED_METHOD = "Face Recognition"

# Undgår at sende 100 logs på samme person hvert sekund
LOG_COOLDOWN_SECONDS = 10

known_face_encodings = []
known_face_user_ids = []

last_logged_times = {}

picam2 = Picamera2()


def ensure_folders():
    Path(KNOWN_FACES_DIR).mkdir(exist_ok=True)
    Path(CAPTURED_LOGS_DIR).mkdir(exist_ok=True)


def load_known_faces():
    print("Loader kendte ansigter...")

    known_face_encodings.clear()
    known_face_user_ids.clear()

    for filename in os.listdir(KNOWN_FACES_DIR):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        image_path = os.path.join(KNOWN_FACES_DIR, filename)

        user_id_text = os.path.splitext(filename)[0]

        try:
            user_id = int(user_id_text)
        except ValueError:
            print(f"Springer over {filename}, filnavn er ikke et user_id")
            continue

        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)

        if len(encodings) == 0:
            print(f"ADVARSEL: Ingen ansigt fundet i {filename}")
            continue

        if len(encodings) > 1:
            print(f"ADVARSEL: Flere ansigter fundet i {filename}. Bruger det første.")

        known_face_encodings.append(encodings[0])
        known_face_user_ids.append(user_id)

        print(f"Indlæst user_id: {user_id}")

    if len(known_face_encodings) == 0:
        print("Ingen kendte ansigter blev indlæst.")
        exit()


def save_log_image(frame):
    filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".jpg"
    image_path = os.path.join(CAPTURED_LOGS_DIR, filename)

    cv2.imwrite(image_path, frame)

    return image_path


def should_send_log(user_id):
    now = time.time()

    last_logged = last_logged_times.get(user_id)

    if last_logged is None:
        last_logged_times[user_id] = now
        return True

    if now - last_logged >= LOG_COOLDOWN_SECONDS:
        last_logged_times[user_id] = now
        return True

    return False


def send_recognition_log(user_id, frame):
    if not should_send_log(user_id):
        return

    image_path = save_log_image(frame)

    try:
        send_log(
            user_id=user_id,
            device=DEVICE_NAME,
            used_method=USED_METHOD,
            access_granted=True,
            result="Access granted",
            image_path=image_path
        )

        print(f"Log sendt for user_id {user_id}")

    except Exception as e:
        print(f"Kunne ikke sende log for user_id {user_id}: {e}")


def setup_camera():
    picam2.configure(
        picam2.create_preview_configuration(
            main={"format": "XRGB8888", "size": (640, 480)}
        )
    )

    picam2.start()


def main():
    ensure_folders()

    print("Logger ind...")
    login()

    print("Henter billeder fra API...")
    load_face_images_from_api()

    load_known_faces()

    setup_camera()

    print("Kamera startet. Tryk Q for at stoppe.")

    while True:
        frame = picam2.capture_array()

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

        small_frame = cv2.resize(
            rgb_frame,
            (0, 0),
            fx=FRAME_RESIZE,
            fy=FRAME_RESIZE
        )

        face_locations = face_recognition.face_locations(small_frame)
        face_encodings = face_recognition.face_encodings(
            small_frame,
            face_locations
        )

        for face_encoding, face_location in zip(face_encodings, face_locations):
            display_name = "Ukendt"
            matched_user_id = None

            face_distances = face_recognition.face_distance(
                known_face_encodings,
                face_encoding
            )

            best_match_index = np.argmin(face_distances)

            if face_distances[best_match_index] < TOLERANCE:
                matched_user_id = known_face_user_ids[best_match_index]
                display_name = f"User {matched_user_id}"

                send_recognition_log(matched_user_id, frame)

            top, right, bottom, left = face_location

            top = int(top / FRAME_RESIZE)
            right = int(right / FRAME_RESIZE)
            bottom = int(bottom / FRAME_RESIZE)
            left = int(left / FRAME_RESIZE)

            color = (0, 255, 0) if matched_user_id is not None else (0, 0, 255)

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            cv2.rectangle(
                frame,
                (left, bottom - 35),
                (right, bottom),
                color,
                cv2.FILLED
            )

            cv2.putText(
                frame,
                display_name,
                (left + 6, bottom - 6),
                cv2.FONT_HERSHEY_DUPLEX,
                0.8,
                (255, 255, 255),
                1
            )

        cv2.imshow("Face recognition test", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    picam2.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()