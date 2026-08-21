import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Development-only server. Production deployments must use a WSGI server
    # such as Gunicorn or the hosting provider's WSGI process.
    app.run(
        debug=False,
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000"))
    )
