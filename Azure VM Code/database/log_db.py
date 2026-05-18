from db import get_connection
from services.file_service import delete_file


def get_all_logs():
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                logging.log_id,
                logging.user_id,
                logging.device,
                logging.used_method,
                logging.timestamp,
                logging.access_granted,
                logging.result,
                logging.security_picture_path,
                user.first_name,
                user.last_name,
                user.email,
                user.role_id,
                role.role_name
            FROM logging
            INNER JOIN user ON logging.user_id = user.user_id
            INNER JOIN role ON user.role_id = role.role_id
            ORDER BY logging.timestamp DESC
        """)

        rows = cur.fetchall()
        return [dict(row) for row in rows]

    finally:
        if conn:
            conn.close()


def get_log_by_id(log_id):
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                logging.log_id,
                logging.user_id,
                logging.device,
                logging.used_method,
                logging.timestamp,
                logging.access_granted,
                logging.result,
                logging.security_picture_path,
                user.first_name,
                user.last_name,
                user.email,
                user.role_id,
                role.role_name
            FROM logging
            INNER JOIN user ON logging.user_id = user.user_id
            INNER JOIN role ON user.role_id = role.role_id
            WHERE logging.log_id = ?
        """, (log_id,))

        row = cur.fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        if conn:
            conn.close()
                


def create_log(user_id, device, used_method, access_granted, result, security_picture_path):
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO logging (
                user_id,
                device,
                used_method,
                access_granted,
                result,
                security_picture_path
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            device,
            used_method,
            access_granted,
            result,
            security_picture_path
        ))

        conn.commit()

        new_log_id = cur.lastrowid
        return get_log_by_id(new_log_id)

    except Exception as e:
        if conn:
            conn.rollback()

        raise e

    finally:
        if conn:
            conn.close()


def delete_log(log_id):
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT security_picture_path
            FROM logging
            WHERE log_id = ?
        """, (log_id,))

        row = cur.fetchone()

        if row is None:
            return False

        security_picture_path = row["security_picture_path"]

        cur.execute("""
            DELETE FROM logging
            WHERE log_id = ?
        """, (log_id,))

        conn.commit()

        delete_file(security_picture_path)

        conn.commit()

        return cur.rowcount > 0

    except Exception as e:
        if conn:
            conn.rollback()

        raise e

    finally:
        if conn:
            conn.close()