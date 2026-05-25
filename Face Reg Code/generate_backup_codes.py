import json
import secrets
from pathlib import Path

import bcrypt


BACKUP_CODES_FILE = Path("backup_codes.json")


def generate_number_code(length):
    min_value = 10 ** (length - 1)
    max_value = (10 ** length) - 1

    return str(secrets.randbelow(max_value - min_value + 1) + min_value)


def generate_backup_codes(amount=10):
    data = {
        "active_code_id": None,
        "codes": {}
    }

    print("Backup-koder, gem listen sikkert:")
    print()

    for _ in range(amount):
        code_id = generate_number_code(4)

        while code_id in data["codes"]:
            code_id = generate_number_code(4)

        backup_pin = generate_number_code(8)

        pin_hash = bcrypt.hashpw(
            backup_pin.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        data["codes"][code_id] = {
            "pin_hash": pin_hash,
            "used": False,
            "used_at": None
        }

        print(f"ID {code_id} -> PIN {backup_pin}")

    first_code_id = next(iter(data["codes"]), None)
    data["active_code_id"] = first_code_id

    with open(BACKUP_CODES_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    print()
    print(f"Gemte backup-koder i {BACKUP_CODES_FILE}")
    print(f"Første aktive backup ID er: {first_code_id}")


if __name__ == "__main__":
    generate_backup_codes(amount=10)