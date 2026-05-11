from db import get_connection


def get_all_users():
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                user.user_id,
                user.first_name,
                user.last_name,
                user.email,
                user.password_hash,
                user.role_id,
                role.role_name
            FROM user
            INNER JOIN role ON user.role_id = role.role_id
            ORDER BY user.user_id
        """)

        rows = cur.fetchall()
        return [dict(row) for row in rows]

    finally:
        if conn:
            conn.close()


def get_user_by_id(user_id):
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                user.user_id,
                user.first_name,
                user.last_name,
                user.email,
                user.password_hash,
                user.role_id,
                role.role_name
            FROM user
            INNER JOIN role ON user.role_id = role.role_id
            WHERE user.user_id = ?
        """, (user_id,))

        row = cur.fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        if conn:
            conn.close()


def create_user(first_name, last_name, email, password_hash, role_id):
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO user (
                first_name,
                last_name,
                email,
                password_hash,
                role_id
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            first_name,
            last_name,
            email,
            password_hash,
            role_id
        ))

        conn.commit()

        new_user_id = cur.lastrowid
        return get_user_by_id(new_user_id)

    except Exception as e:
        if conn:
            conn.rollback()

        raise e

    finally:
        if conn:
            conn.close()


def delete_user(user_id):
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            DELETE FROM user
            WHERE user_id = ?
        """, (user_id,))

        conn.commit()

        return cur.rowcount > 0

    except Exception as e:
        if conn:
            conn.rollback()

        raise e

    finally:
        if conn:
            conn.close()