#!/bin/bash

# Define the absolute path to your Automation folder
AUTOMATION_DIR="/Automation"

# Activate the virtual environment (use the correct path)
source "$AUTOMATION_DIR/bin/activate"

# Run the Django server with SSL
"$AUTOMATION_DIR/bin/gunicorn" --chdir $AUTOMATION_DIR --bind 127.0.0.1:8000 Thermometer.wsgi:application
exit 0
