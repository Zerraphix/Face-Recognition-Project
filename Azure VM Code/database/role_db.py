from db import get_connection


def get_all_roles():
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT role_id, role_name
            FROM role
            ORDER BY role_id
        """)

        rows = cur.fetchall()
        return [dict(row) for row in rows]

    finally:
        if conn:
            conn.close()


def get_role_by_id(role_id):
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT role_id, role_name
            FROM role
            WHERE role_id = ?
        """, (role_id,))

        row = cur.fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        if conn:
            conn.close()