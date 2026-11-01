import os

def load_env_file(filepath=None):
    """Loads environment variables from a .env file if present."""
    if filepath is None:
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip("\"'")
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

# Load .env if present
load_env_file()

# Database connection configuration
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "root")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "erp_academic_db")
DATA_MODE = os.environ.get("DATA_MODE", "csv").strip().lower()

if DATA_MODE not in {"csv", "mysql"}:
    raise ValueError("DATA_MODE must be either 'csv' or 'mysql'")

def get_db_config(include_db=True):
    config = {
        "host": MYSQL_HOST,
        "port": MYSQL_PORT,
        "user": MYSQL_USER,
        "password": MYSQL_PASSWORD,
    }
    if include_db:
        config["database"] = MYSQL_DATABASE
    return config
