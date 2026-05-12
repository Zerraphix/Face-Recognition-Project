from db import get_connection


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
                logging.security_picture_path
            FROM logging
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
                logging.security_picture_path
            FROM logging
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
            DELETE FROM logging
            WHERE log_id = ?
        """, (log_id,))

        conn.commit()

        return cur.rowcount > 0

    except Exception as e:
        if conn:
            conn.rollback()

        raise e

    finally:
        if conn:
            conn.close()