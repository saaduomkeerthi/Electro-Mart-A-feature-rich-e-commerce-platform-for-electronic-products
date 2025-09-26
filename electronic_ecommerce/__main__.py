# electronic_ecommerce/__main__.py

# This file serves as the entry point when you run the package directly
# using the command: python -m electronic_ecommerce

# Use a relative import to find the 'create_app' factory function
# located in the __init__.py file of this same package.
from . import create_app

# Create the application instance by calling the factory.
# All the configuration and setup happens inside create_app().
app = create_app()

# This is the standard Python construct to ensure that the code inside
# this block only runs when the script is executed directly.
if __name__ == "__main__":
    # Start the Flask development server.
    # The debug mode, host, and port settings will be loaded from your
    # config.py file by the create_app() factory.
    app.run()