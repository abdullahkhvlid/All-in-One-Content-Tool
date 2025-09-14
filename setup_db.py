import os
import psycopg2
from utils.config import get_db_url

def run():
    db_url = get_db_url()
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    with open(os.path.join(os.path.dirname(__file__), 'schema.sql'), 'r') as f:
        cur.execute(f.read())
    conn.commit()
    cur.close()
    conn.close()
    print('Database setup complete.')

if __name__ == '__main__':
    run()