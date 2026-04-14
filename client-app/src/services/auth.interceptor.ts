import { HttpInterceptorFn } from '@angular/common/http';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  // Do not add authorization headers to GET requests, as the public API for employee data
  // might not expect them and could cause the request to fail (e.g., due to CORS policy).
  if (req.method === 'GET') {
    const reqWithoutAuth = req.clone({
      setHeaders: {
        'Content-Type': 'application/json',
        'x-api-key': '1234',
        Authorization: 'Token 55edb303ff20f29a02c434fb5634a8cefd5c17cb',

      }
    });
    return next(reqWithoutAuth);
  }

  // For other requests (POST, PUT, DELETE, etc.), add the necessary headers.
  // In a real application, you would inject an AuthService
  // and retrieve the token dynamically.
  const authToken = '55edb303ff20f29a02c434fb5634a8cefd5c17cb';

  // Clone the request to add the new headers.
  const authReq = req.clone({
    setHeaders: {
      'Content-Type': 'application/json',
      Authorization: `Token ${authToken}`,
      'x-api-key': '1234'
    }
  });

  // Pass the cloned request with the updated headers to the next handler.
  return next(authReq);
};
