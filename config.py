import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "creche-management-secret-key-2026")
    
    # Database Mode: "AUTO" (tries MySQL, falls back to SQLite), "MYSQL", or "SQLITE"
    DB_TYPE = os.environ.get("DB_TYPE", "AUTO")
    
    # MySQL Settings
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DB = os.environ.get("MYSQL_DB", "daycare_db")
    
    # SQLite Settings (zero-setup fallback)
    SQLITE_PATH = os.path.join(os.path.dirname(__file__), "daycare.db")
