from pathlib import Path

from api_client import get_faces, get_image_url, download_file


KNOWN_FACES_FOLDER = Path("known_faces")

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def clear_known_faces_folder():
    KNOWN_FACES_FOLDER.mkdir(exist_ok=True)

    for file_path in KNOWN_FACES_FOLDER.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS:
            file_path.unlink()
            print(f"Slettede lokalt billede: {file_path}")


def delete_inactive_local_faces(active_user_ids):
    KNOWN_FACES_FOLDER.mkdir(exist_ok=True)

    active_filenames = {
        f"{user_id}.jpg" for user_id in active_user_ids
    }

    for file_path in KNOWN_FACES_FOLDER.iterdir():
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
            continue

        if file_path.name not in active_filenames:
            file_path.unlink()
            print(f"Slettede forældet/inaktivt lokalt billede: {file_path}")


def load_face_images_from_api():
    KNOWN_FACES_FOLDER.mkdir(exist_ok=True)

    try:
        faces = get_faces()

    except Exception as e:
        print(f"Kunne ikke oprette forbindelse til API: {e}")
        print("Flusher alle lokale known_faces af sikkerhedsgrunde.")
        clear_known_faces_folder()
        return []

    active_faces = []
    active_user_ids = set()

    for face in faces:
        if not face.get("is_active"):
            continue

        face_picture_path = face.get("face_picture_path")

        if not face_picture_path:
            continue

        user_id = face["user_id"]
        active_user_ids.add(user_id)

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

            if local_path.exists():
                local_path.unlink()
                print(f"Slettede lokalt billede fordi download fejlede: {local_path}")

    delete_inactive_local_faces(active_user_ids)

    return active_faces