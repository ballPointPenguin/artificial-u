# ArtificialU API Middlewares

This directory contains the middleware components used in the ArtificialU API.

## Available Middlewares

### CORS Middleware

The CORS (Cross-Origin Resource Sharing) middleware handles cross-origin requests from web clients. It's configured in `cors_middleware.py` and supports different settings for development and production environments.

#### Configuration

CORS settings are defined in `artificial_u/config/settings.py` under the `cors_origins` property. The default configuration includes:

- Development origins:
  - `http://localhost:8000` (API server)
  - `http://localhost:3000` (Frontend development server)
  - `http://localhost:5173` (Vite development server)

- Production origins:
  - `https://artificial-u.example.com`
  - `https://*.artificial-u.example.com`

#### Environment-specific Settings

The middleware automatically adjusts its behavior based on the current environment:

- **Development**: More permissive CORS settings with detailed logging
- **Production**: Stricter security settings with appropriate origins

#### CORS Headers

The middleware adds the following headers to responses for allowed origins:

- `Access-Control-Allow-Origin`: Specifies which origins can access the resource
- `Access-Control-Allow-Credentials`: Allows cookies and authentication headers
- `Access-Control-Allow-Methods`: Allows all standard HTTP methods
- `Access-Control-Allow-Headers`: Allows all request headers
- `Access-Control-Expose-Headers`: Exposes Content-Disposition header for file downloads
- `Access-Control-Max-Age`: Caches preflight responses for 10 minutes

### Logging Middleware

The logging middleware (`logging_middleware.py`) captures request and response information for debugging and monitoring.

### Error Handler

The error handler (`error_handler.py`) provides consistent error responses across the API.

## Adding New Middleware

When adding new middleware:

1. Create a new file in this directory
2. Implement the middleware class or function
3. Register it in `app.py` using `app.add_middleware()`
