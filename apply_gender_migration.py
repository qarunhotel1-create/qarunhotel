from hotel import create_app, db
from flask_migrate import upgrade

app = create_app()
with app.app_context():
    print("Applying database migrations...")
    upgrade()
    print("Migrations applied successfully!")