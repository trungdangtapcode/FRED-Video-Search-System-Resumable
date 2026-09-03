from app import create_app
from flask_cors import CORS

import logging
import os

app = create_app()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)  # or INFO
    CORS(app, resources={r"/*": {"origins": "*"}})
    app.run(
        host=os.getenv("APP_HOST", "127.0.0.1"),
        port=int(os.getenv("APP_PORT", "50313")),
        debug=False,
    )
