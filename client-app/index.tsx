import "@angular/compiler";
import { bootstrapApplication } from "@angular/platform-browser";
import { provideRouter, withHashLocation } from "@angular/router";
import { provideHttpClient, withInterceptors } from "@angular/common/http";
import {
  inject,
  provideAppInitializer,
  provideZonelessChangeDetection,
} from "@angular/core";

import { AppComponent } from "./src/app.component";
import { APP_ROUTES } from "./src/app.routes";
import { authInterceptor } from "./src/services/auth.interceptor";
import { AuthService } from "./src/services/auth.service";

bootstrapApplication(AppComponent, {
  providers: [
    provideZonelessChangeDetection(),
    provideRouter(APP_ROUTES, withHashLocation()),
    provideHttpClient(withInterceptors([authInterceptor])),
    provideAppInitializer(() => {
      inject(AuthService).initAuth();
    }),
  ],
}).catch((err) => console.error(err));

// AI Studio always uses an `index.tsx` file for all project types.
