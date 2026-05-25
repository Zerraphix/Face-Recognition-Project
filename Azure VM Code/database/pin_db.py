from db import get_connection


def get_all_pins():
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                pin.pin_id,
                pin.user_id,
                user.first_name,
                user.last_name,
                user.email,
                user.role_id,
                role.role_name,
                pin.pin_code_hash,
                pin.expiration_time,
                pin.is_active
            FROM pin
            INNER JOIN user ON pin.user_id = user.user_id
            INNER JOIN role ON user.role_id = role.role_id
            ORDER BY pin.expiration_time DESC
        """)

        rows = cur.fetchall()
        return [dict(row) for row in rows]

    finally:
        if conn:
            conn.close()



def get_pin_by_id(pin_id):
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                pin.pin_id,
                pin.user_id,
                user.first_name,
                user.last_name,
                user.email,
                user.role_id,
                role.role_name,
                pin.pin_code_hash,
                pin.expiration_time,
                pin.is_active
            FROM pin
            INNER JOIN user ON pin.user_id = user.user_id
            INNER JOIN role ON user.role_id = role.role_id
            WHERE pin.pin_id = ?
        """, (pin_id,))

        row = cur.fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        if conn:
            conn.close()
                


def create_pin(user_id, pin_code_hash, expiration_time, is_active):
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO pin (
                user_id,
                pin_code_hash,
                expiration_time,
                is_active
            )
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            pin_code_hash,
            expiration_time,
            is_active
        ))

        conn.commit()

        new_pin_id = cur.lastrowid
        return get_pin_by_id(new_pin_id)

    except Exception as e:
        if conn:
            conn.rollback()

        raise e

    finally:
        if conn:
            conn.close()


def delete_pin(pin_id):
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            DELETE FROM pin
            WHERE pin_id = ?
        """, (pin_id,))

        conn.commit()

        return cur.rowcount > 0

    except Exception as e:
        if conn:
            conn.rollback()

        raise e

    finally:
        if conn:
            conn.close()
            
def get_active_pins():
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                pin.pin_id,
                pin.user_id,
                pin.pin_code_hash,
                pin.expiration_time,
                pin.is_active
            FROM pin
            WHERE pin.is_active = 1
        """, ())

        rows = cur.fetchall()
        return [dict(row) for row in rows]

    finally:
        if conn:
            conn.close()