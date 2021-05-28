from osprey_flask_app import create_app
import argparse

#parser = argparse.ArgumentParser(description="Initialize hostname and port number.")
#parser.add_argument("--host", type=str, default="0.0.0.0", help="Host name for running app.")
#parser.add_argument("--port", type=int, default=5000, help="Port number for running app.")
#args = parser.parse_args()

app = create_app()


if __name__ == "__main__":
    app.run()
