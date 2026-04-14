import { Component, ChangeDetectionStrategy, inject, signal, computed, effect, Signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink, ParamMap } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { switchMap } from 'rxjs/operators';
import { DataService } from '../../services/data.service';
import { FormsModule } from '@angular/forms';
import { Employee, TimeEntry } from '../../types/employee';

@Component({
  selector: 'app-employee',
  templateUrl: './employee.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, RouterLink, FormsModule]
})
export class EmployeeComponent {
  private route: ActivatedRoute = inject(ActivatedRoute);
  private dataService: DataService = inject(DataService);

  // FIX: Explicitly type the `employee` signal to `Signal<Employee | undefined>`.
  // This resolves the type inference issue where `employee()` was being treated as `unknown`,
  // causing a compilation error when accessing `employee().timeEntries`.
  employee: Signal<Employee | undefined> = toSignal(
    this.route.paramMap.pipe(
      switchMap((params: ParamMap) => {
        const id = Number(params.get('id'));
        return this.dataService.getEmployeeById(id);
      })
    )
  );

  // Filter signals
  startDateTime = signal<string>('');
  endDateTime = signal<string>('');

  constructor() {
    effect(() => {
      // Reset page to 1 when filters or employee changes
      this.startDateTime();
      this.endDateTime();
      this.employee();
      this.currentPage.set(1);
    });
  }
  
  filteredTimeEntries = computed<TimeEntry[]>(() => {
    const emp = this.employee();
    if (!emp) {
      return [];
    }
    
    // Create a copy and sort by date descending
    const entries = [...emp.timeEntries].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
    const sDateTime = this.startDateTime();
    const eDateTime = this.endDateTime();

    if (!sDateTime && !eDateTime) {
      return entries;
    }
    
    return entries.filter(entry => {
      const entryDateTime = `${entry.date}T${entry.clockIn}`;
      const startMatch = !sDateTime || entryDateTime >= sDateTime;
      const endMatch = !eDateTime || entryDateTime <= eDateTime;
      return startMatch && endMatch;
    });
  });

  // Pagination logic
  pageSize = 10;
  currentPage = signal(1);

  totalPages = computed(() => {
    return Math.ceil(this.filteredTimeEntries().length / this.pageSize);
  });

  paginatedTimeEntries = computed(() => {
    const entries = this.filteredTimeEntries();
    const startIndex = (this.currentPage() - 1) * this.pageSize;
    const endIndex = startIndex + this.pageSize;
    return entries.slice(startIndex, endIndex);
  });
  
  startRecordIndex = computed(() => {
    if (this.filteredTimeEntries().length === 0) return 0;
    return (this.currentPage() - 1) * this.pageSize + 1;
  });

  endRecordIndex = computed(() => Math.min(this.currentPage() * this.pageSize, this.filteredTimeEntries().length));

  
  getStatusClass(status: 'Active' | 'On Leave' | 'Terminated' | undefined): string {
    if (!status) return 'bg-gray-100 text-gray-800';
    switch (status) {
      case 'Active': return 'bg-green-100 text-green-800';
      case 'On Leave': return 'bg-yellow-100 text-yellow-800';
      case 'Terminated': return 'bg-red-100 text-red-800';
      default: 'bg-gray-100 text-gray-800';
    }
    return 'bg-gray-100 text-gray-800';
  }

  goToNextPage(): void {
    if (this.currentPage() < this.totalPages()) {
      this.currentPage.update(page => page + 1);
    }
  }

  goToPreviousPage(): void {
    if (this.currentPage() > 1) {
      this.currentPage.update(page => page - 1);
    }
  }
  
  clearFilters(): void {
    this.startDateTime.set('');
    this.endDateTime.set('');
  }
}
