from pathlib import Path

from api_client import get_faces, get_image_url, download_file


KNOWN_FACES_FOLDER = Path("known_faces")


def load_face_images_from_api():
    KNOWN_FACES_FOLDER.mkdir(exist_ok=True)

    faces = get_faces()
    active_faces = []

    for face in faces:
        if not face.get("is_active"):
            continue

        face_picture_path = face.get("face_picture_path")

        if not face_picture_path:
            continue

        user_id = face["user_id"]
        image_url = get_image_url(face_picture_path)
        local_path = KNOWN_FACES_FOLDER / f"{user_id}.jpg"

        print("Image URL:", image_url)

        try:
            download_file(image_url, local_path)

            active_faces.append({
                "user_id": user_id,
                "face_id": face["face_id"],
                "first_name": face.get("first_name"),
                "last_name": face.get("last_name"),
                "email": face.get("email"),
                "image_path": str(local_path)
            })

            print(f"Hentede billede for user_id {user_id}: {local_path}")

        except Exception as e:
            print(f"Kunne ikke hente billede for user_id {user_id}: {e}")

    return active_faces