# run.py
import os
from dotenv import load_dotenv

from app import create_app

# Load environment variables
load_dotenv()

# Create Flask application
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'

    print(
        f"""
    ============================================
    MedTrack Analytics API
    ============================================
    Environment: {'Development' if debug else 'Production'}
    Database: {os.getenv('DATABASE_URL', 'Not configured')}
    Port: {port}
    Debug: {debug}
    ============================================
    Starting server...
    """
    )

    app.run(host='0.0.0.0', port=port, debug=debug)
