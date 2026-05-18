from api_client import login
from face_loader import load_face_images_from_api
from log_sender import send_log


login()

faces = load_face_images_from_api()

print()
print("Faces hentet:")
for face in faces:
    print(face)

if len(faces) == 0:
    print("Ingen faces blev hentet.")
    exit()

first_face = faces[0]

print()
print("Sender test log...")

new_log = send_log(
    user_id=first_face["user_id"],
    device="PC Test Client",
    used_method="API Test",
    access_granted=True,
    result="Test log from local Python client",
    image_path=first_face["image_path"]
)

print()
print("Log oprettet:")
print(new_log)