import os
from dotenv import load_dotenv

from app import create_app

# Load environment variables
load_dotenv()

# Create Flask application using factory pattern
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
