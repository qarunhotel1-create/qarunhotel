from hotel import create_app
import sys
import os

print("Initializing Hotel Management System...")
sys.stdout.flush()

try:
    # If running as a PyInstaller executable, ensure CWD is the executable directory
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        try:
            os.chdir(exe_dir)
        except Exception:
            pass

    app = create_app()
    
    # --- Auto Migration for Customer Tracking Columns ---
    from hotel import db
    from sqlalchemy import text
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Check current columns
                result = conn.execute(text("PRAGMA table_info(customers)"))
                columns = [row[1] for row in result]
                if 'created_by' not in columns:
                    print("Auto-migration: Adding 'created_by' column...")
                    conn.execute(text("ALTER TABLE customers ADD COLUMN created_by VARCHAR(100)"))
                if 'updated_by' not in columns:
                    print("Auto-migration: Adding 'updated_by' column...")
                    conn.execute(text("ALTER TABLE customers ADD COLUMN updated_by VARCHAR(100)"))
                conn.commit()
                
                # --- Fill and correct creator/updater info ---
                result = conn.execute(text("SELECT id FROM customers ORDER BY id ASC"))
                all_customers = result.fetchall()
                
                # Get all user mapping (username -> full_name)
                user_res = conn.execute(text("SELECT username, full_name FROM users"))
                users_info = {r[0]: r[1] for r in user_res.fetchall()}
                
                # Get known creators from bookings using Full Name
                known_creators_by_booking = {} # customer_id -> full_name
                booking_res = conn.execute(text("""
                    SELECT c.id, u.full_name 
                    FROM customers c
                    JOIN bookings b ON c.id = b.customer_id
                    JOIN users u ON b.user_id = u.id
                    WHERE b.id = (SELECT id FROM bookings WHERE customer_id = c.id ORDER BY created_at ASC LIMIT 1)
                """))
                for row in booking_res:
                    known_creators_by_booking[row[0]] = row[1]
                
                # Define a helper to get full name from username mapping
                def get_full_name(name):
                    if not name: return None
                    if name in users_info: return users_info[name]
                    # Case-insensitive check
                    for uname, fname in users_info.items():
                        if uname.lower() == name.lower():
                            return fname
                    return name

                for i, cust_row in enumerate(all_customers):
                    cid = cust_row[0]
                    # Get current values
                    curr_res = conn.execute(text("SELECT created_by, updated_by FROM customers WHERE id = :cid"), {"cid": cid})
                    curr_row = curr_res.fetchone()
                    c_by, u_by = curr_row[0], curr_row[1]
                    
                    # 1. Correct existing usernames to full names
                    new_c_by = get_full_name(c_by)
                    new_u_by = get_full_name(u_by)
                    
                    # 2. If created_by is still missing or is a username, interpolate
                    if not new_c_by or new_c_by in users_info:
                        new_c_by = known_creators_by_booking.get(cid)
                        if not new_c_by:
                            prev_c = None
                            for j in range(i - 1, -1, -1):
                                if all_customers[j][0] in known_creators_by_booking:
                                    prev_c = known_creators_by_booking[all_customers[j][0]]
                                    break
                            next_c = None
                            for j in range(i + 1, len(all_customers)):
                                if all_customers[j][0] in known_creators_by_booking:
                                    next_c = known_creators_by_booking[all_customers[j][0]]
                                    break
                            if prev_c == next_c and prev_c: new_c_by = prev_c
                            elif prev_c: new_c_by = prev_c
                            elif next_c: new_c_by = next_c
                            else: new_c_by = users_info.get('admin', 'admin')
                    
                    # 3. If updated_by is missing or is a username, use created_by or translate
                    if not new_u_by or new_u_by in users_info:
                        new_u_by = new_c_by
                    
                    # Update if changed
                    if new_c_by != c_by or new_u_by != u_by:
                        conn.execute(text("UPDATE customers SET created_by = :c, updated_by = :u WHERE id = :cid"), 
                                     {"c": new_c_by, "u": new_u_by, "cid": cid})
                
                conn.commit()
                # --- End Fill missing info ---
        except Exception as migrate_err:
            print(f"Auto-migration warning: {migrate_err}")
    # --- End Auto Migration ---
    
    print("App created successfully!")
    sys.stdout.flush()
except Exception as e:
    print(f"Error creating app: {e}")
    sys.stdout.flush()
    sys.exit(1)

if __name__ == '__main__':
    # Read host/port from environment if provided
    host = os.getenv('HOST', '0.0.0.0')
    try:
        port = int(os.getenv('PORT', '5000'))
    except ValueError:
        port = 5000

    print("Starting Hotel Management System...")
    if host == '0.0.0.0':
        print(f"Server is running on all network interfaces.")
        print(f"Access it locally at: http://localhost:{port} or http://127.0.0.1:{port}")
        print("To access from another device (like a mobile), find this computer's IP address and use that (e.g., http://192.168.1.100:5000).")
    else:
        print(f"Server will be available at: http://{host}:{port}")

    print("Username: admin")
    print("Password: admin")
    print("=" * 50)
    sys.stdout.flush()

    try:
        # Disable debug in frozen (end-user) executable
        debug_mode = False if getattr(sys, 'frozen', False) else True
        app.run(host=host, port=port, debug=debug_mode)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.stdout.flush()
        input("Press Enter to exit...")