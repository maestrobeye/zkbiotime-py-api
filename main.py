from fastapi import FastAPI, Request, Form, HTTPException, Header
from typing import Optional
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
    StreamingResponse
)
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from db import get_conn

import pandas as pd
import io
import os
from datetime import date
from pydantic import BaseModel
from fastapi import Query
import httpx
import requests
import os
from datetime import date, datetime, timezone
app = FastAPI(
    title="ZKBioTime RH"
)

ATT_API_URL = "http://localhost/att/api/totalTimeCardReportV2/?format=json"

# -----------------------------
# Session
# -----------------------------

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv(
        "SECRET_KEY",
        "change-this-secret"
    )
)


templates = Jinja2Templates(
    directory="templates"
)


# -----------------------------
# Utilisateur RH
# (à remplacer par table users)
# -----------------------------

USERS = {
    "rh": "1234",
    "admin": "admin"
}


def check_login(request: Request):

    if "user" not in request.session:
        return False

    return True

# -----------------------------
# LOGIN
# -----------------------------

@app.get(
    "/login",
    response_class=HTMLResponse
)
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )

ZK_LOGIN_URL = "http://localhost/api-token-auth/"


class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):

    response = requests.post(
        ZK_LOGIN_URL,
        json={
            "username": username,
            "password": password
        },
        headers={
            "Content-Type": "application/json"
        }
    )


    if response.status_code != 200:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Identifiants incorrects"
            }
        )


    data = response.json()

    # Exemple ZK:
    # {"token":"xxxx"}

    token = data.get("token")


    if not token:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Token absent"
            }
        )


    request.session["user"] = username
    request.session["zk_token"] = token


    return RedirectResponse(
        "/",
        status_code=302
    )


@app.get("/logout")
def logout(request: Request):

    request.session.clear()

    return RedirectResponse(
        "/login"
    )

# -----------------------------
# DASHBOARD
# -----------------------------

@app.get(
    "/",
    response_class=HTMLResponse
)
async def dashboard(request: Request):

    if not check_login(request):
        return RedirectResponse("/login")


    conn = get_conn()
    cur = conn.cursor()

 
    cur.execute(
        """
        SELECT COUNT(*)
        FROM personnel_employee
        """
    )

    employees = cur.fetchone()[0]


    cur.execute(
        """
        SELECT COUNT(*)
        FROM att_payloadtimecard
        WHERE att_date=CURRENT_DATE
        """
    )

    today = cur.fetchone()[0]

    cur.execute("""
            SELECT
                t.id,
                t.emp_id,
                e.emp_code,
                e.first_name,
                e.last_name,
                t.punch_time,
                t.punch_state,
                t.terminal_alias,
                t.verify_type
            FROM iclock_transaction t
            LEFT JOIN personnel_employee e
                ON e.id = t.emp_id
              WHERE DATE(t.punch_time) = CURRENT_DATE
            ORDER BY t.punch_time DESC
            LIMIT 100
        """)

    rows = cur.fetchall()

    punches = [
        {
            "id": r[0],
            "emp_id": r[1],
            "emp_code": r[2],
            "first_name": r[3],
            "last_name": r[4],
            "punch_time": r[5],
            "punch_state": r[6],
            "terminal_alias": r[7],
            "verify_type": r[8],
        }
        for r in rows
    ]


    cur.close()
    conn.close()

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            "http://localhost/iclock/api/transactions/?page_size=1000",
            # params={
            #     "employees": employee_ids,
            #     "query": 32,
            #     "start_date": start_date.isoformat(),
            #     "end_date": end_date.isoformat(),
            #     "page": page,
            #     "page_size": page_size,
            #     "departments" : -1,
            #     "areas" : -1,
            #     "groups" : -1
            # },
            headers={
                "Authorization": f"Token {request.session['zk_token']}",
                "X-API-Key": "1234",
            },
        )

    if response.status_code != 200:
        raise HTTPException(response.status_code, response.text)

    data = response.json()

    print(data)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "employees": employees,
            "today": today,
            "punches": data.get("data", [])
        }
    )

# -----------------------------
# EMPLOYEES
# -----------------------------
PAGE_SIZE = 50
@app.get(
    "/employees",
    response_class=HTMLResponse
)
def employees_page(
    request: Request,
    page: int = 1
): 

    if not check_login(request):
        return RedirectResponse("/login")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM personnel_employee")
    total = cur.fetchone()[0]

    offset = (page - 1) * PAGE_SIZE

    cur.execute(
        """
        SELECT
            e.id,
            e.emp_code,
            e.first_name,
            e.last_name,
            e.email,
            pp.position_name

        FROM personnel_employee e

        LEFT JOIN personnel_position pp
        ON pp.id=e.position_id

        ORDER BY e.last_name
        LIMIT %s OFFSET %s
        """,
        (PAGE_SIZE, offset)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    employees = []

    for r in rows:

        employees.append(
            {
                "id": r[0],
                "code": r[1],
                "first_name": r[2],
                "last_name": r[3],
                "email": r[4],
                "position": r[5]
            }
        )

    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    
    return templates.TemplateResponse(
            request=request,
            name="employees.html",
            context={
                "employees": employees,
                "page": page,
                "page_size": PAGE_SIZE,
                "total": total,
                "total_pages": total_pages,
                "has_previous": page > 1,
                "has_next": page < total_pages,
            }
        )

# -----------------------------
# DETAIL EMPLOYEE
# -----------------------------

@app.get(
    "/employee/{emp_id}",
    response_class=HTMLResponse
)
def employee_detail(
    request: Request,
    emp_id:int
):
    if not check_login(request):
        return RedirectResponse("/login")


    conn=get_conn()
    cur=conn.cursor()


    cur.execute(
        """
        SELECT
            e.emp_code,
            e.first_name,
            e.last_name,
            e.email,
            d.dept_name,
            p.position_name

        FROM personnel_employee e

        LEFT JOIN personnel_department d
        ON d.id=e.department_id

        LEFT JOIN personnel_position p
        ON p.id=e.position_id

        WHERE e.id=%s

        """,
        (emp_id,)
    )


    emp=cur.fetchone()

    cur.close()
    conn.close()

    if not emp:
        raise HTTPException(
            404,
            "Employé introuvable"
        )

    employee = {
        "code": emp[0],
        "first_name": emp[1],
        "last_name": emp[2],
        "email": emp[3],
        "department": emp[4],
    }

    print(employee)
    return templates.TemplateResponse(
        request=request,
        name="employee.html",
        context={
            "employee": employee,
        }
    )

# -----------------------------
# POINTAGES
# -----------------------------

def get_employee_ids():

    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT id
            FROM personnel_employee
            ORDER BY id
            """
        )

        rows = cur.fetchall()

        ids = [
            str(row[0])
            for row in rows
        ]

        return ",".join(ids)

    finally:
        cur.close()
        conn.close()

def get_attendance_status(clock_in: str | None = None):

    if not clock_in or clock_in in ("00:00", "00:00:00"):
        return "Absent"

    fmt = "%H:%M:%S" if len(clock_in.split(":")) == 3 else "%H:%M"

    heure_arrivee = datetime.strptime(clock_in, fmt).time()
    heure_limite = datetime.strptime("09:00", "%H:%M").time()

    return "En retard" if heure_arrivee > heure_limite else "Présent"

templates.env.globals["get_attendance_status"] = get_attendance_status

@app.get("/attendance")
async def attendance_page(
    request: Request,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(200, le=200),
):
    # Dates par défaut : année en cours
    today = date.today()

    if start_date is None:
        start_date = date(today.year, 1, 1)

    if end_date is None:
        end_date = date(today.year, 12, 31)

    employee_ids = get_employee_ids()

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            ATT_API_URL,
            params={
                "employees": employee_ids,
                "query": 32,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "page": page,
                "page_size": page_size,
                "departments" : -1,
                "areas" : -1,
                "groups" : -1
            },
            headers={
                "Authorization": f"Token {request.session['zk_token']}",
                "X-API-Key": "1234",
            },
        )

    if response.status_code != 200:
        raise HTTPException(response.status_code, response.text)

    data = response.json()

    # print(data)
    return templates.TemplateResponse(
        request=request,
        name="attendance.html",
        context={
            "request": request,
            "records": data.get("data", []),
            "count": data.get("count", 0),
            "next": data.get("next"),
            "previous": data.get("previous"),
            "page": page,
            "page_size": page_size,
            "start_date": start_date,
            "end_date": end_date,
        },
    )
# -----------------------------
# EXPORT EXCEL
# -----------------------------

@app.get(
    "/attendance/export"
)
def export_excel(
    request:Request
):

    if not check_login(request):
        return RedirectResponse("/login")

    conn=get_conn()

    df=pd.read_sql(
        """
        SELECT
            e.emp_code,
            e.first_name,
            e.last_name,
            a.att_date,
            a.clock_in,
            a.clock_out

        FROM att_payloadtimecard a

        JOIN personnel_employee e
        ON e.id=a.emp_id
        """,
        conn
    )

    conn.close()

    output=io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Pointages"
        )

    output.seek(0)

    return StreamingResponse(
        output,
        media_type=
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition":
            "attachment; filename=pointages.xlsx"
        }
    )

def to_utc(dt):
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).isoformat()

def format_time(dt):
    if dt is None:
        return None

    utc_time = dt.astimezone(timezone.utc)
    return utc_time.strftime("%H:%M:%S")