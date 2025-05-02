# Migration Plan: Legacy Repository Wrapper to Repository Factory

## Overview

This document outlines the plan to migrate from the legacy `Repository` wrapper to directly using the `RepositoryFactory` pattern throughout the codebase. This will simplify the database access layer, remove unnecessary abstraction, and improve code maintainability.

## Current Architecture

Currently, the codebase uses a dual approach:

1. **Legacy Repository Wrapper**: `artificial_u/models/repository.py` contains a `Repository` class that wraps around `RepositoryFactory` for backward compatibility.
2. **Repository Factory**: `artificial_u/models/repositories/factory.py` contains the modern `RepositoryFactory` class with specific repository implementations.

## Migration Steps

### 1. Update Service Classes

Replace `Repository` parameter in service class constructors with `RepositoryFactory`:

```python
# Before
def __init__(self, repository: Repository, ...):
    self.repository = repository

# After
def __init__(self, repository_factory: RepositoryFactory, ...):
    self.repository_factory = repository_factory
```

Update repository method calls:

```python
# Before
self.repository.course.get(course_id)

# After
self.repository_factory.course.get(course_id)
```

### 2. Update Service Instantiation

When instantiating services, pass the repository factory directly:

```python
# Before
service = SomeService(repository=repository, ...)

# After
service = SomeService(repository_factory=repository_factory, ...)
```

### 3. Update API Layer

Update API service classes to use `RepositoryFactory`:

```python
# Before
class SomeApiService:
    def __init__(self, repository: Repository, ...):
        self.repository = repository
        self.core_service = CoreService(repository=repository, ...)

# After
class SomeApiService:
    def __init__(self, repository_factory: RepositoryFactory, ...):
        self.repository_factory = repository_factory
        self.core_service = CoreService(repository_factory=repository_factory, ...)
```

### 4. Update Dependency Injection

Update dependency injection in API routes:

```python
# Before
def get_service(repository: Repository = Depends(get_repository)):
    return SomeService(repository=repository)

# After
def get_service(repository_factory: RepositoryFactory = Depends(get_repository_factory)):
    return SomeService(repository_factory=repository_factory)
```

### 5. Create/Update Factory Dependencies

Ensure proper factory injection is available:

```python
# Create or update in dependencies.py or similar
def get_repository_factory() -> RepositoryFactory:
    return RepositoryFactory(db_url=settings.DATABASE_URL)
```

### 6. Clean Up Legacy Repository

Once all references to the legacy `Repository` have been migrated:

1. Mark the `Repository` class as deprecated with warnings
2. Eventually remove the class entirely

## Progress Tracking

| Component | Status | Notes |
|-----------|--------|-------|
| CourseService | ✅ Completed | Direct use of RepositoryFactory |
| CourseApiService | ✅ Completed | Updated to use RepositoryFactory |
| ProfessorService | ⏳ Pending | |
| LectureService | ⏳ Pending | |
| AudioService | ⏳ Pending | |
| ... | | |

## Testing Strategy

After each service is updated:

1. Run unit tests for that service
2. Run integration tests that depend on that service
3. Verify functionality in development environment

## Benefits

- **Simplified Architecture**: Direct use of repositories without unnecessary wrappers
- **Improved Code Readability**: Clearer where database calls are happening
- **Better Maintainability**: Fewer abstraction layers to maintain
- **Consistent Pattern**: All code follows the same repository access pattern
