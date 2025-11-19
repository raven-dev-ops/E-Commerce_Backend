# E-Commerce Backend Wiki

This wiki centralizes project documentation and task lists for the e-commerce backend.

## Documentation Index

- `README.md` — setup, usage notes, and high-level overview.
- `BACKLOG.md` — detailed backend improvement tasks (completed and planned).
- `timeline.md` — project chronology and milestones.
- `roadmap.md` — near-term, mid-term, and long-term direction.

## Task Overview

All checklist-style tasks are organized below so this wiki is the canonical place to see what is done and what is still outstanding.

### Backend Improvement Tasks (from `BACKLOG.md`)

These are the core technical tasks for the backend. See `BACKLOG.md` for full context and any future edits.

#### Completed

> Completed items (snapshot from `BACKLOG.md` at the time of compilation):

- [x] Make DEBUG configurable via environment variable to ease local development and production configuration.
- [x] Add additional security headers (e.g., Content-Security-Policy, Strict-Transport-Security) in custom middleware for better hardening.
- [x] Optimize product list endpoint by reducing verbose logging and adding caching to the list query.
- [x] Trigger asynchronous order confirmation emails after order creation using Celery.
- [x] Introduce rate limiting on the login endpoint to mitigate brute-force attacks.
- [x] Add unit tests for `SecurityHeadersMiddleware` to verify required HTTP headers are present.
- [x] Refactor order creation logic into a service layer to reduce complexity and ensure atomic inventory updates.
- [x] Implement structured logging with configurable log levels and forward logs to external monitoring.
- [x] Enforce code linting (e.g., flake8/black) and integrate checks into the CI pipeline.
- [x] Require email verification for new user signups and send verification emails asynchronously.
- [x] Provide a `/health/` endpoint for basic application and database connectivity checks.
- [x] Replace stubbed `Discount` and `Category` classes in the discounts API with real model integration and remove temporary placeholders.
- [x] Implement unit tests for the discounts app covering models and API endpoints.
- [x] Generate API documentation (e.g., OpenAPI/Swagger) for easier client integration.
- [x] Serve a minimal `robots.txt` for basic SEO directives.
- [x] Add Django `AUTH_PASSWORD_VALIDATORS` to enforce strong password rules.
- [x] Replace `TokenAuthentication` with `JWTAuthentication` in order and review viewsets.
- [x] Introduce pagination to the review list endpoint to prevent unbounded result sets.
- [x] Apply rate throttling to review creation to mitigate spam submissions.
- [x] Move review rating and count updates into model methods or a service layer.
- [x] Add tests covering review creation, update, and deletion with rating recalculation.
- [x] Allow client-defined page size with an upper bound in `CustomProductPagination`.
- [x] Restrict product creation, update, and deletion endpoints to staff users.
- [x] Add a unique `slug` field to `Product` for SEO-friendly URLs.
- [x] Support filtering products by category and price range using query parameters.
- [x] Write tests verifying caching behavior for product list and detail views.
- [x] Release reserved inventory when orders are canceled or payments fail.
- [x] Add unit tests for `create_order_from_cart` covering discounts and inventory changes.
- [x] Implement an order cancellation endpoint that restores inventory.
- [x] Schedule a periodic Celery task to purge inactive carts.
- [x] Provide a management command to remove expired email verification tokens.
- [x] Integrate Bandit security scanning into the CI workflow.
- [x] Add a `pre-commit` configuration to enforce formatting and linting before commits.
- [x] Introduce static type checking with mypy and add type hints across the codebase.
- [x] Cache category list responses and invalidate cache on updates.
- [x] Internationalize user-facing error messages via Django's translation framework.
- [x] Document authentication requirements and examples in the README.
- [x] Normalize discount codes to enforce case-insensitive uniqueness.
- [x] Log unhandled Stripe webhook event types for easier debugging.
- [x] Integrate Sentry for centralized error monitoring.
- [x] Implement API versioning to support backward-compatible changes.
- [x] Add a GraphQL endpoint to enable flexible client queries.
- [x] Introduce soft-delete functionality for products, orders, and carts with restoration options.
- [x] Add database indexes on frequently queried fields to improve performance.
- [x] Enforce global API rate limiting to protect against abusive traffic.
- [x] Optimize queryset performance using `select_related` and `prefetch_related` where appropriate.
- [x] Implement background SMS notifications for order status updates.
- [x] Provide bulk product import and export via CSV files.
- [x] Implement WebSocket-based real-time order status notifications.
- [x] Add a feature flag framework to allow gradual feature rollouts.
- [x] Support distributed caching with a Redis cluster for scalability.
- [x] Implement audit logging for sensitive administrative actions.
- [x] Add integration tests validating Stripe webhook processing.
- [x] Introduce full-text search powered by Elasticsearch.
- [x] Monitor Celery tasks with metrics and alerts on failures.
- [x] Provide a management command to seed the database with sample data.
- [x] Offload product image uploads to asynchronous cloud storage such as S3.
- [x] Add an automated migration check in CI to catch potential issues early.
- [x] Support user profile avatars with size and format validation.
- [x] Configure dynamic CORS allowed origins per environment.
- [x] Schedule periodic cleanup of expired user sessions.
- [x] Publish an official Python API client SDK for external integrators.
- [x] Add an endpoint exposing API rate usage and limits.
- [x] Cache CORS pre-flight responses to reduce request overhead.
- [x] Provide a quickstart guide for new contributors in the README.
- [x] Include a security.txt file for vulnerability disclosure.
- [x] Expose an admin endpoint to purge application caches.

#### Open

> Open items (snapshot from `BACKLOG.md` at the time of compilation):

- [ ] Support SAML-based single sign-on for enterprise customers.
- [ ] Add account deletion flow with email confirmation.
- [ ] Encrypt sensitive data at rest using a KMS.
- [ ] Offer per-user notification preference settings.
- [ ] Support partial returns for individual order line items.
- [ ] Define rules for stacking multiple coupons on one order.
- [ ] Add subscription billing for recurring product purchases.
- [ ] Provide personalized product recommendations via ML models.
- [ ] Supply a script to reset the staging database.
- [ ] Enforce commit signature verification in the repository.
- [ ] Customize logging formats per environment.
- [ ] Integrate with a service mesh for resilient networking.
- [ ] Report code coverage metrics in the CI pipeline.
- [ ] Send Slack alerts when critical errors occur.
- [ ] Allow users to revoke their own API keys.
- [ ] Track user consent preferences for marketing emails.
- [ ] Add an endpoint to check real-time inventory availability.
- [ ] Calculate tax based on customer location automatically.
- [ ] Build analytics charts for the admin dashboard.
- [ ] Store feature toggle states in the database for runtime updates.
- [ ] Offer an API sandbox environment for integrators.
- [ ] Use UUIDs as primary keys across models.
- [ ] Implement job retry policies with exponential backoff.
- [ ] Manage translations through an external service like Transifex.
- [ ] Separate access logs into a dedicated security log.
- [ ] Publish API deprecation notices ahead of breaking changes.
- [ ] Add a dark mode option to the admin interface.
- [ ] Set proper caching headers on REST API responses.
- [ ] Generate signed URLs for accessing private assets.
- [ ] Retry failed webhooks with exponential backoff.
- [ ] Monitor database replication lag and alert on thresholds.
- [ ] Stream inventory updates using Server-Sent Events.
- [ ] Provide gRPC client SDK code generation scripts.
- [ ] Make audit logs queryable through an API endpoint.
- [ ] Allow customers to schedule preferred delivery dates.

### Documentation & Planning Tasks

These tasks relate to documentation, planning, and project organization.

#### Timeline (`timeline.md`)

- [ ] Add initial project milestones and release dates.
- [ ] Keep the timeline updated as new features ship.

#### Roadmap (`roadmap.md`)

- [ ] Extract concrete roadmap items from `BACKLOG.md`.
- [ ] Prioritize features based on business impact and technical risk.
- [ ] Define scaling, performance, and reliability milestones.
- [ ] Plan integrations with external services and systems.
- [ ] Capture multi-year product and platform goals.
- [ ] Revisit and revise the roadmap regularly.

#### README / Repo-Level Docs

- [ ] Ensure `README.md`, `timeline.md`, `roadmap.md`, and `wiki.md` stay in sync as the source of truth for documentation and tasks.

---

## License & Usage

This repository is provided with **no license**. All rights are reserved by the owner; you are not granted any rights to use, copy, modify, or distribute this code without explicit written permission from the owner. See the **License & Usage** section in `README.md` for the authoritative statement.

