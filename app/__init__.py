from flask import Flask
import os
os.environ['FLASK_ENV'] = 'development'


def create_app():
    app = Flask(__name__)

    from app.routes import main
    app.register_blueprint(main)
    
    app.config['DEBUG'] = True
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.debug = True

    return app
