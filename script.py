# # import psycopg

# # conn = psycopg.connect(
# #     host="localhost",
# #     port=7496,
# #     dbname="biotime",
# #     user="postgres",
# #     password="mon_mot_de_passe"
# # )

# # with conn.cursor() as cur:
# #     cur.execute("""
# #         SELECT table_name
# #         FROM information_schema.tables
# #         WHERE table_schema = 'public'
# #         ORDER BY table_name;
# #     """)
# #     tables = cur.fetchall()

# #     print("Tables dans la base :")
# #     for table in tables:
# #         print("-", table[0])

# # conn.close()
# import psycopg2

# conn = psycopg2.connect(
#     host="localhost",
#     port=7496,
#     dbname="biotime",
#     user="postgres",
#     password="mon_mot_de_passe"
# )

# with conn.cursor() as cur:
#     cur.execute("""
#         SELECT
#             column_name,
#             data_type,
#             is_nullable,
#             column_default
#         FROM information_schema.columns
#         WHERE table_schema = 'public'
#           AND table_name = 'iclock_transaction'
#         ORDER BY ordinal_position;
#     """)

#     columns = cur.fetchall()

#     print("Structure de la table iclock_transaction :")
#     print("-" * 80)

#     for col in columns:
#         print(f"Colonne : {col[0]}")
#         print(f"  Type      : {col[1]}")
#         print(f"  Nullable  : {col[2]}")
#         print(f"  Défaut    : {col[3]}")
#         print()
# import psycopg2

# conn = psycopg2.connect(
#     host="localhost",
#     port=7496,
#     dbname="biotime",
#     user="postgres",
#     password="mon_mot_de_passe"
# )

# with conn.cursor() as cur:

#     # ==================================================
#     # 1. Structure de la table
#     # ==================================================

#     cur.execute("""
#         SELECT
#             column_name,
#             data_type,
#             is_nullable,
#             column_default
#         FROM information_schema.columns
#         WHERE table_schema = 'public'
#           AND table_name = 'personnel_employee_area'
#         ORDER BY ordinal_position;
#     """)

#     columns = cur.fetchall()

#     print("Structure de la table personnel_employee_area :")
#     print("-" * 80)

#     for col in columns:
#         print(f"Colonne : {col[0]}")
#         print(f"  Type      : {col[1]}")
#         print(f"  Nullable  : {col[2]}")
#         print(f"  Défaut    : {col[3]}")
#         print()


#     # ==================================================
#     # 2. Voir les données de la table
#     # ==================================================

#     cur.execute("""
#       SELECT
#     tc.table_schema,
#     tc.table_name,
#     tc.constraint_name,
#     kcu.column_name,
#     ccu.table_schema AS foreign_table_schema,
#     ccu.table_name AS foreign_table_name,
#     ccu.column_name AS foreign_column_name
# FROM information_schema.table_constraints AS tc
# JOIN information_schema.key_column_usage AS kcu
#     ON tc.constraint_name = kcu.constraint_name
#     AND tc.table_schema = kcu.table_schema
# JOIN information_schema.constraint_column_usage AS ccu
#     ON ccu.constraint_name = tc.constraint_name
#     AND ccu.table_schema = tc.table_schema
# WHERE tc.constraint_type = 'FOREIGN KEY'
#   AND ccu.table_schema = 'public'
#   AND ccu.table_name = 'personnel_employee_area'
#   AND ccu.column_name = 'id';
#     """)

#     rows = cur.fetchall()

#     print("\nDonnées de personnel_employee_area :")
#     print("-" * 80)

#     for row in rows:
#         print(row)


# conn.close()

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
            FROM public.personnel_employee
            WHERE id = 12;
        """)

        rows = cur.fetchall()

        # Noms des colonnes
        column_names = [desc[0] for desc in cur.description]

        print("Données de personnel_employee avec id = 12 :")
        print("-" * 80)

        print(" | ".join(column_names))
        print("-" * 80)

        for row in rows:
            print(" | ".join(str(value) for value in row))

        if not rows:
            print("Aucun utilisateur trouvé avec id = 12.")

finally:
    conn.close()
