# Repository Architecture

This directory contains the new repository architecture for ArtificialU, which follows the repository pattern with better separation of concerns.

## Architecture Overview

The repository architecture consists of the following components:

- **BaseRepository**: Common functionality shared by all repositories
- **Entity-specific repositories**: Repositories for each entity type (Department, Professor, Course, Lecture, Voice)
- **RepositoryFactory**: Factory class for creating and managing repository instances

## Migration Guide

To migrate your codebase to the new repository architecture, follow these steps:

#### Step 1: Update imports

Replace your old repository imports with the new repository import:

```python
from artificial_u.models.repositories import RepositoryFactory
```

#### Step 2: Update initialization

```python
# Initialize the RepositoryFactory with your database URL
factory = RepositoryFactory(db_url="postgresql://...")
```

#### Step 3: Update repository calls

```python
# Use the new RepositoryFactory properties to perform operations
departments = factory.department.list()
professor = factory.professor.get(professor_id)
course = factory.course.create(new_course)
```

### Benefits of the New Architecture

1. **Better separation of concerns**: Each entity type has its own repository
2. **Improved maintainability**: Smaller files are easier to understand and modify
3. **More granular testing**: Test repositories independently
4. **Code reuse**: Share common repository logic through inheritance
5. **Dependency injection**: The repository factory provides a clean way to manage dependencies
6. **Interface consistency**: Method names and signatures are consistent across repositories

### Repository Methods

Each repository follows a consistent pattern with standard methods:

- `create(entity)`: Create a new entity
- `get(id)`: Get an entity by ID
- `list()`: List entities (with optional filters)
- `update(entity)`: Update an existing entity
- `delete(id)`: Delete an entity by ID

Additional specialized methods may be available for specific repository types.

## Using the Repository Factory

The `RepositoryFactory` class provides access to all repositories through properties:

```python
factory = RepositoryFactory()

# Access repositories
factory.department  # DepartmentRepository
factory.professor   # ProfessorRepository
factory.course      # CourseRepository
factory.lecture     # LectureRepository
factory.voice       # VoiceRepository

# Create tables if they don't exist
factory.create_tables()

# Example usage
departments = factory.department.list()
voices = factory.voice.list(gender="female")
```

## Test Suite Migration

Integration tests and support files have been updated to use the new RepositoryFactory nested interface. Please update any direct repository calls in your tests accordingly. For example:

- Replace `repository.create_professor(entity)` with `repository.professor.create(entity)`
- Replace `repository.get_professor(id)` with `repository.professor.get(id)`
- Replace `repository.list_professors()` with `repository.professor.list()`
- Replace `repository.create_course(entity)` with `repository.course.create(entity)`
- Replace `repository.get_course(id)` with `repository.course.get(id)`
- Replace `repository.get_course_by_code(code)` with `repository.course.get_by_code(code)`
- Replace `repository.list_courses()` with `repository.course.list()`
- Replace `repository.create_lecture(entity)` with `repository.lecture.create(entity)`
- Replace `repository.get_lecture(id)` with `repository.lecture.get(id)`
- Replace `repository.get_lecture_by_course_week_order(course_id, week, order)` with `repository.lecture.get_by_course_week_order(course_id, week, order)`
- Replace `repository.list_lectures_by_course(course_id)` with `repository.lecture.list_by_course(course_id)`

### Legacy UniversitySystem Methods

In addition to repository calls, some tests use legacy UniversitySystem methods (e.g., `create_professor`, `create_course`, and `generate_lecture`). These methods have been monkey patched to internally delegate to the new RepositoryFactory interface:

- `create_professor` now wraps `repository.professor.create`
- `create_course` now wraps `repository.course.create`
- `generate_lecture` now wraps `repository.lecture.create`

Make sure your test environment is configured to use these updated calls.
