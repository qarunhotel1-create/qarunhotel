
try:
    from hotel.routes import admin
    print("admin.py syntax is correct")
except ImportError as e:
    # Ignore import errors due to missing dependencies/app context, just checking syntax
    print(f"Import error (expected): {e}")
except SyntaxError as e:
    print(f"Syntax error in admin.py: {e}")

try:
    from hotel.routes import user
    print("user.py syntax is correct")
except ImportError as e:
    print(f"Import error (expected): {e}")
except SyntaxError as e:
    print(f"Syntax error in user.py: {e}")
