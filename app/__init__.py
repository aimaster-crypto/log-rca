import os
from flask import Flask
from dotenv import load_dotenv


def create_app() -> Flask:
    # Load environment variables
    load_dotenv()
    # Ensure Chroma/PostHog telemetry is disabled at process start
    os.environ.setdefault("CHROMA_ANONYMIZED_TELEMETRY", "False")
    os.environ.setdefault("POSTHOG_DISABLED", "1")

    app = Flask(__name__, static_folder=os.path.join("static"), template_folder=os.path.join("templates"))

    # Secret key for session/CSRF (optional for this app)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-me")

    # Register routes
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
