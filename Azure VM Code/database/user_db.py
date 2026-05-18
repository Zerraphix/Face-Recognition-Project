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

def get_user_by_email(email):
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
                role.role_name,

                CASE
                    WHEN facedata.face_id IS NOT NULL THEN 1
                    ELSE 0
                END AS has_face_data

            FROM user
            JOIN role ON user.role_id = role.role_id

            LEFT JOIN facedata 
                ON user.user_id = facedata.user_id
                AND facedata.is_active = 1

            WHERE user.email = ?
        """, (email,))

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
            
def update_user(
    user_id,
    first_name=None,
    last_name=None,
    email=None,
    password_hash=None,
    role_id=None
):
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT user_id
            FROM user
            WHERE user_id = ?
        """, (user_id,))

        row = cur.fetchone()

        if row is None:
            return None

        fields = []
        values = []

        if first_name is not None:
            fields.append("first_name = ?")
            values.append(first_name)

        if last_name is not None:
            fields.append("last_name = ?")
            values.append(last_name)

        if email is not None:
            fields.append("email = ?")
            values.append(email)

        if password_hash is not None:
            fields.append("password_hash = ?")
            values.append(password_hash)

        if role_id is not None:
            fields.append("role_id = ?")
            values.append(role_id)

        if not fields:
            return get_user_by_id(user_id)

        values.append(user_id)

        cur.execute(f"""
            UPDATE user
            SET {", ".join(fields)}
            WHERE user_id = ?
        """, values)

        conn.commit()

        return get_user_by_id(user_id)

    except Exception as e:
        if conn:
            conn.rollback()

        raise e

    finally:
        if conn:
            conn.close()