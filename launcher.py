import os
import sys
import threading
import time
import webbrowser
import uvicorn


def get_base_path():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def set_working_directory():
    if getattr(sys, "frozen", False):
        os.chdir(os.path.join(get_base_path(), "app"))
    else:
        os.chdir(get_base_path())


def open_browser():
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:8000")


if __name__ == "__main__":
    set_working_directory()

    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False
    )