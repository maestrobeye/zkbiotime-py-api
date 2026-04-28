import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Employee } from '../types/employee';
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

// API-specific types
export interface ApiEmployee {
  emp_id: number;
  emp_code: string;
  first_name: string;
  last_name: string;
  email: string;
  position: string;
}

export interface PaginatedEmployeesResponse {
  page: number;
  page_size: number;
  total_results: number;
  total_pages: number;
  data: any[];
}

// App-level paginated type
export interface PaginatedEmployees {
  page: number;
  page_size: number;
  total_results: number;
  total_pages: number;
  data: any[];
}

@Injectable({
  providedIn: 'root'
})
export class DataService {
  private http: HttpClient = inject(HttpClient);
  private apiUrl = 'http://10.14.202.7:8000';

  // Mock data to be used as a fallback
  private mockEmployees: Employee[] = [
    {
      id: 1,
      name: 'Alice Dubois',
      position: 'Développeuse Frontend',
      email: 'alice.dubois@example.com',
      phone: '06 12 34 56 78',
      status: 'Active',
      timeEntries: [
        { date: '2024-07-15', clockIn: '09:05', clockOut: '17:35', totalHours: 7.5 },
        { date: '2024-07-14', clockIn: '09:00', clockOut: '17:30', totalHours: 7.5 },
        { date: '2024-06-20', clockIn: '09:15', clockOut: '18:00', totalHours: 7.75 },
      ],
    },
    {
      id: 2,
      name: 'Bob Martin',
      position: 'Chef de projet',
      email: 'bob.martin@example.com',
      phone: '06 87 65 43 21',
      status: 'Active',
      timeEntries: [
        { date: '2024-07-15', clockIn: '08:45', clockOut: '18:15', totalHours: 8.5 },
        { date: '2024-07-14', clockIn: '09:30', clockOut: '17:00', totalHours: 6.5 },
      ],
    },
    {
      id: 3,
      name: 'Charlie Dupont',
      position: 'Designer UX/UI',
      email: 'charlie.dupont@example.com',
      phone: '07 11 22 33 44',
      status: 'On Leave',
      timeEntries: [
        { date: '2024-05-10', clockIn: '10:00', clockOut: '17:00', totalHours: 6.0 },
      ],
    },
    {
      id: 4,
      name: 'Diana Moreau',
      position: 'Développeuse Backend',
      email: 'diana.moreau@example.com',
      phone: '07 55 66 77 88',
      status: 'Active',
      timeEntries: [
        { date: '2024-07-15', clockIn: '09:02', clockOut: '17:45', totalHours: 7.72 },
        { date: '2024-07-14', clockIn: '09:10', clockOut: '18:00', totalHours: 7.83 },
      ],
    },
    {
      id: 5,
      name: 'Eva Petit',
      position: 'Spécialiste Marketing',
      email: 'eva.petit@example.com',
      phone: '06 99 88 77 66',
      status: 'Terminated',
      timeEntries: [
        { date: '2024-03-01', clockIn: '09:00', clockOut: '12:00', totalHours: 3.0 },
      ],
    },
    {
      id: 6,
      name: 'Frank Lemoine',
      position: 'Ingénieur DevOps',
      email: 'frank.lemoine@example.com',
      phone: '06 10 20 30 40',
      status: 'Active',
      timeEntries: [
        { date: '2024-07-15', clockIn: '09:25', clockOut: '18:05', totalHours: 7.67 },
        { date: '2024-07-14', clockIn: '08:55', clockOut: '17:30', totalHours: 7.58 },
      ],
    },
    {
      id: 7,
      name: 'Grace Hopper',
      position: 'Computer Scientist',
      email: 'grace.hopper@example.com',
      phone: '06 11 22 33 44',
      status: 'Active',
      timeEntries: [
        { date: '2024-07-15', clockIn: '09:00', clockOut: '17:00', totalHours: 8.0 },
      ],
    },
    {
      id: 8,
      name: 'Hedy Lamarr',
      position: 'Inventor',
      email: 'hedy.lamarr@example.com',
      phone: '06 55 66 77 88',
      status: 'Active',
      timeEntries: [
        { date: '2024-07-15', clockIn: '10:00', clockOut: '18:00', totalHours: 7.0 },
      ],
    },
    {
      id: 9,
      name: 'Isaac Newton',
      position: 'Physicist',
      email: 'isaac.newton@example.com',
      phone: '06 99 88 77 66',
      status: 'On Leave',
      timeEntries: [],
    },
    {
      id: 10,
      name: 'Jocelyn Bell Burnell',
      position: 'Astrophysicist',
      email: 'jocelyn.bell@example.com',
      phone: '07 12 34 56 78',
      status: 'Active',
      timeEntries: [
        { date: '2024-07-15', clockIn: '09:30', clockOut: '17:30', totalHours: 7.0 },
      ],
    },
    {
      id: 11,
      name: 'Katherine Johnson',
      position: 'Mathematician',
      email: 'katherine.johnson@example.com',
      phone: '06 23 45 67 89',
      status: 'Terminated',
      timeEntries: [],
    },
    {
      id: 12,
      name: 'Leonardo da Vinci',
      position: 'Polymath',
      email: 'leo.davinci@example.com',
      phone: '07 87 65 43 21',
      status: 'Active',
      timeEntries: [
        { date: '2024-07-15', clockIn: '08:00', clockOut: '16:00', totalHours: 7.0 },
      ],
    },
  ];

  private mapApiEmployeeToEmployee(apiEmp: ApiEmployee): Employee {
    return {
      id: apiEmp.emp_id,
      name: `${apiEmp.first_name} ${apiEmp.last_name}`,
      email: apiEmp.email,
      position: apiEmp.position || 'Non spécifié',
      phone: 'N/A',
      status: 'Active',
      timeEntries: []
    };
  }

  // Used by components that need just a list, not pagination (dashboard, stats).
  // This fetches the first page to avoid breaking them.
  getEmployees(): Observable<any[]> {
    return this.http.get<PaginatedEmployeesResponse>(`${this.apiUrl}/employees`).pipe(
      map((response: PaginatedEmployeesResponse) => response.data.map(this.mapApiEmployeeToEmployee.bind(this))),
      catchError((error): Observable<Employee[]> => {
        console.error('Error fetching employees, returning mock data:', error);
        return of(this.mockEmployees); // Return mock data on error
      })
    );
  }

  getEmployeesPaginated(page: number = 1): Observable<PaginatedEmployees> {
    return this.http.get<PaginatedEmployeesResponse>(`${this.apiUrl}/employees?page=${page}`).pipe(
      map((response: PaginatedEmployeesResponse) => ({
        ...response,
        data: response.data.map(this.mapApiEmployeeToEmployee.bind(this)) // Ensure the map converts ApiEmployee to Employee
      })),
      catchError((error): Observable<PaginatedEmployees> => {
        console.error(`Error fetching paginated employees page ${page}, returning mock data:`, error);

        const pageSize = 10;
        const totalPages = Math.ceil(this.mockEmployees.length / pageSize);
        const paginatedMock: Employee[] = this.mockEmployees.slice((page - 1) * pageSize, page * pageSize);

        // Create the paginated mock data matching the PaginatedEmployees structure
        const paginatedData: PaginatedEmployees = {
          page: page,
          page_size: pageSize,
          total_results: this.mockEmployees.length,
          total_pages: totalPages,
          data: paginatedMock // This is now explicitly typed as Employee[]
        };

        return of(paginatedData);
      })
    );
  }

  getEmployeeById(id: number): Observable<Employee | undefined> {
    return this.http.get<ApiEmployee>(`${this.apiUrl}/employees/${id}`).pipe(
      map((apiEmp: ApiEmployee) => this.mapApiEmployeeToEmployee(apiEmp)),
      catchError((error): Observable<Employee | undefined> => {
        console.error(`Error fetching employee with id=${id}, returning mock data:`, error);
        const employee = this.mockEmployees.find(e => e.id === id);
        return of(employee); // Return mock employee on error
      })
    );
  }

  getPresences(
    employeeIds: number[],
    startDate: string,
    endDate: string,
    query: string = ''): Observable<any[]> {
    let params = new HttpParams()
      .set('employees', employeeIds.join(',')) // 👈 IMPORTANT
      .set('start_date', startDate)
      .set('end_date', endDate)
      .set('query', query);
    return this.http.get<any[]>(`${this.apiUrl}/attendance/total-timecard`, { params }).pipe(
      catchError((error): Observable<any[]> => {
        return of([]); // Return empty array on error
      })
    );
  }

  downloadPresencesExcel(
    employeeIds: number[],
    startDate: string,
    endDate: string,
    query: string = ''): Observable<Blob> {
    let params = new HttpParams()
      .set('employees', employeeIds.join(','))
      .set('start_date', startDate)
      .set('end_date', endDate)
      .set('query', query);
    return this.http.get(`${this.apiUrl}/attendance/total-timecard/export`, {
      params,
      responseType: 'blob'
    }).pipe(
      catchError((error): Observable<Blob> => {
        console.error('Error downloading Excel file:', error);
        return of(new Blob()); // Return empty Blob on error
      })
    );
  }
}