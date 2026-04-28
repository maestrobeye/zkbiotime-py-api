
import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { User } from '@/src/types/user';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, ReactiveFormsModule]
})
export class LoginComponent {
  // FIX: Add explicit types to injected services to resolve 'unknown' type errors.
  private fb: FormBuilder = inject(FormBuilder);
  private authService: AuthService = inject(AuthService);
  private router: Router = inject(Router);

  isLoading = signal(false);
  errorMessage = signal<string | null>(null);
  passwordVisible = signal(false);
  currentUser: User | null = null;

  loginForm = this.fb.group({
    email: ['admin@pointage.pro', [Validators.required, Validators.email]],
    password: ['password', [Validators.required]]
  });

  togglePasswordVisibility(): void {
    this.passwordVisible.update(v => !v);
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      this.errorMessage.set('Veuillez remplir tous les champs correctement.');
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set(null);
    const { email, password } = this.loginForm.value;

    this.authService.login(email!, password!).subscribe({
      next: (data: any) => {
        this.isLoading.set(false);
        this.currentUser = {
          email: email,
          name: 'Admin User'
        }

        this.authService.setToken('55edb303ff20f29a02c434fb5634a8cefd5c17cb');
        this.authService.setCurrentUser(this.currentUser);
        if (data) {
          this.router.navigate(['/dashboard']);
        } else {
          this.errorMessage.set('Email ou mot de passe incorrect.');
        }
      },
      error: () => {
        this.isLoading.set(false);
        this.errorMessage.set('Une erreur est survenue. Veuillez réessayer.');
      }
    });
  }
}