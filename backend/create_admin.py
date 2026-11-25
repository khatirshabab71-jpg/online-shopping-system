"""Run locally with the cloud DB environment configured. Never expose as an API."""
from getpass import getpass
from auth import hash_password, validate_password_strength
from database import get_db_connection

def main():
    username = input('New admin username: ').strip()
    password = getpass('New admin password: ')
    good, message = validate_password_strength(password)
    if not username or not good:
        raise SystemExit(message or 'Username required')
    if password != getpass('Repeat password: '):
        raise SystemExit('Passwords do not match')
    conn = get_db_connection()
    if not conn:
        raise SystemExit('Database unavailable')
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO admins (username, password) VALUES (%s, %s)',
                    (username, hash_password(password)))
        conn.commit()
        cur.close()
        print('Admin created. No password was written to a file.')
    except Exception:
        conn.rollback()
        raise SystemExit('Could not create admin. Check schema and duplicate username.')
    finally:
        conn.close()

if __name__ == '__main__':
    main()
