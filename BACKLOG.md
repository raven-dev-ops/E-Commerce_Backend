# Backend Improvement Tasks

- [ ] Make DEBUG configurable via environment variable to ease local development and production configuration.
- [ ] Add additional security headers (e.g., Content-Security-Policy, Strict-Transport-Security) in custom middleware for better hardening.
- [ ] Optimize product list endpoint by reducing verbose logging and adding caching to the list query.
- [ ] Standardize MongoDB connection environment variables between settings and connection helper.
- [ ] Trigger asynchronous order confirmation emails after order creation using Celery.
