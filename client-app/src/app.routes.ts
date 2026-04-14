
import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';

export const APP_ROUTES: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./components/login/login.component').then(c => c.LoginComponent),
    title: 'Connexion'
  },
  {
    path: '',
    loadComponent: () => import('./components/main-layout/main-layout.component').then(c => c.MainLayoutComponent),
    canActivate: [authGuard],
    children: [
      {
        path: 'dashboard',
        loadComponent: () => import('./components/dashboard/dashboard.component').then(c => c.DashboardComponent),
        title: 'Dashboard'
      },
      {
        path: 'personnel',
        loadComponent: () => import('./components/personnel/personnel.component').then(c => c.PersonnelComponent),
        title: 'Personnel'
      },
      {
        path: 'historique',
        loadComponent: () => import('./components/history/history.component').then(c => c.HistoryComponent),
        title: 'Historique'
      },
      {
        path: 'employee/:id',
        loadComponent: () => import('./components/employee/employee.component').then(c => c.EmployeeComponent),
        title: 'Employee Details'
      },
      {
        path: 'statistics',
        loadComponent: () => import('./components/statistics/statistics.component').then(c => c.StatisticsComponent),
        title: 'Statistics'
      },
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full'
      },
    ]
  },
  {
    path: '**',
    redirectTo: '',
    pathMatch: 'full'
  }
];
