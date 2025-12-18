import psycopg

conn = psycopg.connect(
    host="localhost",
    port=7496,
    dbname="biotime",
    user="postgres",
    password="mon_mot_de_passe"
)

with conn.cursor() as cur:
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cur.fetchall()

    print("Tables dans la base :")
    for table in tables:
        print("-", table[0])

conn.close()
