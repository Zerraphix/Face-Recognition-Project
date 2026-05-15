from db import get_connection


def get_all_faces():
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                facedata.face_id,
                facedata.user_id,
                user.first_name,
                user.last_name,
                user.email,
                user.role_id,
                role.role_name,
                facedata.face_encoding,
                facedata.face_picture_path,
                facedata.created_at,
                facedata.is_active
            FROM facedata
            INNER JOIN user ON facedata.user_id = user.user_id
            INNER JOIN role ON user.role_id = role.role_id
            ORDER BY facedata.created_at DESC
        """)

        rows = cur.fetchall()
        return [dict(row) for row in rows]

    finally:
        if conn:
            conn.close()


def get_face_by_id(face_id):
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                facedata.face_id,
                facedata.user_id,
                user.first_name,
                user.last_name,
                user.email,
                user.role_id,
                role.role_name,
                facedata.face_encoding,
                facedata.face_picture_path,
                facedata.created_at,
                facedata.is_active
            FROM facedata
            INNER JOIN user ON facedata.user_id = user.user_id
            INNER JOIN role ON user.role_id = role.role_id
            WHERE facedata.face_id = ?
        """, (face_id,))

        row = cur.fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        if conn:
            conn.close()

                


def create_face(user_id, face_encoding, face_picture_path, is_active):
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO facedata (
                user_id,
                face_encoding,
                face_picture_path,
                is_active
            )
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            face_encoding,
            face_picture_path,
            is_active
        ))

        conn.commit()

        new_face_id = cur.lastrowid
        return get_face_by_id(new_face_id)

    except Exception as e:
        if conn:
            conn.rollback()

        raise e

    finally:
        if conn:
            conn.close()


def delete_face(face_id):
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            DELETE FROM facedata
            WHERE face_id = ?
        """, (face_id,))

        conn.commit()

        return cur.rowcount > 0

    except Exception as e:
        if conn:
            conn.rollback()

        raise e

    finally:
        if conn:
            conn.close()