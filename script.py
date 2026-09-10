# import psycopg

# conn = psycopg.connect(
#     host="localhost",
#     port=7496,
#     dbname="biotime",
#     user="postgres",
#     password="mon_mot_de_passe"
# )

# with conn.cursor() as cur:
#     cur.execute("""
#         SELECT table_name
#         FROM information_schema.tables
#         WHERE table_schema = 'public'
#         ORDER BY table_name;
#     """)
#     tables = cur.fetchall()

#     print("Tables dans la base :")
#     for table in tables:
#         print("-", table[0])

# conn.close()
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=7496,
    dbname="biotime",
    user="postgres",
    password="mon_mot_de_passe"
)

with conn.cursor() as cur:
    cur.execute("""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'iclock_transaction'
        ORDER BY ordinal_position;
    """)

    columns = cur.fetchall()

    print("Structure de la table iclock_transaction :")
    print("-" * 80)

    for col in columns:
        print(f"Colonne : {col[0]}")
        print(f"  Type      : {col[1]}")
        print(f"  Nullable  : {col[2]}")
        print(f"  Défaut    : {col[3]}")
        print()