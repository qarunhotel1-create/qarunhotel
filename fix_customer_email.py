from hotel import create_app
from hotel.models.customer import Customer
from hotel import db

def add_email_column():
    """Add email column to customers table if it doesn't exist"""
    app = create_app()
    with app.app_context():
        try:
            # Check if the email column exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('customers')]
            
            if 'email' not in columns:
                print("Adding email column to customers table...")
                with db.engine.connect() as connection:
                    with connection.begin():
                        connection.execute(db.text('ALTER TABLE customers ADD COLUMN email VARCHAR(120)'))
                print("Successfully added email column to customers table.")
            else:
                print("Email column already exists in customers table.")
                
        except Exception as e:
            print(f"Error adding email column: {str(e)}")
            raise

if __name__ == '__main__':
    add_email_column()
