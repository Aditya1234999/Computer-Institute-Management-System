import psycopg2
from config import DB_CONFIG

def add_batch_timing_column():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE admissions ADD COLUMN IF NOT EXISTS batch_timing VARCHAR(50);")
        conn.commit()
        print("Successfully added batch_timing column!")
    except Exception as e:
        print("Error:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    add_batch_timing_column()
