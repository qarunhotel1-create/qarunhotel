import sqlite3
import os
import sys

db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'hotel.db')
db_path = os.path.abspath(db_path)

print('Using DB:', db_path)
if not os.path.exists(db_path):
    print('ERROR: DB file not found')
    sys.exit(1)

con = sqlite3.connect(db_path)
cur = con.cursor()

# Show columns before
cur.execute('PRAGMA table_info(users)')
cols_before = [c[1] for c in cur.fetchall()]
print('Before columns:', cols_before)

changed = False

if 'role' not in cols_before:
    try:
        cur.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20)")
        changed = True
        print('Added column: role')
    except Exception as e:
        print('WARN: Could not add column role:', e)

# Fill defaults
try:
    cur.execute("UPDATE users SET role='guest' WHERE role IS NULL")
    cur.execute("UPDATE users SET role='admin' WHERE username='admin'")
    con.commit()
except Exception as e:
    print('WARN: Update defaults failed:', e)

# Show columns after
cur.execute('PRAGMA table_info(users)')
cols_after = [c[1] for c in cur.fetchall()]
print('After columns:', cols_after)
print('Changed:', changed)

con.close()
print('Done.')
