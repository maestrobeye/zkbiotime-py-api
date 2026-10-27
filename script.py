import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=7496,
    dbname="biotime",
    user="postgres",
    password="mon_mot_de_passe"
)

try:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT *
            FROM public.auth_user;
        """)

        # Afficher les noms des colonnes
        columns = [desc[0] for desc in cur.description]
        print(columns)

        # Afficher toutes les données
        for row in cur.fetchall():
            print(row)

finally:
    conn.close()