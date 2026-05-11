from db import get_connection


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

        cur.executemany("""
            INSERT OR IGNORE INTO role (role_name)
            VALUES (?)
        """, roles)

        conn.commit()
        print("Roles seeded successfully")

    except Exception as e:
        print(f"Error seeding roles: {e}")

        if conn:
            conn.rollback()

    finally:
        if conn:
            conn.close()