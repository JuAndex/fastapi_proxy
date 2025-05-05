import threading
import uvicorn
import time
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
        },
        "rotating_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "uvicorn_requests.log",
            "maxBytes": 5 * 1024 * 1024,  # 5 MB
            "backupCount": 3,
            "formatter": "default",
            "level": "INFO",
        },
    },
    "loggers": {
        "uvicorn.access": {
            "handlers": ["console", "rotating_file"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

logging.config.dictConfig(LOGGING_CONFIG)


class UvicornServer:
    def __init__(self, app, host="127.0.0.1", port=5000):
        self.config = uvicorn.Config(
            app=app, host=host, port=port, log_level="info", log_config=LOGGING_CONFIG
        )
        self.server = uvicorn.Server(config=self.config)
        self.thread = None

    def start(self):
        if self.thread and self.thread.is_alive():
            print("Server is already running.")
            return

        def run_server():
            # Run the server and handle shutdown gracefully
            self.server.run()

        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()

        # Wait for the server to actually start (optional)
        while not self.server.started:
            time.sleep(0.1)
        print("Uvicorn server started.")

    def stop(self):
        if not self.thread or not self.thread.is_alive():
            print("Server is not running.")
            return

        self.server.should_exit = True
        self.thread.join()
        print("Uvicorn server stopped.")
