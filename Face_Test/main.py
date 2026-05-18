from picamera2 import Picamera2
import cv2
import face_recognition
import os
import numpy as np

KNOWN_FACES_DIR = "known_faces"
TOLERANCE = 0.55
FRAME_RESIZE = 0.25

known_face_encodings = []
known_face_names = []

picam2 = Picamera2()


def load_known_faces():
    print("Loader kendte ansigter...")

    for filename in os.listdir(KNOWN_FACES_DIR):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        image_path = os.path.join(KNOWN_FACES_DIR, filename)
        name = os.path.splitext(filename)[0]

        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)

        if len(encodings) == 0:
            print(f"ADVARSEL: Ingen ansigt fundet i {filename}")
            continue

        if len(encodings) > 1:
            print(f"ADVARSEL: Flere ansigter fundet i {filename}. Bruger det første.")

        known_face_encodings.append(encodings[0])
        known_face_names.append(name)

        print(f"Indlæst: {name}")

    if len(known_face_encodings) == 0:
        print("Ingen kendte ansigter blev indlæst.")
        exit()


def main():
    load_known_faces()

    picam2.configure(
        picam2.create_preview_configuration(
            main={"format": "XRGB8888", "size": (640, 480)}
        )
    )

    picam2.start()

    print("Kamera startet. Tryk Q for at stoppe.")

    while True:
        frame = picam2.capture_array()

        small_frame = cv2.resize(
            frame, (0, 0),
            fx=FRAME_RESIZE,
            fy=FRAME_RESIZE
        )

        rgb_small_frame = cv2.cvtColor(
            small_frame,
            cv2.COLOR_BGR2RGB
        )

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(
            rgb_small_frame,
            face_locations
        )

        for face_encoding, face_location in zip(face_encodings, face_locations):

            name = "Ukendt"

            face_distances = face_recognition.face_distance(
                known_face_encodings,
                face_encoding
            )

            best_match_index = np.argmin(face_distances)

            if face_distances[best_match_index] < TOLERANCE:
                name = known_face_names[best_match_index]

            top, right, bottom, left = face_location

            top = int(top / FRAME_RESIZE)
            right = int(right / FRAME_RESIZE)
            bottom = int(bottom / FRAME_RESIZE)
            left = int(left / FRAME_RESIZE)

            color = (0, 255, 0) if name != "Ukendt" else (0, 0, 255)

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
                name,
                (left + 6, bottom - 6),
                cv2.FONT_HERSHEY_DUPLEX,
                0.8,
                (255, 255, 255),
                1
            )

        # Vis ALTID vinduet
        cv2.imshow("Face recognition test", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    picam2.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()