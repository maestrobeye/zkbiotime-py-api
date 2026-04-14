import { Component, ChangeDetectionStrategy, inject, signal, computed, Signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DataService } from '../../services/data.service';
import { Employee } from '../../types/employee';
import { toSignal } from '@angular/core/rxjs-interop';

interface StatCard {
  title: string;
  value: string | number;
  icon: string;
  color: string;
}

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule]
})
export class DashboardComponent {
  private dataService = inject(DataService);
  
  // FIX: Explicitly type the `employees` signal to resolve type inference issues with `toSignal`.
  employees: Signal<Employee[]> = toSignal(this.dataService.getEmployees(), { initialValue: [] });
  
  totalEmployees = computed(() => this.employees().length);
  activeEmployees = computed(() => this.employees().filter(e => e.status === 'Active').length);
  onLeave = computed(() => this.employees().filter(e => e.status === 'On Leave').length);

  hoursToday = computed(() => {
    const today = new Date().toISOString().slice(0, 10);
    return this.employees()
      .flatMap(e => e.timeEntries)
      .filter(t => t.date === today)
      .reduce((sum, t) => sum + t.totalHours, 0)
      .toFixed(1);
  });

  hoursThisMonth = computed(() => {
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth();

    return this.employees()
      .flatMap(e => e.timeEntries)
      .filter(t => {
        const entryDate = new Date(t.date);
        return entryDate.getFullYear() === currentYear && entryDate.getMonth() === currentMonth;
      })
      .reduce((sum, t) => sum + t.totalHours, 0)
      .toFixed(1);
  });
  
  activeEmployeesPercentage = computed(() => {
    const total = this.totalEmployees();
    if (total === 0) {
      return '0%';
    }
    const active = this.activeEmployees();
    return `${Math.round((active / total) * 100)}%`;
  });
  
  statCards = computed<StatCard[]>(() => [
    { title: 'Total des employés', value: this.totalEmployees(), icon: 'users', color: 'bg-blue-500' },
    { title: 'Employés actifs', value: this.activeEmployees(), icon: 'user-check', color: 'bg-green-500' },
    { title: 'Taux d\'activité', value: this.activeEmployeesPercentage(), icon: 'percent', color: 'bg-pink-500' },
    { title: 'En congé', value: this.onLeave(), icon: 'user-minus', color: 'bg-yellow-500' },
    { title: 'Heures aujourd\'hui', value: this.hoursToday() + 'h', icon: 'clock', color: 'bg-indigo-500' },
    { title: 'Heures ce mois-ci', value: this.hoursThisMonth() + 'h', icon: 'calendar', color: 'bg-purple-500' }
  ]);

  recentActivity = computed(() => {
    const today = new Date().toISOString().slice(0, 10);
    return this.employees()
      .filter(e => e.timeEntries.some(t => t.date === today))
      .map(e => ({
          name: e.name,
          position: e.position,
          clockIn: e.timeEntries.find(t => t.date === today)?.clockIn || '--:--'
      }))
      .slice(0, 5);
  });
}