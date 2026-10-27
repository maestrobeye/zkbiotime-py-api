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
           SELECT
    tc.table_name,
    kcu.column_name,
    tc.constraint_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
   AND tc.constraint_schema = kcu.constraint_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
   AND ccu.constraint_schema = tc.constraint_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND ccu.table_name = 'auth_user'
  AND ccu.column_name = 'id'
ORDER BY tc.table_name;
        """)

        # Afficher les noms des colonnes
        columns = [desc[0] for desc in cur.description]
        print(columns)

        # Afficher toutes les données
        for row in cur.fetchall():
            print(row)

finally:
    conn.close()