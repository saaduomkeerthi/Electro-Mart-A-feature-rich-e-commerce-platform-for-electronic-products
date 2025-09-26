# run.py - Our New Smart Launcher

import sys
import os

# This is the most important part of the script.
# It tells Python to add the current directory to its list of search paths.
# This allows the import statement on the next line to find your 'electronic_ecommerce' package.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Now that Python knows where to look, we can import the factory function.
# It will find the 'electronic_ecommerce' folder and the __init__.py file inside it.
from electronic_ecommerce import create_app

# Create the application instance by calling the factory.
app = create_app()

# This is the standard entry point for running the application.
if __name__ == "__main__":
    # Start the Flask development server.
    app.run()