import { Component, ChangeDetectionStrategy, signal, OnInit, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, RouterLinkActive],
  host: {
    '(document:click)': 'closeProfileMenu()',
  },
})
export class HeaderComponent implements OnInit {
  isMobileMenuOpen = signal(false);
  isProfileMenuOpen = signal(false);
  currentDate = signal('');
  currentUser: any;
  subscriptions: Subscription[] = []

  // FIX: Add explicit types to injected services to resolve 'unknown' type errors.
  private authService: AuthService = inject(AuthService);
  private router: Router = inject(Router);

  ngOnInit(): void {
    this.updateDate();
     const subscription = this.authService.currentUserProvider
      .subscribe((user: any) => this.currentUser = user)
    if (!this.subscriptions.includes(subscription)) {
      this.subscriptions.push(subscription)
    }
  }

  toggleMobileMenu(): void {
    this.isMobileMenuOpen.update(v => !v);
  }

  toggleProfileMenu(): void {
    this.isProfileMenuOpen.update(v => !v);
  }
  
  closeProfileMenu(): void {
    this.isProfileMenuOpen.set(false);
  }

  logout(): void {
    this.closeProfileMenu();
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  private updateDate(): void {
    const date = new Date();
    // Mocking date to match the screenshot
    date.setDate(new Date().getDay());
    date.setMonth(new Date().getMonth()); // December is month 11
    date.setFullYear(new Date().getFullYear());
    const day = date.getDay();
    // Manually set to Monday if needed for consistency with image
    const dateOffset = day === 1 ? 0 : (1 - day + 7) % 7;
    date.setDate(date.getDate() + dateOffset);


    const formattedDate = date.toLocaleDateString('fr-FR', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
    // Capitalize the first letter
    this.currentDate.set(formattedDate.charAt(0).toUpperCase() + formattedDate.slice(1));
  }
}
