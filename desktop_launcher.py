import os
import sys
import threading
import time

import uvicorn
import webview


def get_base_path():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def set_working_directory():
    os.chdir(get_base_path())


def start_server():
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="error"
    )


if __name__ == "__main__":
    set_working_directory()

    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    time.sleep(2)

    webview.create_window(
        title="Trading Journal",
        url="http://127.0.0.1:8000",
        width=1300,
        height=850,
        resizable=True
    )

    webview.start()