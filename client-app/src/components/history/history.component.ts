import { Component, ChangeDetectionStrategy, computed, inject, signal, effect, Signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DataService } from '../../services/data.service';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { Employee } from '../../types/employee';
import { switchMap } from 'rxjs';

interface AttendanceRecord {
  employeeId: number;
  employeeName: string;
  date: string;
  status: 'Présent' | 'En retard';
  clockIn: string;
  clockOut: string;
  totalHours: number;
}

@Component({
  selector: 'app-history',
  templateUrl: './history.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule]
})
export class HistoryComponent {
  private dataService = inject(DataService);
  currentPage = signal(1);

  private page$ = toObservable(this.currentPage);

  // FIX: Explicitly type the `employees` signal to resolve type inference issues with `toSignal`.

  private responsePresence: Signal<any | undefined> = toSignal(
    this.page$.pipe(
      switchMap(page => this.dataService.getPresences([93, 94, 4, 97, 100, 79, 98, 99], '2025-12-01', '2025-12-31', "200"))
    )
  );
  // Filter signals
  startDateTime = signal<string>('');
  endDateTime = signal<string>('');

  constructor() {
    effect(() => {
      // Reset page to 1 when filters change
      this.startDateTime();
      this.endDateTime();
      this.currentPage.set(1);
    });
  }
  presences = computed(() => this.responsePresence()?.data ?? []);

  allAttendanceRecords = computed<any[]>(() => {
    console.log(this.presences());
    return this.presences()
      // .flatMap(employee =>
      .map(employee => ({
        employeeId: employee.id,
        employeeName: employee.first_name + ' ' + employee.last_name,
        date: employee.att_date,
        status: this.getAttendanceStatus(employee.clock_in),
        clockIn: employee.clock_in,
        clockOut: employee.clock_out,
        totalHours: employee.total_hrs,
      })
        // )
      )
      .sort((a, b) =>
        new Date(b.date).getTime() - new Date(a.date).getTime() ||
        (a.clockIn ?? '').localeCompare(b.clockIn ?? '')
      );
  });

  filteredAttendanceRecords = computed(() => {
    const allRecords = this.allAttendanceRecords();
    const sDateTime = this.startDateTime();
    const eDateTime = this.endDateTime();

    if (!sDateTime && !eDateTime) {
      return allRecords;
    }

    return allRecords.filter(record => {
      const recordDateTime = `${record.date}T${record.clockIn}`;
      const startMatch = !sDateTime || recordDateTime >= sDateTime;
      const endMatch = !eDateTime || recordDateTime <= eDateTime;
      return startMatch && endMatch;
    });
  });

  // Pagination logic
  pageSize = 100;

  totalPages = computed(() => {
    return Math.ceil(this.filteredAttendanceRecords().length / this.pageSize);
  });

  paginatedRecords = computed(() => {
    const records = this.filteredAttendanceRecords();
    const startIndex = (this.currentPage() - 1) * this.pageSize;
    const endIndex = startIndex + this.pageSize;
    return records.slice(startIndex, endIndex);
  });

  startRecordIndex = computed(() => {
    if (this.filteredAttendanceRecords().length === 0) return 0;
    return (this.currentPage() - 1) * this.pageSize + 1;
  });

  endRecordIndex = computed(() => Math.min(this.currentPage() * this.pageSize, this.filteredAttendanceRecords().length));

  getAttendanceStatus(clockIn: string = "9:00"): 'Présent' | 'En retard' | 'Absent' {
    if (!clockIn) {
      return 'Absent'; // or 'Not Clocked In'
    }
    const [hours, minutes] = clockIn.split(':').map(Number);
    // Late is defined as clocking in after 9:00 AM.
    if (hours > 9 || (hours === 9 && minutes > 0)) {
      return 'En retard';
    }
    return 'Présent';
  }

  getStatusClass(status: 'Présent' | 'En retard' | 'Absent'): string {
    switch (status) {
      case 'Présent': return 'bg-green-100 text-green-800';
      case 'En retard': return 'bg-yellow-100 text-yellow-800';
      case 'Absent': return 'bg-red-100 text-yellow-800';
    }
  }

  goToNextPage(): void {
    if (this.currentPage() < this.totalPages()) {
      // FIX: Correctly call update on the signal, not its value.
      this.currentPage.update(page => page + 1);
    }
  }

  goToPreviousPage(): void {
    if (this.currentPage() > 1) {
      // FIX: Correctly call update on the signal, not its value.
      this.currentPage.update(page => page - 1);
    }
  }

  clearFilters(): void {
    this.startDateTime.set('');
    this.endDateTime.set('');
  }

  exportData(): void {
    const records = this.filteredAttendanceRecords();
    if (records.length === 0) {
      alert("Aucune donnée à exporter avec les filtres actuels.");
      return;
    }

    const headers = ['Employé', 'Date', 'Statut', 'Arrivée', 'Départ', 'Total Heures'];
    const csvRows = [
      headers.join(','),
      ...records.map(r => [
        `"${r.employeeName.replace(/"/g, '""')}"`,
        r.date,
        r.status,
        r.clockIn,
        r.clockOut,
        r.totalHours.toFixed(2)
      ].join(','))
    ];

    const csvString = csvRows.join('\n');
    // FIX: Corrected typo in charset from 'utf-t' to 'utf-8'.
    const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    const today = new Date().toISOString().slice(0, 10);
    link.setAttribute('download', `export_pointages_${today}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  // exportDataExcel(): void {
  //   console.log("Downloading Excel file...");
  //   this.dataService.downloadPresencesExcel([93,94,4,97,100,79,98,99], '2025-12-01', '2025-12-31', "200")
  // }
  exportDataExcel(): void {
    console.log('Downloading Excel file...');

    this.dataService
      .downloadPresencesExcel(
        [93, 94, 4, 97, 100, 79, 98, 99],
        '2025-12-01',
        '2025-12-31',
        '200'
      )
      .subscribe({
        next: (blob: Blob) => {
          this.downloadFile(blob, 'attendance.xlsx');
        },
        error: (err) => {
          console.error('Download failed', err);
        }
      });
  }

  private downloadFile(blob: Blob, fileName: string): void {
    if (!blob || blob.size === 0) {
      console.warn('Empty file received');
      return;
    }

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    a.click();

    window.URL.revokeObjectURL(url);
  }
}