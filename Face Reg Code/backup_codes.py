import json
from pathlib import Path
from datetime import datetime

import bcrypt


BACKUP_CODES_FILE = Path("backup_codes.json")


def load_backup_data():
    if not BACKUP_CODES_FILE.exists():
        return {
            "active_code_id": None,
            "codes": {}
        }

    with open(BACKUP_CODES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_backup_data(data):
    with open(BACKUP_CODES_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def get_next_unused_code_id(data):
    codes = data.get("codes", {})

    for code_id, entry in codes.items():
        if entry.get("used") is False:
            return code_id

    return None


def ensure_active_backup_code():
    data = load_backup_data()

    active_code_id = data.get("active_code_id")
    codes = data.get("codes", {})

    if active_code_id in codes:
        active_entry = codes[active_code_id]

        if active_entry.get("used") is False:
            return active_code_id

    next_code_id = get_next_unused_code_id(data)

    data["active_code_id"] = next_code_id
    save_backup_data(data)

    return next_code_id


def get_active_backup_code_id():
    return ensure_active_backup_code()


def verify_active_backup_code(backup_pin):
    data = load_backup_data()

    active_code_id = ensure_active_backup_code()

    if active_code_id is None:
        print("Ingen ubrugte backup-koder tilbage.")
        return False

    entry = data["codes"].get(active_code_id)

    if entry is None:
        print("Aktiv backup-kode findes ikke i filen.")
        return False

    if entry.get("used") is True:
        print("Aktiv backup-kode er allerede brugt.")
        return False

    pin_hash = entry.get("pin_hash")

    if not pin_hash:
        print("Backup-kode mangler hash.")
        return False

    is_valid = bcrypt.checkpw(
        backup_pin.encode("utf-8"),
        pin_hash.encode("utf-8")
    )

    if not is_valid:
        print("Backup-kode matcher ikke.")
        return False

    entry["used"] = True
    entry["used_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    next_code_id = get_next_unused_code_id(data)
    data["active_code_id"] = next_code_id

    save_backup_data(data)

    print(f"Backup-kode {active_code_id} blev brugt.")
    
    if next_code_id:
        print(f"Næste backup ID er nu: {next_code_id}")
    else:
        print("Ingen ubrugte backup-koder tilbage.")

    return True