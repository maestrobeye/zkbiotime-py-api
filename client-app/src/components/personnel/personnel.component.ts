import { Component, ChangeDetectionStrategy, inject, signal, computed, Signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { toSignal, toObservable } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { switchMap } from 'rxjs/operators';

import { DataService, PaginatedEmployees } from '../../services/data.service';

@Component({
  selector: 'app-personnel',
  templateUrl: './personnel.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, RouterLink]
})
export class PersonnelComponent {
  private dataService = inject(DataService);
  
  currentPage = signal(1);
  private page$ = toObservable(this.currentPage);

  // FIX: Explicitly type the `response` signal to resolve type inference issues with `toSignal`.
  private response: Signal<PaginatedEmployees | undefined> = toSignal(
    this.page$.pipe(
      switchMap(page => this.dataService.getEmployeesPaginated(page))
    )
  );

   private responsePresence: Signal<any | undefined> = toSignal(
    this.page$.pipe(
      switchMap(page => this.dataService.getPresences([93], '2025-12-01', '2025-12-31',   "31"))
    )
  );

  employees = computed(() => this.response()?.data ?? []);
  totalPages = computed(() => this.response()?.total_pages ?? 1);
  totalResults = computed(() => this.response()?.total_results ?? 0);
  presences = computed(() => {
    console.log(this.responsePresence());
  });

  pageStart = computed(() => this.response() ? ((this.response()!.page - 1) * this.response()!.page_size) + 1 : 0);
  pageEnd = computed(() => this.response() ? Math.min(this.response()!.page * this.response()!.page_size, this.response()!.total_results) : 0);

  paginationPages = computed<Array<number | string>>(() => {
    const totalPages = this.totalPages();
    const currentPage = this.currentPage();
    if (totalPages <= 1) {
      return [];
    }
    
    const pages: Array<number | string> = [];
    const maxPagesToShow = 7;
    
    if (totalPages <= maxPagesToShow) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      pages.push(1);
      
      let startPage: number;
      let endPage: number;

      if (currentPage <= 4) {
        startPage = 2;
        endPage = 5;
        pages.push(...Array.from({length: endPage - startPage + 1}, (_, i) => startPage + i));
        pages.push('...');
      } else if (currentPage >= totalPages - 3) {
        startPage = totalPages - 4;
        endPage = totalPages - 1;
        pages.push('...');
        pages.push(...Array.from({length: endPage - startPage + 1}, (_, i) => startPage + i));
      } else {
        startPage = currentPage - 1;
        endPage = currentPage + 1;
        pages.push('...');
        pages.push(...Array.from({length: endPage - startPage + 1}, (_, i) => startPage + i));
        pages.push('...');
      }
      
      pages.push(totalPages);
    }
    
    return pages;
  });

  goToPage(page: number | string): void {
    if (typeof page === 'number') {
      this.currentPage.set(page);
    }
  }

  getStatusClass(status: 'Active' | 'On Leave' | 'Terminated'): string {
    switch (status) {
      case 'Active': return 'bg-green-100 text-green-800';
      case 'On Leave': return 'bg-yellow-100 text-yellow-800';
      case 'Terminated': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  }
  
  nextPage(): void {
    if (this.currentPage() < this.totalPages()) {
      this.currentPage.update(p => p + 1);
    }
  }

  previousPage(): void {
    if (this.currentPage() > 1) {
      this.currentPage.update(p => p - 1);
    }
  }
}