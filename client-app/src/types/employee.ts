
export interface TimeEntry {
  date: string;
  clockIn: string;
  clockOut: string;
  totalHours: number;
}

export interface Employee {
  id: number;
  name: string;
  position: string;
  email: string;
  phone: string;
  status: 'Active' | 'On Leave' | 'Terminated';
  timeEntries: TimeEntry[];
}