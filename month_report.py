# from collections import defaultdict
# from datetime import date, datetime
# from io import BytesIO
# import re
# import unicodedata

# from fastapi import FastAPI, HTTPException
# from fastapi.responses import StreamingResponse
# from pydantic import BaseModel, Field
# from openpyxl import Workbook
# from openpyxl.styles import Font, PatternFill, Alignment
# from openpyxl.utils import get_column_letter


# app = FastAPI(
#     title="API de gestion du pointage",
#     version="1.0.0",
#     description="Génération automatique des rapports mensuels de pointage."
# )


# class RapportRequest(BaseModel):
#     pointages: list[dict] = Field(
#         ...,
#         description="Liste des pointages des employés"
#     )


# MOIS_FR = [
#     "Janvier", "Février", "Mars", "Avril",
#     "Mai", "Juin", "Juillet", "Août",
#     "Septembre", "Octobre", "Novembre", "Décembre"
# ]


# BLEU = "1A73E8"
# BLANC = "FFFFFF"
# ROUGE = "F4CCCC"
# VERT = "D9EAD3"
# GRIS = "E8EAED"

# def get_attendance_status(record):
#     check_in = record.get("clock_in")
#     check_out = record.get("clock_out")

#     if check_in and check_out:
#         return "P"

#     return "A"

# def normaliser(valeur):
#     texte = str(valeur or "").strip().lower()
#     texte = unicodedata.normalize("NFD", texte)
#     return "".join(
#         c for c in texte
#         if unicodedata.category(c) != "Mn"
#     )


# def obtenir(ligne, *noms):
#     """Recherche une colonne indépendamment des accents et majuscules."""
#     donnees = {
#         normaliser(k): v
#         for k, v in ligne.items()
#     }

#     for nom in noms:
#         cle = normaliser(nom)
#         if cle in donnees:
#             return donnees[cle]

#     return None


# def convertir_date(valeur):
#     if isinstance(valeur, datetime):
#         return valeur.date()

#     if isinstance(valeur, date):
#         return valeur

#     if valeur is None:
#         return None

#     texte = str(valeur).strip()

#     formats = [
#         "%Y-%m-%d",
#         "%d/%m/%Y",
#         "%Y-%m-%d %H:%M:%S",
#         "%Y-%m-%dT%H:%M:%S",
#         "%d-%m-%Y",
#     ]

#     for fmt in formats:
#         try:
#             return datetime.strptime(texte, fmt).date()
#         except ValueError:
#             continue

#     return None


# def convertir_statut(valeur):
#     statut = normaliser(valeur)

#     if statut in ("present", "p"):
#         return "P"

#     if statut in ("absent", "a"):
#         return "A"

#     # Les statuts inconnus ne sont pas transformés en absence.
#     return ""


# def creer_rapport(pointages):
#     employes = {}
#     mois_trouves = set()
#     erreurs = []

#     for numero, ligne in enumerate(pointages, start=1):
#         code = obtenir(ligne, "Code employé", "emp_code", "Code")
#         prenom = obtenir(ligne, "Prénom", "first_name")
#         nom = obtenir(ligne, "last_name")
#         valeur_date = obtenir(ligne, "att_date")
#         statut = get_attendance_status(ligne)

#         if code is None or str(code).strip() == "":
#             erreurs.append(f"Ligne JSON {numero} : code employé manquant.")
#             continue

#         date_pointage = convertir_date(valeur_date)

#         if date_pointage is None:
#             erreurs.append(f"Ligne JSON {numero} : date invalide.")
#             continue

#         cle = str(code).strip()
#         periode = (date_pointage.year, date_pointage.month)
#         jour = date_pointage.day

#         mois_trouves.add(periode)

#         if cle not in employes:
#             employes[cle] = {
#                 "code": code,
#                 "prenom": prenom or "",
#                 "nom": nom or "",
#                 "jours": {}
#             }

#         emp = employes[cle]

#         # Pour les doublons, un statut connu est prioritaire
#         # sur une valeur vide. Les conflits P/A sont signalés.
#         cle_jour = (periode, jour)
#         ancien = emp["jours"].get(cle_jour)

#         if ancien in ("P", "A") and statut in ("P", "A"):
#             if ancien != statut:
#                 erreurs.append(
#                     f"Conflit de pointage : employé {cle}, "
#                     f"{date_pointage.isoformat()}."
#                 )
#             continue

#         if statut or ancien is None:
#             emp["jours"][cle_jour] = statut

#     if not mois_trouves:
#         raise HTTPException(
#             status_code=422,
#             detail="Aucune date valide n'a été trouvée dans les pointages."
#         )

#     wb = Workbook()
#     premiere = wb.active
#     wb.remove(premiere)

#     # Un onglet par mois présent dans les données.
#     for annee, mois in sorted(mois_trouves):
#         ws = wb.create_sheet(f"{MOIS_FR[mois - 1]} {annee}")

#         dernier_jour = (
#             date(annee + 1, 1, 1) - date(annee, mois, 1)
#         ).days if mois == 12 else (
#             date(annee, mois + 1, 1) - date(annee, mois, 1)
#         ).days

#         entete = (
#             ["Code employé", "Prénom", "Nom"]
#             + [f"{j:02d}" for j in range(1, dernier_jour + 1)]
#             + ["Total présents", "Total absents"]
#         )

#         ws.append(entete)
#         ws.freeze_panes = "D2"
#         ws.auto_filter.ref = (
#             f"A1:{get_column_letter(len(entete))}1"
#         )

#         for cell in ws[1]:
#             cell.fill = PatternFill("solid", fgColor=BLEU)
#             cell.font = Font(color=BLANC, bold=True)
#             cell.alignment = Alignment(horizontal="center")

#         for cle, emp in sorted(
#             employes.items(),
#             key=lambda item: str(item[1]["code"])
#         ):
#             ligne = [emp["code"], emp["prenom"], emp["nom"]]
#             presents = 0
#             absents = 0

#             for jour in range(1, dernier_jour + 1):
#                 statut = emp["jours"].get(((annee, mois), jour), "")
#                 ligne.append(statut)

#                 if statut == "P":
#                     presents += 1
#                 elif statut == "A":
#                     absents += 1

#             ligne.extend([presents, absents])
#             ws.append(ligne)

#         # Mise en forme des statuts et des week-ends.
#         for jour in range(1, dernier_jour + 1):
#             colonne = jour + 3
#             date_jour = date(annee, mois, jour)
#             weekend = date_jour.weekday() >= 5

#             for numero_ligne in range(2, ws.max_row + 1):
#                 cellule = ws.cell(numero_ligne, colonne)
#                 statut = cellule.value

#                 if weekend:
#                     cellule.fill = PatternFill("solid", fgColor=ROUGE)
#                 elif statut == "P":
#                     cellule.fill = PatternFill("solid", fgColor=VERT)
#                 elif statut == "A":
#                     cellule.fill = PatternFill("solid", fgColor=ROUGE)

#                 cellule.alignment = Alignment(horizontal="center")

#             if weekend:
#                 ws.cell(1, colonne).fill = PatternFill(
#                     "solid", fgColor=ROUGE
#                 )
#                 ws.cell(1, colonne).font = Font(
#                     bold=True, color="990000"
#                 )

#         for colonne in range(1, ws.max_column + 1):
#             lettre = get_column_letter(colonne)
#             ws.column_dimensions[lettre].width = (
#                 16 if colonne <= 3 else 12
#             )

#         ws.column_dimensions["B"].width = 22
#         ws.column_dimensions["C"].width = 22

#         if ws.max_row > 1:
#             for row in ws.iter_rows(min_row=2):
#                 for cellule in row[:3] + row[-2:]:
#                     cellule.alignment = Alignment(
#                         horizontal="center"
#                     )

#     fichier = BytesIO()
#     wb.save(fichier)
#     fichier.seek(0)

#     return fichier, len(employes), sorted(mois_trouves), erreurs
from collections import defaultdict
from datetime import date, datetime, timedelta
from io import BytesIO
import calendar
import re
import unicodedata

import httpx
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter


app = FastAPI(
    title="API de gestion du pointage",
    version="1.0.0",
    description="Génération automatique des rapports mensuels de pointage."
)


class RapportRequest(BaseModel):
    pointages: list[dict] = Field(
        ...,
        description="Liste des pointages des employés"
    )


MOIS_FR = [
    "Janvier", "Février", "Mars", "Avril",
    "Mai", "Juin", "Juillet", "Août",
    "Septembre", "Octobre", "Novembre", "Décembre"
]

BLEU = "1A73E8"
BLANC = "FFFFFF"
ROUGE = "F4CCCC"
VERT = "D9EAD3"
GRIS = "E8EAED"


def get_attendance_status(record):
    check_in = record.get("clock_in")
    check_out = record.get("clock_out")

    if check_in and check_out:
        return "P"

    return "A"


def normaliser(valeur):
    texte = str(valeur or "").strip().lower()
    texte = unicodedata.normalize("NFD", texte)
    return "".join(
        c for c in texte
        if unicodedata.category(c) != "Mn"
    )


def obtenir(ligne, *noms):
    """Recherche une colonne sans tenir compte des accents."""
    donnees = {
        normaliser(k): v
        for k, v in ligne.items()
    }

    for nom in noms:
        cle = normaliser(nom)
        if cle in donnees:
            return donnees[cle]

    return None


def convertir_date(valeur):
    if isinstance(valeur, datetime):
        return valeur.date()

    if isinstance(valeur, date):
        return valeur

    if valeur is None:
        return None

    texte = str(valeur).strip()

    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%d-%m-%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(texte, fmt).date()
        except ValueError:
            continue

    return None


def convertir_statut(valeur):
    statut = normaliser(valeur)

    if statut in ("present", "p"):
        return "P"

    if statut in ("absent", "a"):
        return "A"

    return ""


def convertir_total_hrs(valeur):
    """
    Convertit une durée HH:MM en minutes.
    Exemple : 05:42 -> 342 minutes.
    Une valeur vide ou invalide ne contribue pas au total.
    """
    if valeur is None:
        return None

    texte = str(valeur).strip()

    if not texte:
        return None

    correspondance = re.fullmatch(r"(\d+):([0-5]\d)", texte)

    if not correspondance:
        return None

    heures = int(correspondance.group(1))
    minutes = int(correspondance.group(2))

    return heures * 60 + minutes


def creer_rapport(pointages):
    employes = {}
    mois_trouves = set()
    erreurs = []

    for numero, ligne in enumerate(pointages, start=1):
        code = obtenir(
            ligne, "Code employé", "emp_code", "Code"
        )
        prenom = obtenir(ligne, "Prénom", "first_name")
        nom = obtenir(ligne, "last_name")
        valeur_date = obtenir(ligne, "att_date")
        statut = get_attendance_status(ligne)

        # Récupération du volume horaire fourni par ZKTeco.
        valeur_heures = obtenir(ligne, "total_hrs")
        total_minutes_jour = convertir_total_hrs(valeur_heures)

        if code is None or str(code).strip() == "":
            erreurs.append(
                f"Ligne JSON {numero} : code employé manquant."
            )
            continue

        date_pointage = convertir_date(valeur_date)

        if date_pointage is None:
            erreurs.append(
                f"Ligne JSON {numero} : date invalide."
            )
            continue

        cle = str(code).strip()
        periode = (date_pointage.year, date_pointage.month)
        jour = date_pointage.day

        mois_trouves.add(periode)

        if cle not in employes:
            employes[cle] = {
                "code": code,
                "prenom": prenom or "",
                "nom": nom or "",
                "jours": {},
                "total_minutes": 0,
            }

        emp = employes[cle]

        # Chaque ligne représente une journée distincte.
        if total_minutes_jour is not None:
            emp["total_minutes"] += total_minutes_jour
        elif valeur_heures not in (None, ""):
            erreurs.append(
                f"Ligne JSON {numero} : total_hrs invalide "
                f"({valeur_heures})."
            )

        # Gestion des statuts journaliers existante.
        cle_jour = (periode, jour)
        ancien = emp["jours"].get(cle_jour)

        if ancien in ("P", "A") and statut in ("P", "A"):
            if ancien != statut:
                erreurs.append(
                    f"Conflit de pointage : employé {cle}, "
                    f"{date_pointage.isoformat()}."
                )
            continue

        if statut or ancien is None:
            emp["jours"][cle_jour] = statut

    if not mois_trouves:
        raise HTTPException(
            status_code=422,
            detail="Aucune date valide n'a été trouvée dans les pointages."
        )

    wb = Workbook()
    premiere = wb.active
    wb.remove(premiere)

    for annee, mois in sorted(mois_trouves):
        ws = wb.create_sheet(f"{MOIS_FR[mois - 1]} {annee}")

        dernier_jour = calendar.monthrange(annee, mois)[1]

        entete = (
            ["Code employé", "Prénom", "Nom"]
            + [f"{j:02d}" for j in range(1, dernier_jour + 1)]
            + [
                "Total présents",
                "Total absents",
                "Volume horaire total",
            ]
        )

        ws.append(entete)
        ws.freeze_panes = "D2"
        ws.auto_filter.ref = (
            f"A1:{get_column_letter(len(entete))}1"
        )

        for cell in ws[1]:
            cell.fill = PatternFill("solid", fgColor=BLEU)
            cell.font = Font(color=BLANC, bold=True)
            cell.alignment = Alignment(horizontal="center")

        for cle, emp in sorted(
            employes.items(),
            key=lambda item: str(item[1]["code"])
        ):
            ligne = [
                emp["code"],
                emp["prenom"],
                emp["nom"],
            ]

            presents = 0
            absents = 0

            for jour in range(1, dernier_jour + 1):
                statut = emp["jours"].get(((annee, mois), jour), "")
                ligne.append(statut)

                if statut == "P":
                    presents += 1
                elif statut == "A":
                    absents += 1

            # Ajouter les totaux de présence et le volume horaire.
            # timedelta permet à Excel d'afficher plus de 24 heures.
            volume_horaire = timedelta(
                minutes=emp["total_minutes"]
            )

            ligne.extend([
                presents,
                absents,
                volume_horaire,
            ])

            ws.append(ligne)

            cellule_heures = ws.cell(
                row=ws.max_row,
                column=ws.max_column,
            )
            cellule_heures.number_format = '[h]" h "mm'
            cellule_heures.alignment = Alignment(
                horizontal="center"
            )

        # Mise en forme des statuts et des week-ends.
        for jour in range(1, dernier_jour + 1):
            colonne = jour + 3
            date_jour = date(annee, mois, jour)
            weekend = date_jour.weekday() >= 5

            for numero_ligne in range(2, ws.max_row + 1):
                cellule = ws.cell(numero_ligne, colonne)
                statut = cellule.value

                if weekend:
                    cellule.fill = PatternFill(
                        "solid", fgColor=ROUGE
                    )
                elif statut == "P":
                    cellule.fill = PatternFill(
                        "solid", fgColor=VERT
                    )
                elif statut == "A":
                    cellule.fill = PatternFill(
                        "solid", fgColor=ROUGE
                    )

                cellule.alignment = Alignment(
                    horizontal="center"
                )

            if weekend:
                ws.cell(1, colonne).fill = PatternFill(
                    "solid", fgColor=ROUGE
                )
                ws.cell(1, colonne).font = Font(
                    bold=True, color="990000"
                )

        for colonne in range(1, ws.max_column + 1):
            lettre = get_column_letter(colonne)
            ws.column_dimensions[lettre].width = (
                16 if colonne <= 3 else 12
            )

        ws.column_dimensions["B"].width = 22
        ws.column_dimensions["C"].width = 22
        ws.column_dimensions[
            get_column_letter(ws.max_column)
        ].width = 24

        if ws.max_row > 1:
            for row in ws.iter_rows(min_row=2):
                for cellule in row[:3] + row[-3:]:
                    cellule.alignment = Alignment(
                        horizontal="center"
                    )

    fichier = BytesIO()
    wb.save(fichier)
    fichier.seek(0)

    return fichier, len(employes), sorted(mois_trouves), erreurs


@app.get("/month-report")
async def month_report_page(
    request: Request,
    year: int = Query(default_factory=lambda: date.today().year),
    month: int = Query(
        default_factory=lambda: date.today().month,
        ge=1,
        le=12,
    ),
):
    if "zk_token" not in request.session:
        raise HTTPException(
            status_code=401,
            detail="Session expirée"
        )

    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    # Ces éléments doivent rester définis dans ton projet.
    employee_ids = get_employee_ids()

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(
            ATT_API_URL,
            params={
                "employees": employee_ids,
                "query": 32,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "page": 1,
                "page_size": 100000,
                "departments": -1,
                "areas": -1,
                "groups": -1,
            },
            headers={
                "Authorization": (
                    f"Token {request.session['zk_token']}"
                ),
                "X-API-Key": "1234",
            },
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="Erreur lors de la récupération des pointages",
        )

    data = response.json()
    records = data.get("data", [])

    if not records:
        raise HTTPException(
            status_code=404,
            detail="Aucun pointage trouvé pour ce mois",
        )

    fichier, nb_employes, periodes, erreurs = creer_rapport(records)

    nom_fichier = f"Pointage_{year}_{MOIS_FR[month - 1]}.xlsx"

    return StreamingResponse(
        fichier,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (
                f'attachment; filename="{nom_fichier}"'
            ),
        },
    )