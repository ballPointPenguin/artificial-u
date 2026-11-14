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

# Example usage
departments = factory.department.list()
voices = factory.voice.list(gender="female")
```
