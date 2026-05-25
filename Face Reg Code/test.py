from api_client import login, verify_pin
from face_loader import load_face_images_from_api
from log_sender import send_log
from backup_codes import get_active_backup_code_id, verify_active_backup_code

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

result = verify_pin("12345678")

if result["approved"]:
    user_id = result["user_id"]
    print(f"Adgang godkendt for user_id {user_id}")
else:
    print("Adgang afvist")
    
    
    
active_id = get_active_backup_code_id()

if active_id is None:
    print("Ingen backup-koder tilbage.")
    exit()

print(f"Aktiv backup ID: {active_id}")

backup_pin = input("Indtast 8-cifret backup PIN: ")

if verify_active_backup_code(backup_pin):
    print("Adgang godkendt med backup-kode.")
else:
    print("Adgang afvist.")