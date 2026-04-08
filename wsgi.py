import sys
import os

# Add the project directory to the sys.path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

from hotel import create_app

# Create the application object
application = create_app()

if __name__ == "__main__":
    application.run()
