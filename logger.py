import logging
import psycopg2
from utils.config import get_db_url

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

def log_event(level, message, module):
    logging.log(getattr(logging, level.upper()), f"[{module}] {message}")
    try:
        conn = psycopg2.connect(get_db_url())
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO automation_logs(level, message, module) VALUES (%s, %s, %s)",
            (level, message, module)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Failed to log to DB: {e}")