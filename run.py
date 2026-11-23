import sys
import webbrowser
import threading
import time
from database import init_database, get_active_db_type
from app import app

def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    print("=" * 70)
    print("   DAYCARE & CRECHE MANAGEMENT SYSTEM - DBMS MINI PROJECT")
    print("   Technology: HTML, CSS, JavaScript, Python Flask, MySQL / SQLite")
    print("=" * 70)
    
    # Initialize DB & Seed Data
    try:
        init_database()
        active_db = get_active_db_type()
        print(f"[*] Database Status: Connected to [{active_db}] Engine")
        print("[*] Tables, Foreign Keys, Views, and Triggers are ready.")
    except Exception as e:
        print(f"[!] Database initialization error: {e}")

    print("[*] Starting web server on http://127.0.0.1:5000")
    print("[*] Press Ctrl+C in terminal to stop.")
    print("=" * 70)

    # Automatically launch default web browser
    threading.Thread(target=open_browser, daemon=True).start()

    # Launch Flask application
    app.run(host="127.0.0.1", port=5000, debug=False)
