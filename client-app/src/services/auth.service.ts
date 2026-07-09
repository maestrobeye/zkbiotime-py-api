
import { inject, Injectable, signal } from '@angular/core';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { catchError, delay, mapTo, tap } from 'rxjs/operators';
import { User } from '../types/user'
import { HttpClient } from '@angular/common/http';
@Injectable({
  providedIn: 'root'
})
export class AuthService {
  isAuthenticated = signal<boolean>(false);
  private tokenName = 'Token';
  private token: string | null = null;
  private http: HttpClient = inject(HttpClient);
  private apiUrl = 'http://10.14.209.12:8000';

  private currentUserManager: BehaviorSubject<any> = new BehaviorSubject(null);
  public currentUserProvider = this.currentUserManager.asObservable();

  login(username: string, password: string): Observable<boolean> {
    return this.http.post<{ token: string }>(`${this.apiUrl}/auth/login`, { username, password }).pipe(
      tap(response => {
        this.setToken(response.token);
        this.isAuthenticated.set(true);
      }),
      mapTo(true),
      catchError(() => of(false))
    );
  }

  public get currentUserValue(): User {
    return this.currentUserManager.value;
  }

  logout(): void {
    localStorage.removeItem(this.getTokenName())
    this.isAuthenticated.set(false);
  }

  public getTokenName() {
    return this.tokenName;
  }

  public getToken() {
    if (this.token == null) {
      return this.token = localStorage.getItem(this.tokenName);
    }
    return this.token;
  }

  public setToken(token: string) {
    this.token = token;
    localStorage.setItem(this.tokenName, token);
    this.isAuthenticated.set(true);
  }

  /**
   * @author Mamadou lamine BEYE
   * @description Définit l'utilisateur dans le subject afin de le propager
   * à tous les programmes qui souhaitent récuperer l'utilisateur connecté
   * @param user
   * @copyright isep-thies
   * @since 21.12.25
   */
  setCurrentUser(user: any) {
    this.currentUserManager.next(user);
    localStorage.setItem('currentUser', JSON.stringify(user));
  }

  /**
  * @author Mamadou lamine BEYE
  * @description Recupere l'utilisateur connecté
  * Cette fonction est surtout appelée pendant l'initialisation
  * du projet pour récuperer le user à partir du Token
  * @since 21.01.22
  * @copyright isep-thies
  * @returns Promise
  */
  getCurrentUser() {
    return new Promise((resolve) => {
      const token = localStorage.getItem('Token');

      if (!token) {
        resolve(null);
        return;
      }

      // Optionnel : si tu stockes aussi l'user
      const user = localStorage.getItem('currentUser');
      resolve(user ? JSON.parse(user) : null);
    });

  }

  initAuth() {
    const token = localStorage.getItem(this.tokenName);

    if (token) {
      this.token = token;
      this.isAuthenticated.set(true);

      const user = localStorage.getItem('currentUser');
      if (user) {
            // this.currentUserManager.next(JSON.parse(user));
      }
    } else {
      this.isAuthenticated.set(false);
    }
  }
}
