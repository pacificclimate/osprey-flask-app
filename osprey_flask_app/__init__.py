from flask import Flask


def create_app(config="config.ProdConfig"):
    """Application factory for osprey flask app"""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config)

    with app.app_context():
        from .routes import data

        app.register_blueprint(data)

        return app
