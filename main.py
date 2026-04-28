from fastapi import FastAPI, Query, Header, HTTPException
from typing import Optional
from datetime import datetime
from db import get_conn
from dotenv import load_dotenv
import os
from datetime import datetime, date, timezone, timedelta
import math
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pandas as pd
import io
import httpx
from pydantic import BaseModel
import requests

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")


app = FastAPI(title="API Pointage ZKBioTime")

ATT_API_URL = "http://localhost/att/api/totalTimeCardReportV2/?format=json"

# ----------------- CORS -----------------
origins = [
    "http://localhost:3001",  # Frontend en développement
    "http://10.14.209.68:3001", # Frontend en production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def check_token(token: str):
    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

#auth login route
class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/auth/login")
def login(user: LoginRequest):
    headers = {
        "Content-Type": "application/json",
    }

    url = "http://localhost/api-token-auth"

    response = requests.post(
        url,
        json=user.dict(),
        headers=headers
    )
    print("Status:", response.status_code)
    print("Content:", response.text)

    return {
        "status": response.status_code,
        "raw": response.text
    }
    return response.json()

# 🔐 Sécurité simple par token
@app.get("/punches")
def get_punches(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    emp_id: Optional[int] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    x_api_key: str = Header(...)
):
    check_token(x_api_key)

    query = """
        SELECT
            t.id,
            t.emp_id,
            e.emp_code,
            e.first_name,
            e.last_name,
            t.punch_time,
            t.punch_state,
            t.terminal_id
        FROM iclock_transaction t
        LEFT JOIN personnel_employee e ON e.id = t.emp_id
        WHERE 1=1
    """

    params = []

    if emp_id:
        query += " AND t.emp_id = %s"
        params.append(emp_id)

    if start:
        query += " AND t.punch_time >= %s"
        params.append(start)

    if end:
        query += " AND t.punch_time <= %s"
        params.append(end)

    query += " ORDER BY t.punch_time DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "id": r[0],
            "emp_id": r[1],
            "emp_code": r[2],
            "first_name": r[3],
            "last_name": r[4],
            # "punch_time": r[5],
            "punch_time": to_utc(r[5]),
            "punch_state": r[6],
            "terminal_id": r[7]
        }
        for r in rows
    ]

@app.get("/attendance/daily",
         summary="Récupère les pointages journaliers",
         description="""
            Récupère les pointages des employés avec :
            - heure d'arrivée
            - heure de départ
            - présence
            - plein pointage
            - filtrage par date ou par employé
            - pagination
    """)
def daily_attendance(
    start: Optional[date] = None,
    end: Optional[date] = None,
    emp_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    x_api_key: str = Header(...),
):
    check_token(x_api_key)

    page_size = 100
    offset = (page - 1) * page_size

    # ---- Requête pour le total de résultats ----
    count_query = "SELECT COUNT(*) FROM att_payloadtimecard t WHERE 1=1"
    count_params = []

    if emp_id:
        count_query += " AND t.emp_id = %s"
        count_params.append(emp_id)
    if start:
        count_query += " AND t.att_date >= %s"
        count_params.append(start)
    if end:
        count_query += " AND t.att_date <= %s"
        count_params.append(end)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(count_query, count_params)
    total_results = cur.fetchone()[0]
    total_pages = math.ceil(total_results / page_size)

    # ---- Requête pour les données ----
    query = """
        SELECT
            t.emp_id,
            e.emp_code,
            e.first_name,
            e.last_name,
            t.att_date AS date,
            COALESCE(t.clock_in, t.check_in) AS arrival,
            COALESCE(t.clock_out, t.check_out) AS departure,
            t.present,
            t.full_attendance
        FROM att_payloadtimecard t
        JOIN personnel_employee e ON e.id = t.emp_id
        WHERE 1=1
    """
    params = []

    if emp_id:
        query += " AND t.emp_id = %s"
        params.append(emp_id)
    if start:
        query += " AND t.att_date >= %s"
        params.append(start)
    if end:
        query += " AND t.att_date <= %s"
        params.append(end)

    query += " ORDER BY t.att_date DESC, t.emp_id ASC"
    query += " LIMIT %s OFFSET %s"
    params.extend([page_size, offset])

    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    data = [
        {
            "emp_id": r[0],
            "emp_code": r[1],
            "first_name": r[2],
            "last_name": r[3],
            "date": r[4].strftime("%Y-%m-%d") if hasattr(r[4], "strftime") else r[4],
            "arrival": to_utc(r[5]),
            "departure": to_utc(r[6]),
            "present": r[7],
            "full_attendance": r[8]
        }
        for r in rows
    ]

    return {
        "page": page,
        "page_size": page_size,
        "total_results": total_results,
        "total_pages": total_pages,
        "data": data
    }

@app.get("/attendance/daily/hours", summary="Pointages journaliers avec heures")
def daily_attendance_hours(
    start: Optional[date] = None,
    end: Optional[date] = None,
    emp_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    x_api_key: str = Header(...)
):
    check_token(x_api_key)

    page_size = 100
    offset = (page - 1) * page_size

    conn = get_conn()
    cur = conn.cursor()

    # ---- Total pour pagination ----
    count_query = "SELECT COUNT(*) FROM att_payloadtimecard t WHERE 1=1"
    count_params = []
    if emp_id:
        count_query += " AND t.emp_id = %s"
        count_params.append(emp_id)
    if start:
        count_query += " AND t.att_date >= %s"
        count_params.append(start)
    if end:
        count_query += " AND t.att_date <= %s"
        count_params.append(end)
    cur.execute(count_query, count_params)
    total_results = cur.fetchone()[0]
    total_pages = math.ceil(total_results / page_size)

    # ---- Récupération des données ----
    query = """
        SELECT
            t.emp_id,
            e.emp_code,
            e.first_name,
            e.last_name,
            t.att_date AS date,
            COALESCE(t.clock_in, t.check_in) AS arrival,
            COALESCE(t.clock_out, t.check_out) AS departure,
            t.present,
            t.full_attendance
        FROM att_payloadtimecard t
        JOIN personnel_employee e ON e.id = t.emp_id
        WHERE 1=1
    """
    params = []
    if emp_id:
        query += " AND t.emp_id = %s"
        params.append(emp_id)
    if start:
        query += " AND t.att_date >= %s"
        params.append(start)
    if end:
        query += " AND t.att_date <= %s"
        params.append(end)

    query += " ORDER BY t.att_date DESC, t.emp_id ASC LIMIT %s OFFSET %s"
    params.extend([page_size, offset])

    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    data = []
    for r in rows:
        arrival = r[5]
        departure = r[6]
        total_hours = calculate_total_hours(arrival, departure)

        data.append({
            "emp_id": r[0],
            "emp_code": r[1],
            "first_name": r[2],
            "last_name": r[3],
            "date": r[4].strftime("%Y-%m-%d") if hasattr(r[4], "strftime") else r[4],
            "arrival": arrival.strftime("%H:%M:%S") if arrival else None,
            "departure": departure.strftime("%H:%M:%S") if departure else None,
            "total_hours": total_hours,
            "present": r[7],
            "full_attendance": r[8]
        })

    return {
        "page": page,
        "page_size": page_size,
        "total_results": total_results,
        "total_pages": total_pages,
        "data": data
    }

@app.get("/attendance/daily/export", summary="Exporter les pointages en Excel")
def export_daily_attendance(
    start: Optional[date] = None,
    end: Optional[date] = None,
    emp_id: Optional[int] = None,
    x_api_key: str = Header(...)
):
    check_token(x_api_key)

    # --- Récupération des données depuis la DB ---
    conn = get_conn()
    cur = conn.cursor()

    query = """
        SELECT
            t.emp_id,
            e.emp_code,
            e.first_name,
            e.last_name,
            t.att_date AS date,
            COALESCE(t.clock_in, t.check_in) AS arrival,
            COALESCE(t.clock_out, t.check_out) AS departure,
            t.present,
            t.full_attendance
        FROM att_payloadtimecard t
        JOIN personnel_employee e ON e.id = t.emp_id
        WHERE 1=1
    """
    params = []
    if emp_id:
        query += " AND t.emp_id = %s"
        params.append(emp_id)
    if start:
        query += " AND t.att_date >= %s"
        params.append(start)
    if end:
        query += " AND t.att_date <= %s"
        params.append(end)

    query += " ORDER BY t.att_date DESC, t.emp_id ASC"
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # --- Transformation en DataFrame pandas ---
    df = pd.DataFrame(rows, columns=[
        "emp_id", "emp_code", "first_name", "last_name",
        "date", "arrival", "departure", "present", "full_attendance"
    ])
    # Convertir les dates et heures en string lisible
    df["date"] = df["date"].apply(lambda x: x.strftime("%Y-%m-%d") if x else "")
    df["arrival"] = df["arrival"].apply(lambda x: x.strftime("%H:%M:%S") if x else "")
    df["departure"] = df["departure"].apply(lambda x: x.strftime("%H:%M:%S") if x else "")

    # --- Création du fichier Excel en mémoire ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Attendance")
    output.seek(0)

    # --- Retourner le fichier Excel ---
    headers = {
        'Content-Disposition': 'attachment; filename="attendance.xlsx"'
    }
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)

@app.get("/employees",
         summary="Récupère la liste de tous les employés",
         description="""
            Récupère la liste des employés avec :
            - code employé
            - prénom
            - nom
            - Poste
            - pagination
         """)
def get_employees(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    x_api_key: str = Header(...)
):
    # Vérification du token
    check_token(x_api_key)

    offset = (page - 1) * page_size

    # Connexion à la base
    conn = get_conn()
    cur = conn.cursor()

    # ---- Total des résultats pour pagination ----
    cur.execute("SELECT COUNT(*) FROM personnel_employee")
    total_results = cur.fetchone()[0]
    total_pages = math.ceil(total_results / page_size)

    # ---- Récupération des données ----
    query = """
        SELECT
            e.id,  -- employee id
            e.emp_code,
            e.first_name,
            e.last_name,
            e.email,
            pp.position_name
        FROM personnel_employee e
        JOIN personnel_position pp ON pp.id = e.position_id
        ORDER BY e.last_name ASC, e.first_name ASC
        LIMIT %s OFFSET %s;

    """
    cur.execute(query, (page_size, offset))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    data = [
        {
            "emp_id": r[0],
            "emp_code": r[1],
            "first_name": r[2],
            "last_name": r[3],
            "email": r[4],
            "position": r[5]
        }
        for r in rows
    ]

    return {
        "page": page,
        "page_size": page_size,
        "total_results": total_results,
        "total_pages": total_pages,
        "data": data
    }

# @app.get("/employee/{emp_id}",
#          summary="Récupère les informations d'un employé",
#          description="""
#             Récupère les informations détaillées d'un employé avec :
#             - code employé
#             - prénom
#             - nom
#             - date de création
#             - département
#             - etc.
#          """)
# def get_employee(emp_id: int, x_api_key: str = Header(...)):
#     # Vérification du token
#     check_token(x_api_key)

#     # Requête SQL
#     query = """
#         SELECT
#             e.id,
#             e.emp_code,
#             e.first_name,
#             e.last_name,
#             e.hire_date,
#             d.dept_name,
#             pp.position_name,
#             e.email
#         FROM personnel_employee e
#         JOIN personnel_department d ON d.id = e.department_id
#         JOIN personnel_position pp ON pp.id = e.position_id
#         WHERE e.id = %s
#     """

#     conn = get_conn()
#     cur = conn.cursor()
#     cur.execute(query, (emp_id,))
#     row = cur.fetchone()
#     cur.close()
#     conn.close()
#     print(emp_id)
#     if not row:
#         raise HTTPException(status_code=404, detail="Employee not found")

#     return {
#         "emp_id": row[0],
#         "emp_code": row[1],
#         "first_name": row[2],
#         "last_name": row[3],
#         "hire_date": row[4].strftime("%Y-%m-%d") if row[4] else None,
#         "department": row[5],
#         "position": row[6],
#         "email": row[7]
#     }
@app.get("/employee/{emp_id}",
         summary="Récupère les informations d'un employé avec ses pointages")
def get_employee(emp_id: int, x_api_key: str = Header(...)):
    check_token(x_api_key)

    conn = get_conn()
    cur = conn.cursor()

    # ---------------------------
    # 👤 Infos employé
    # ---------------------------
    query_employee = """
        SELECT
            e.id,
            e.emp_code,
            e.first_name,
            e.last_name,
            e.hire_date,
            d.dept_name,
            pp.position_name,
            e.email
        FROM personnel_employee e
        LEFT JOIN personnel_department d ON d.id = e.department_id
        LEFT JOIN personnel_position pp ON pp.id = e.position_id
        WHERE e.id = %s
    """

    cur.execute(query_employee, (emp_id,))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Employee not found")

    # ---------------------------
    # ⏱ Pointages (att_payloadtimecard)
    # ---------------------------
    query_attendance = """
        SELECT
            t.att_date,
            COALESCE(t.clock_in, t.check_in) AS arrival,
            COALESCE(t.clock_out, t.check_out) AS departure,
            t.present,
            t.full_attendance
        FROM att_payloadtimecard t
        WHERE t.emp_id = %s
        ORDER BY t.att_date DESC
        LIMIT 30
    """

    cur.execute(query_attendance, (emp_id,))
    rows = cur.fetchall()

    cur.close()
    conn.close()

    # ---------------------------
    # 📊 Formatage pointages
    # ---------------------------
    attendance = [
        {
            "date": r[0].strftime("%Y-%m-%d") if r[0] else None,
            "arrival": r[1].strftime("%H:%M:%S") if r[1] else None,
            "departure": r[2].strftime("%H:%M:%S") if r[2] else None,
            "present": r[3],
            "full_attendance": r[4],
            # "worked_hours": float(r[5]) if r[5] else 0,
            # "overtime": float(r[6]) if r[6] else 0
        }
        for r in rows
    ]

    # ---------------------------
    # 📦 Réponse finale
    # ---------------------------
    return {
        "emp_id": row[0],
        "emp_code": row[1],
        "first_name": row[2],
        "last_name": row[3],
        "hire_date": row[4].strftime("%Y-%m-%d") if row[4] else None,
        "department": row[5] if row[5] else "Non défini",
        "position": row[6] if row[6] else "Non défini",
        "email": row[7],
        "attendance": attendance
    }

@app.get(
    "/attendance/total-timecard",
    summary="Proxy ZKBioTime - Total TimeCard avec paramètres"
)
async def get_total_timecard_report(
    # Filtres ZK
    areas: int = Query(-1),
    departments: int = Query(-1),
    employees: Optional[str] = Query(None, description="IDs séparés par des virgules"),
    groups: int = Query(-1),
    start_date: date = Query(...),
    end_date: date = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=200),

    # Sécurité
    authorization: str = Header(...),
    x_api_key: str = Header(...)
):
    check_token(x_api_key)

    params = {
        "areas": areas,
        "departments": departments,
        "groups": groups,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "page": page,
        "page_size": page_size,
        "format": "json"  # IMPORTANT
    }

    if employees:
        params["employees"] = employees

    headers = {
        "Content-Type": "application/json",
        "Authorization": authorization
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            ATT_API_URL,
            headers=headers,
            params=params
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )

    return response.json()

@app.get(
    "/attendance/total-timecard/export",
    summary="Export Excel - Total TimeCard (ZKBioTime)"
)
async def export_total_timecard_excel(
    # Filtres ZK
    areas: int = Query(-1),
    departments: int = Query(-1),
    employees: Optional[str] = Query(None),
    groups: int = Query(-1),
    start_date: date = Query(...),
    end_date: date = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, le=5000),  # plus grand pour export

    # 🔐 Sécurité
    authorization: str = Header(...),
    x_api_key: str = Header(...)
):
    check_token(x_api_key)

    params = {
        "areas": areas,
        "departments": departments,
        "groups": groups,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "page": page,
        "page_size": page_size,
        "format": "json"
    }

    if employees:
        params["employees"] = employees

    headers = {
        "Content-Type": "application/json",
        "Authorization": authorization
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(
            ATT_API_URL,
            headers=headers,
            params=params
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )

    zk_data = response.json()

    # ZK renvoie souvent { "data": [...], "count": ... }
    rows = zk_data.get("data", [])

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="Aucune donnée à exporter"
        )
    
    columns_to_keep = [
        "emp_code",
        "first_name",
        "last_name",
        "att_date",
        "clock_in",
        "clock_out",
        "worked_hrs",
        "total_ot",
        "full_attendance"
    ]
    df = pd.DataFrame(rows)
    # 📊 Conversion en DataFrame
    #df = pd.DataFrame(rows)
    df = df[[col for col in columns_to_keep if col in df.columns]]
    df.rename(columns={
        "emp_code": "Code Employé",
        "first_name": "Prénom",
        "last_name": "Nom",
        "att_date": "Date",
        "clock_in": "Heure arrivée",
        "clock_out": "Heure départ",
        "worked_hrs": "Heures travaillées",
        "total_ot": "Heures supplémentaires",
        "full_attendance": "Présence complète"
    }, inplace=True)

    print(df.columns)
    # ✨ (Optionnel) renommage colonnes lisibles
    # df.rename(columns={
    #     "emp_code": "Code Employé",
    #     "first_name": "Prénom",
    #     "last_name": "Nom",
    #     "att_date": "Date",
    #     "clock_in": "Arrivée",
    #     "clock_out": "Départ",
    #     "work_time": "Temps travaillé",
    #     "work_day": "Jour travaillé"
    # }, inplace=True)

    # 📁 Génération Excel en mémoire
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="TimeCard")

    output.seek(0)

    filename = f"timecard_{start_date}_{end_date}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

@app.get(
    "/presences",
    summary="Liste des présences",
    description="""
    Liste des présences journalières avec pagination.
    Filtres optionnels par date de début et date de fin.
    """
)
def list_presences(
    page: int = Query(1, ge=1),
    date_debut: Optional[str] = Query(None, example="2025-12-01"),
    date_fin: Optional[str] = Query(None, example="2025-12-31"),
    x_api_key: str = Header(...)
):
    check_token(x_api_key)

    limit = 150
    offset = (page - 1) * limit

    filters = []
    params = []

    if date_debut:
        filters.append("att_date >= %s")
        params.append(date_debut)

    if date_fin:
        filters.append("att_date <= %s")
        params.append(date_fin)

    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    query = f"""
        SELECT
            a.id,
            a.att_date,
            a.emp_id,
            e.emp_code,
            e.first_name,
            e.last_name,
            a.check_in,
            a.check_out,
            a.work_day,
            a.present,
            a.full_attendance
        FROM att_payloadtimecard a
        JOIN personnel_employee e ON e.id = a.emp_id
        {where_clause}
        ORDER BY a.att_date DESC, e.last_name
        LIMIT {limit} OFFSET {offset}
    """

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    data = []
    for row in rows:
        data.append({
            "id": row[0],
            "date": row[1].strftime("%Y-%m-%d"),
            "emp_id": row[2],
            "emp_code": row[3],
            "first_name": row[4],
            "last_name": row[5],
            "check_in": row[6].isoformat() if row[6] else None,
            "check_out": row[7].isoformat() if row[7] else None,
            "work_day": float(row[8]),
            "present": bool(row[9]),
            "full_attendance": bool(row[10]),
        })

    return {
        "page": page,
        "limit": limit,
        "count": len(data),
        "filters": {
            "date_debut": date_debut,
            "date_fin": date_fin
        },
        "data": data
    }

def to_utc(dt):
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).isoformat()


def calculate_total_hours(arrival, departure):
    if arrival is None or departure is None:
        return None
    if departure < arrival:
        # Shift de nuit : ajouter 1 jour au départ
        departure += timedelta(days=1)
    delta = departure - arrival
    return round(delta.total_seconds() / 3600, 2)  # heures décimales