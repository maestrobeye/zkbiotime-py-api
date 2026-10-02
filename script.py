import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=7496,
    dbname="biotime",
    user="postgres",
    password="mon_mot_de_passe"
)

cur = conn.cursor()

date_autorisee = "20260709"
date_expiration = "20260907"

# Formats possibles dans PostgreSQL
formats_autorisee = [
    "20260709",
    "2026-07-09",
    "2026-07-09 00:00:00",
]

formats_expiration = [
    "20260907",
    "2026-09-07",
    "2026-09-07 00:00:00",
]

# Récupérer toutes les colonnes utilisables
cur.execute("""
    SELECT table_schema, table_name, column_name, data_type
    FROM information_schema.columns
    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
      AND data_type IN (
          'character varying',
          'character',
          'text',
          'integer',
          'bigint',
          'smallint',
          'numeric',
          'date',
          'timestamp without time zone',
          'timestamp with time zone'
      )
    ORDER BY table_schema, table_name, ordinal_position;
""")

colonnes = cur.fetchall()

# Regrouper les colonnes par table
tables = {}

for schema, table, colonne, data_type in colonnes:
    key = (schema, table)

    if key not in tables:
        tables[key] = []

    tables[key].append((colonne, data_type))


trouves = 0

for (schema, table), cols in tables.items():

    # On teste toutes les paires de colonnes
    for colonne1, type1 in cols:
        for colonne2, type2 in cols:

            if colonne1 == colonne2:
                continue

            s = '"' + schema.replace('"', '""') + '"'
            t = '"' + table.replace('"', '""') + '"'
            c1 = '"' + colonne1.replace('"', '""') + '"'
            c2 = '"' + colonne2.replace('"', '""') + '"'

            try:

                requete = f"""
                    SELECT *
                    FROM {s}.{t}
                    WHERE CAST({c1} AS TEXT) = ANY(%s)
                      AND CAST({c2} AS TEXT) = ANY(%s)
                    LIMIT 20;
                """

                cur.execute(
                    requete,
                    (formats_autorisee, formats_expiration)
                )

                resultats = cur.fetchall()

                if resultats:
                    trouves += len(resultats)

                    print("\n" + "=" * 100)
                    print(f"TABLE : {schema}.{table}")
                    print(f"DATE AUTORISÉE : {colonne1}")
                    print(f"DATE EXPIRATION : {colonne2}")
                    print(f"RÉSULTATS : {len(resultats)}")
                    print("=" * 100)

                    for ligne in resultats:
                        print(ligne)

            except Exception as e:
                conn.rollback()

print("\n" + "=" * 100)
print(f"Recherche terminée.")
print(f"Nombre de résultats trouvés : {trouves}")
print("=" * 100)

cur.close()
conn.close()