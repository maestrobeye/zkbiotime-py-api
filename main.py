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
from pydantic import BaseModel,EmailStr
from fastapi import Query
import httpx
import requests
import os
from datetime import date, datetime, timezone

from io import BytesIO

from typing import Annotated

import asyncio
import httpx

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

class EmployeeCreate(BaseModel):
    emp_code: str
    department: int
    area: list[int]

    hire_date: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    mobile: Optional[str] = None
    national: Optional[str] = None
    address: Optional[str] = None
    email: Optional[EmailStr] = None
    app_status: Optional[int] = None


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

async def get_next_position_code(client, headers):

    response = await client.get(
        "http://localhost/personnel/api/positions/",
        headers=headers,
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )

    data = response.json()

    # Selon la structure de ton API
    positions = data.get("data", data)

    codes = []

    for position in positions:
        try:
            code = int(position.get("position_code"))
            codes.append(code)
        except (TypeError, ValueError):
            pass

    next_code = max(codes, default=0) + 1

    return str(next_code)

@app.post("/employees/create")

async def create_employee(
    request: Request,
    emp_code: Annotated[str, Form()],
    area: Annotated[list[int], Form()],
    card_no: Annotated[int, Form()],
    position: Annotated[str, Form()],
    first_name: Annotated[str | None, Form()] = None,
    last_name: Annotated[str | None, Form()] = None,
    mobile: Annotated[str | None, Form()] = None,
    email: Annotated[str | None, Form()] = None,
):
    url = f"http://localhost/personnel/api/employees/"

    # Supprimer les champs None
    payload = {
        "emp_code": emp_code,
        "department": 1,
        "area": area,
        "card_no": card_no,
        "position": position,
        "mobile": mobile
    }
    
    if first_name:
        payload["first_name"] = first_name

    if last_name:
        payload["last_name"] = last_name

    if mobile:
        payload["mobile"] = mobile

    if email:
        payload["email"] = email

    token = request.session["zk_token"]

    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
        "X-API-Key": "1234",
    }

    async with httpx.AsyncClient(timeout=30) as client:

        # ==========================================
        # 1. Créer la position
        # ==========================================

         # Récupérer le prochain position_code
        position_code = await get_next_position_code(
            client,
            headers
        )

        # Créer la position
        payload_position = {
            "position_code": position_code,
            "position_name": position,
        }

        position_response = await client.post(
            "http://localhost/personnel/api/positions/",
            json=payload_position,
            headers=headers,
        )

        if position_response.status_code not in (200, 201):
            raise HTTPException(
                status_code=position_response.status_code,
                detail=(
                    "Erreur lors de la création de la position : "
                    + position_response.text
                ),
            )

        position_data = position_response.json()
        # ==========================================
        # 2. Créer l'employé
        # ==========================================

        payload = {
            "emp_code": emp_code,
            "department": 1,
            "area": area,
            "card_no": card_no,
            "position": position_data["position_code"],
        }

        if first_name:
            payload["first_name"] = first_name

        if last_name:
            payload["last_name"] = last_name

        if mobile:
            payload["mobile"] = mobile

        if email:
            payload["email"] = email

        employee_response = await client.post(
            "http://localhost/personnel/api/employees/",
            json=payload,
            headers=headers,
        )

        if employee_response.status_code not in (200, 201):
            raise HTTPException(
                status_code=employee_response.status_code,
                detail=(
                    "Erreur lors de la création de l'employé : "
                    + employee_response.text
                ),
            )
        
    if employee_response.status_code not in (200, 201):
        raise HTTPException(
            status_code=employee_response.status_code,
            detail=employee_response.text,
        )

    return RedirectResponse(
        url="/employees",
        status_code=303
    )

@app.get("/employees/create")
async def get_form(request: Request):
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            "http://localhost/personnel/api/areas/",
            headers={
                "Authorization": f"Token {request.session['zk_token']}",
                "X-API-Key": "1234",
            },
        )

    if response.status_code != 200:
        raise HTTPException(response.status_code, response.text)

    data = response.json()

    areas = data.get("data", [])
   
    return templates.TemplateResponse(
        request=request,
        name="employeeForm.html",
        context={
            "areas": areas
        }
    )

@app.get("/employees/edit/{employee_id}")
async def edit_employee_page(
    request: Request,
    employee_id: int,
):
    headers = {
        "Authorization": f"Token {request.session['zk_token']}",
        "Content-Type": "application/json",
        "X-API-Key": "1234",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        employee_response, area_response = await asyncio.gather(
            client.get(
                f"http://localhost/personnel/api/employees/{employee_id}/",
                headers=headers,
            ),
            client.get(
                "http://localhost/personnel/api/areas/",
                headers=headers,
            ),
        )

    employee = employee_response.json()

   # Vérification employee
    if employee_response.status_code != 200:
        raise HTTPException(
            status_code=employee_response.status_code,
            detail=employee_response.text,
        )

    # Vérification areas
    if area_response.status_code != 200:
        raise HTTPException(
            status_code=area_response.status_code,
            detail=area_response.text,
        )

    employee = employee_response.json()
    area = area_response.json()

    employee_area_ids = [a["id"] for a in employee.get("area", [])]

    return templates.TemplateResponse(
        request=request,
        name="employee_edit.html",
        context={
            "request": request,
            "employee": employee,
            "area": area,
            "employee_area_ids": employee_area_ids,
        },
    )

# @app.post("/employees/edit/{employee_id}")
# async def update_employee(
#     request: Request,
#     employee_id: int,

#     emp_code: Annotated[str, Form()],
#     area: Annotated[list[int], Form()],
#     card_no: Annotated[int, Form()],
#     position: Annotated[str, Form()],

#     first_name: Annotated[str | None, Form()] = None,
#     last_name: Annotated[str | None, Form()] = None,
#     mobile: Annotated[str | None, Form()] = None,
#     email: Annotated[str | None, Form()] = None,
# ):
#     token = request.session["zk_token"]

#     headers = {
#         "Authorization": f"Token {token}",
#         "Content-Type": "application/json",
#         "X-API-Key": "1234",
#     }

#     payload = {
#         "emp_code": emp_code,
#         "department": 1,
#         "area": area,
#         "card_no": card_no,
#         "position": position,
#         "first_name": first_name,
#         "last_name": last_name,
#         "mobile": mobile,
#         "email": email,
#     }

#     async with httpx.AsyncClient(timeout=30) as client:

#         response = await client.put(
#             f"http://localhost/personnel/api/employees/{employee_id}/",
#             json=payload,
#             headers=headers,
#         )

#     if response.status_code not in (200, 201):
#         raise HTTPException(
#             status_code=response.status_code,
#             detail=response.text,
#         )

#     return RedirectResponse(
#         url="/employees",
#         status_code=303,
#     )

@app.post("/employees/edit/{employee_id}")
async def update_employee(
    request: Request,
    employee_id: int,

    emp_code: Annotated[str, Form()],
    area: Annotated[list[int], Form()] = [],
    card_no: Annotated[int | None, Form()] = None,
    position: Annotated[str, Form()] = "",
    first_name: Annotated[str | None, Form()] = None,
    last_name: Annotated[str | None, Form()] = None,
    mobile: Annotated[str | None, Form()] = None,
    email: Annotated[str | None, Form()] = None,
):
    token = request.session["zk_token"]

    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
        "X-API-Key": "1234",
    }

    employee_url = (
        f"http://localhost/personnel/api/employees/{employee_id}/"
    )

    async with httpx.AsyncClient(timeout=30) as client:

        # ==========================================
        # 1. Récupérer l'employé actuel
        # ==========================================

        employee_response = await client.get(
            employee_url,
            headers=headers,
        )

        if employee_response.status_code != 200:
            raise HTTPException(
                status_code=employee_response.status_code,
                detail=(
                    "Erreur lors de la récupération de l'employé : "
                    + employee_response.text
                ),
            )

        employee = employee_response.json()

        # ==========================================
        # 2. Gérer la position
        # ==========================================

        current_position = employee.get("position")

        position_code = None

        if current_position:
            current_position_name = current_position.get("position_name")
            current_position_code = current_position.get("position_code")

            # La position n'a pas changé
            if position == current_position_name:
                position_code = current_position_code

        # ==========================================
        # 3. Si la position a changé
        # ==========================================

        if position_code is None:

            # Récupérer le prochain position_code
            position_code = await get_next_position_code(
                client,
                headers
            )

            # Créer la nouvelle position
            payload_position = {
                "position_code": position_code,
                "position_name": position,
            }

            position_response = await client.post(
                "http://localhost/personnel/api/positions/",
                json=payload_position,
                headers=headers,
            )

            if position_response.status_code not in (200, 201):
                raise HTTPException(
                    status_code=position_response.status_code,
                    detail=(
                        "Erreur lors de la création de la position : "
                        + position_response.text
                    ),
                )

            # Utiliser le code retourné par l'API
            position_data = position_response.json()

            position_code = position_data["position_code"]

        # ==========================================
        # 4. Préparer le payload employé
        # ==========================================

        payload = {
            "emp_code": emp_code,
            "department": 1,
            "area": area,
            "card_no": card_no,
            "position": position_code,
        }

        if first_name:
            payload["first_name"] = first_name

        if last_name:
            payload["last_name"] = last_name

        if mobile:
            payload["mobile"] = mobile

        if email:
            payload["email"] = email

        # ==========================================
        # 5. Mise à jour de l'employé
        # ==========================================

        update_response = await client.put(
            employee_url,
            json=payload,
            headers=headers,
        )

        if update_response.status_code not in (200, 201):
            raise HTTPException(
                status_code=update_response.status_code,
                detail=(
                    "Erreur lors de la mise à jour de l'employé : "
                    + update_response.text
                ),
            )

    # ==========================================
    # 6. Retour vers la liste
    # ==========================================

    return RedirectResponse(
        url="/employees",
        status_code=303,
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
        "emp_id": emp_id
    }

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

@app.post("/employees/sync")
async def sync_employees(request: Request):

    token = request.session["zk_token"]

    employee_ids = get_employee_ids()

    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
        "X-API-Key": "1234",
    }

    employees = [
        int(x)
        for x in employee_ids.split(",")
        if x.strip()
    ]
    payload = {
        "employees": employees
    }

    async with httpx.AsyncClient(timeout=120) as client:

        response = await client.post(
            "http://localhost/personnel/api/employees/resync_to_device/",
            json=payload,
            headers=headers,
        )

    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )
    print(response.json())
    return RedirectResponse(
        url="/employees",
        status_code=303
    )

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

# @app.get(
#     "/attendance/export"
# )
# async def export_excel(
#     request:Request
# ):

#     if not check_login(request):
#         return RedirectResponse("/login")

#     conn=get_conn()

#     df= pd.read_sql(
#         """
#         SELECT
#             e.emp_code,
#             e.first_name,
#             e.last_name,
#             a.att_date,
#             a.clock_in,
#             a.clock_out

#         FROM att_payloadtimecard a

#         JOIN personnel_employee e
#         ON e.id=a.emp_id
#         """,
#         conn
#     )

#     conn.close()

#     output=io.BytesIO()

#     with pd.ExcelWriter(
#         output,
#         engine="openpyxl"
#     ) as writer:

#         df.to_excel(
#             writer,
#             index=False,
#             sheet_name="Pointages"
#         )

#     output.seek(0)

#     return StreamingResponse(
#         output,
#         media_type=
#         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#         headers={
#             "Content-Disposition":
#             "attachment; filename=pointages.xlsx"
#         }
#     )

@app.get("/attendance/export")
async def attendance_export(
    request: Request,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    print(start_date)
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
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "page_size": 300,
                "page": 1,
                "departments": -1,
                "areas": -1,
                "groups": -1,
            },
            headers={
                "Authorization": f"Token {request.session['zk_token']}",
                "X-API-Key": "1234",
            },
        )

    if response.status_code != 200:
        raise HTTPException(response.status_code, response.text)

    data = response.json()

    records = data.get("data", [])

    # Transformer en DataFrame
    df = pd.DataFrame(records)

    # Supprimer les timezones des colonnes datetime
    for col in df.select_dtypes(include=["datetimetz"]).columns:
        df[col] = df[col].dt.tz_localize(None)

    # Créer le fichier Excel en mémoire
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Attendance"
        )

    output.seek(0)

    filename = (
        f"attendance_{start_date.isoformat()}_"
        f"{end_date.isoformat()}.xlsx"
    )

    print(len(employee_ids))
    print(len(records))

    return StreamingResponse(
        output,
        media_type=(
            "application/vnd.openxmlformats-officedocument"
            ".spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
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