from db import get_connection
from services.security_service import hash_pass

def create_tables():
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS role (
                role_id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT NOT NULL UNIQUE
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS user (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role_id INTEGER NOT NULL,
                FOREIGN KEY (role_id) REFERENCES role(role_id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS logging (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NULL,
                device TEXT NOT NULL,
                used_method TEXT NOT NULL,
                timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                access_granted BOOLEAN NOT NULL,
                result TEXT NOT NULL,
                security_picture_path TEXT NULL,
                FOREIGN KEY (user_id) REFERENCES user(user_id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS facedata (
                face_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NULL,
                face_encoding TEXT NULL,
                face_picture_path TEXT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN NOT NULL,
                FOREIGN KEY (user_id) REFERENCES user(user_id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS pin (
                pin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NULL,
                pin_code_hash TEXT NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expiration_time DATETIME NOT NULL,
                is_active BOOLEAN NOT NULL,
                FOREIGN KEY (user_id) REFERENCES user(user_id)
            )
        """)


        conn.commit()
        print("Tables created successfully")

    except Exception as e:
        print(f"Error creating tables: {e}")

        if conn:
            conn.rollback()

    finally:
        if conn:
            conn.close()


def seed_data():
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        roles = [
            ("Admin",),
            ("Employee",),
            ("Guest",)
        ]
        
        user = ("Admin", "User", "admin@example.com", hash_pass("password"), 1)

        cur.executemany("""
            INSERT OR IGNORE INTO role (role_name)
            VALUES (?)
        """, roles)

        cur.execute("""
            INSERT OR IGNORE INTO user (first_name, last_name, email, password_hash, role_id)
            VALUES (?, ?, ?, ?, ?)
        """, user)

        conn.commit()
        print("Roles seeded successfully")

    except Exception as e:
        print(f"Error seeding roles: {e}")

        if conn:
            conn.rollback()

    finally:
        if conn:
            conn.close()