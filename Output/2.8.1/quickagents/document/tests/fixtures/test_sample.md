# Project Architecture

This document describes the system architecture.

## Frontend

The frontend uses Vue.js with TypeScript.

### Vue Components

Component-based architecture with Composition API.

### State Management

Pinia for global state, localStorage for persistence.

## Backend

Python FastAPI backend with async support.

### API Layer

REST API with JWT authentication middleware.

### Business Logic

Domain-driven design with service layer pattern.

## Database

PostgreSQL primary, Redis for caching.

### Schema Design

Normalized to 3NF with strategic denormalization.

### Migration Strategy

Alembic for schema migrations with version tracking.
