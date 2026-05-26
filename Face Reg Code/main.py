from picamera2 import Picamera2
import cv2
import face_recognition
import os
import numpy as np
from pathlib import Path
from datetime import datetime
import time
import threading

from api_client import login, verify_pin
from face_loader import load_face_images_from_api, clear_known_faces_folder
from log_sender import send_log
from backup_codes import get_active_backup_code_id, verify_active_backup_code
from keypad import get_pin_code, setup_keypad

from lcd import write_text, clear_lcd
from led import setup_leds, green_on, green_off, red_on, red_off, all_leds_off, clear_gpio


KNOWN_FACES_DIR = "known_faces"
CAPTURED_LOGS_DIR = "captured_logs"

TOLERANCE = 0.55
FRAME_RESIZE = 0.25
LOG_COOLDOWN_SECONDS = 10

UNKNOWN_USER_ID = 0

DEVICE_PROFILES = {
    "lager": {
        "device_name": "Lager kamera",
        "allowed_roles": ["Employee", "Admin"]
    },
    "admin_kontor": {
        "device_name": "Admin kontor kamera",
        "allowed_roles": ["Admin"]
    }
}

ACTIVE_PROFILE_NAME = "admin_kontor"
ACTIVE_PROFILE = DEVICE_PROFILES[ACTIVE_PROFILE_NAME]

known_face_encodings = []
known_face_users = []

last_logged_times = {}

api_online = False
running = True

picam2 = Picamera2()

def ensure_folders():
    Path(KNOWN_FACES_DIR).mkdir(exist_ok=True)
    Path(CAPTURED_LOGS_DIR).mkdir(exist_ok=True)

def show_status(message, seconds=0):
    print(message)
    write_text(message)

    if seconds > 0:
        time.sleep(seconds)

def access_granted_message(message="Adgang godkendt"):
    all_leds_off()
    green_on()
    write_text(message)
    time.sleep(2)
    green_off()
    write_text("Klar")

def access_denied_message(message="Adgang afvist"):
    all_leds_off()
    red_on()
    write_text(message)
    time.sleep(2)
    red_off()
    write_text("Klar")

def role_is_allowed(role_name):
    return role_name in ACTIVE_PROFILE["allowed_roles"]

def save_log_image(frame):
    filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".jpg"
    image_path = os.path.join(CAPTURED_LOGS_DIR, filename)

    cv2.imwrite(image_path, frame)

    return image_path

def should_send_log(key):
    now = time.time()
    last_logged = last_logged_times.get(key)

    if last_logged is None:
        last_logged_times[key] = now
        return True

    if now - last_logged >= LOG_COOLDOWN_SECONDS:
        last_logged_times[key] = now
        return True

    return False

def load_known_faces(face_records):
    print("Loader kendte ansigter...")

    known_face_encodings.clear()
    known_face_users.clear()

    face_lookup = {}

    for face in face_records:
        user_id = face["user_id"]
        face_lookup[user_id] = face

    for filename in os.listdir(KNOWN_FACES_DIR):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        image_path = os.path.join(KNOWN_FACES_DIR, filename)
        user_id_text = os.path.splitext(filename)[0]

        try:
            user_id = int(user_id_text)
        except ValueError:
            print(f"Springer over {filename}, filnavn er ikke user_id")
            continue

        face_data = face_lookup.get(user_id)

        if face_data is None:
            print(f"Springer over {filename}, user_id findes ikke i API data")
            continue

        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)

        if len(encodings) == 0:
            print(f"ADVARSEL: Ingen ansigt fundet i {filename}")
            continue

        known_face_encodings.append(encodings[0])
        known_face_users.append({
            "user_id": user_id,
            "first_name": face_data.get("first_name"),
            "last_name": face_data.get("last_name"),
            "role_name": face_data.get("role_name")
        })

        print(f"Indlæst user_id {user_id}, role {face_data.get('role_name')}")

    if len(known_face_encodings) == 0:
        print("Ingen kendte ansigter blev indlæst.")

def setup_online_mode():
    global api_online

    try:
        show_status("Forbinder til API...")
        login()

        show_status("Henter faces...")
        faces = load_face_images_from_api()

        load_known_faces(faces)

        api_online = True
        show_status("Online mode\nKlar", 1)
        return True

    except Exception as e:
        print(f"API offline eller fejl: {e}")

        api_online = False

        show_status("API offline\nFlusher faces", 2)

        try:
            clear_known_faces_folder()
        except Exception as clear_error:
            print(f"Kunne ikke flushe known_faces: {clear_error}")

        show_status("Offline mode\nBackup PIN", 2)
        return False

def handle_face_match(user, frame):
    user_id = user["user_id"]
    role_name = user["role_name"]

    cooldown_key = f"face_{user_id}"

    if not should_send_log(cooldown_key):
        return

    image_path = save_log_image(frame)

    if role_is_allowed(role_name):
        send_access_log(
            user_id=user_id,
            method="Face Recognition",
            access_granted=True,
            result=f"Access granted by face. Role: {role_name}",
            image_path=image_path
        )

        access_granted_message("Face godkendt")

    else:
        send_access_log(
            user_id=user_id,
            method="Face Recognition",
            access_granted=False,
            result=f"Access denied by role. Role: {role_name}",
            image_path=image_path
        )

        access_denied_message("Rolle afvist")

def send_access_log(user_id, method, access_granted, result, image_path=None):
    if not api_online:
        print("API offline, kan ikke sende log.")
        return

    try:
        send_log(
            user_id=user_id,
            device=ACTIVE_PROFILE["device_name"],
            used_method=method,
            access_granted=access_granted,
            result=result,
            image_path=image_path
        )

        print(f"Log sendt: {method}, user_id {user_id}, granted {access_granted}")

    except Exception as e:
        print(f"Kunne ikke sende log: {e}")

def keypad_loop():
    global running

    setup_keypad()

    while running:
        try:
            if api_online:
                write_text("Indtast PIN")
                pin_code = get_pin_code(8)

                result = verify_pin(pin_code)
                
                image_path = save_log_image(frame)

                if not result.get("approved"):
                    send_access_log(
                        user_id=UNKNOWN_USER_ID,
                        method="PIN",
                        access_granted=False,
                        result="Invalid PIN",
                        image_path=image_path
                    )

                    access_denied_message("Forkert PIN")
                    continue

                user_id = result["user_id"]
                role_name = result.get("role_name")

                if role_is_allowed(role_name):
                    send_access_log(
                        user_id=user_id,
                        method="PIN",
                        access_granted=True,
                        result=f"Access granted by PIN. Role: {role_name}",
                        image_path=image_path
                    )

                    access_granted_message("PIN godkendt")

                else:
                    send_access_log(
                        user_id=user_id,
                        method="PIN",
                        access_granted=False,
                        result=f"PIN valid, but role denied. Role: {role_name}",
                        image_path=image_path
                    )

                    access_denied_message("Rolle afvist")

            else:
                active_id = get_active_backup_code_id()

                if active_id is None:
                    write_text("Ingen backup\nkoder tilbage")
                    time.sleep(3)
                    continue

                write_text(f"Backup ID:\n{active_id}\nIndtast PIN")

                backup_pin = get_pin_code(8)

                if verify_active_backup_code(backup_pin):
                    save_log_image(frame)
                    access_granted_message("Backup godkendt")
                else:
                    save_log_image(frame)
                    access_denied_message("Backup afvist")

        except Exception as e:
            print(f"Keypad fejl: {e}")
            access_denied_message("Keypad fejl")
            time.sleep(1)

def setup_camera():
    picam2.configure(
        picam2.create_preview_configuration(
            main={"format": "XRGB8888", "size": (640, 480)}
        )
    )

    picam2.start()

def camera_loop():
    global running

    setup_camera()

    print("Kamera startet. Tryk Q for at stoppe.")

    while running:
        global frame
        frame = picam2.capture_array()

        if api_online and len(known_face_encodings) > 0:
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
                matched_user = None

                face_distances = face_recognition.face_distance(
                    known_face_encodings,
                    face_encoding
                )

                best_match_index = np.argmin(face_distances)

                if face_distances[best_match_index] < TOLERANCE:
                    matched_user = known_face_users[best_match_index]
                    display_name = f"User {matched_user['user_id']}"

                    handle_face_match(matched_user, frame)

                top, right, bottom, left = face_location

                top = int(top / FRAME_RESIZE)
                right = int(right / FRAME_RESIZE)
                bottom = int(bottom / FRAME_RESIZE)
                left = int(left / FRAME_RESIZE)

                color = (0, 255, 0) if matched_user is not None else (0, 0, 255)

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
            running = False
            break

    picam2.stop()
    cv2.destroyAllWindows()

def main():
    global running

    ensure_folders()
    setup_leds()

    write_text("Starter system...")
    time.sleep(1)

    setup_online_mode()

    keypad_thread = threading.Thread(target=keypad_loop, daemon=True)
    keypad_thread.start()

    try:
        camera_loop()

    finally:
        running = False
        all_leds_off()
        clear_lcd()
        clear_gpio()
        print("System stoppet.")


if __name__ == "__main__":
    main()