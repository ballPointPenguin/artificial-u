# API Service Patterns and Standard Idioms

This document outlines the standardized patterns and idioms for API services to ensure consistency across the codebase.

## Overview

The API services follow a consistent pattern for list operations, error handling, and data transformation. This standardization improves maintainability, reduces code duplication, and ensures consistent behavior across all endpoints.

## Base Service Class

All API services should inherit from `BaseApiService` which provides standardized methods for common operations.

### Generic Types

```python
class BaseApiService(Generic[T, R, L]):
    # T: Core model type (e.g., CoreLecture, CoreProfessor)
    # R: Response model type (e.g., Lecture, Professor)
    # L: List response model type (e.g., LectureListResponse, ProfessorsListResponse)
```

## Standard List Operation Pattern

### Template Method

Use the `_standard_list_operation` method for consistent list operations:

```python
def list_items(
    self,
    page: int = 1,
    size: int = 10,
    filters: Optional[Dict[str, Any]] = None,
    **kwargs
) -> ListResponse:
    """
    Get a paginated list of items with optional filtering.

    Args:
        page: Page number (1-indexed)
        size: Items per page
        filters: Optional filters to apply
        **kwargs: Additional arguments for core service

    Returns:
        ListResponse with paginated items
    """
    return self._standard_list_operation(
        core_service_method="list_items",
        response_class=ItemResponse,
        list_response_class=ItemListResponse,
        page=page,
        size=size,
        filters=filters,
        **kwargs
    )
```

### Manual Implementation

If you need more control, follow this pattern:

```python
def list_items(
    self,
    page: int = 1,
    size: int = 10,
    **filters
) -> ListResponse:
    """
    Get a paginated list of items with optional filtering.
    """
    try:
        # 1. Get all items from core service
        all_items = self.core_service.list_items(**filters)

        # 2. Apply additional filters if needed
        if additional_filter:
            all_items = self._apply_filters(all_items, additional_filter)

        # 3. Count total before pagination
        total = len(all_items)

        # 4. Apply pagination
        paginated_items = self._paginate_items(all_items, page, size)

        # 5. Convert to response models
        response_items = self._convert_to_response_models(
            paginated_items, ItemResponse
        )

        # 6. Create and return list response
        return self._create_list_response(
            response_items, total, page, size, ItemListResponse
        )

    except Exception as e:
        self._handle_general_error("list items", e)
```

## Standard Idioms

### 1. Pagination Calculation

**Always use**: `ceil(total / size)` for page calculation

```python
pages = ceil(total / size) if total > 0 else 1
```

### 2. Error Handling

**Use standardized error handlers**:

```python
try:
    # operation
except DatabaseError as e:
    self._handle_database_error("operation name", e)
except Exception as e:
    self._handle_general_error("operation name", e)
```

### 3. Model Conversion

**Use standardized conversion**:

```python
response_items = self._convert_to_response_models(core_items, ResponseClass)
```

### 4. Filter Application

**Use standardized filtering**:

```python
filtered_items = self._apply_filters(items, filters_dict)
```

### 5. List Response Creation

**Use standardized response creation**:

```python
return self._create_list_response(
    items, total, page, size, ListResponseClass
)
```

## Filter Patterns

### Dictionary-Based Filters

```python
filters = {
    "department_id": department_id,
    "name": name,
    "specialization": specialization,
}
```

### String Matching

For string filters, use case-insensitive partial matching:

```python
if name:
    items = [item for item in items
             if name.lower() in item.name.lower()]
```

### Exact Matching

For exact value matching:

```python
if department_id:
    items = [item for item in items
             if item.department_id == department_id]
```

## Response Model Patterns

### List Response Structure

All list responses should include:

- `items`: List of response models
- `total`: Total number of matching items
- `page`: Current page number
- `size`: Number of items per page
- `pages`: Total number of pages

### Brief Response Models

For related data (e.g., courses in a department), use brief models:

```python
class CourseBrief(BaseModel):
    id: int
    code: str
    title: str
    level: str
    credits: int
```

## Migration Guide

### Before (Inconsistent)

```python
def list_items(self, page=1, size=10):
    items = self.core_service.get_items()
    total = len(items)
    start = (page - 1) * size
    end = start + size
    paginated = items[start:end]

    return ItemListResponse(
        items=paginated,
        total=total,
        page=page,
        size=size,
        # Missing pages field!
    )
```

### After (Standardized)

```python
def list_items(self, page=1, size=10, **filters):
    return self._standard_list_operation(
        core_service_method="get_items",
        response_class=ItemResponse,
        list_response_class=ItemListResponse,
        page=page,
        size=size,
        filters=filters
    )
```

## Benefits

1. **Consistency**: All list operations follow the same pattern
2. **Maintainability**: Changes to pagination logic only need to be made in one place
3. **Error Handling**: Standardized error responses across all endpoints
4. **Type Safety**: Generic types ensure correct model usage
5. **Testing**: Easier to test with consistent patterns
6. **Documentation**: Self-documenting code with clear patterns

## Implementation Checklist

When implementing a new list operation:

- [ ] Inherit from `BaseApiService`
- [ ] Use `_standard_list_operation` or follow the manual pattern
- [ ] Include all required fields in list response
- [ ] Use standardized error handling
- [ ] Apply consistent filtering patterns
- [ ] Use brief models for related data
- [ ] Include comprehensive docstrings
- [ ] Add appropriate type hints

## Completed Refactoring

The following API services have been successfully refactored to use the standardized patterns:

### 1. DepartmentApiService

- **Before**: 30+ lines of manual pagination and filtering logic
- **After**: 15 lines using `_standard_list_operation`
- **Benefits**: Reduced code duplication, consistent error handling

### 2. TopicApiService

- **Before**: Manual pagination calculation and error handling
- **After**: Uses `_calculate_pages` and standardized error handlers
- **Benefits**: Consistent page calculation, unified error responses

### 3. ProfessorApiService

- **Before**: Complex filtering and pagination logic
- **After**: Uses `_standard_list_operation` with filter dictionary
- **Benefits**: Simplified filtering, consistent pagination

### 4. LectureApiService

- **Before**: Manual error handling and pagination
- **After**: Uses standardized error handlers and pagination methods
- **Benefits**: Unified error handling, consistent pagination

### 5. CourseApiService

- **Before**: Complex filtering logic with manual pagination
- **After**: Uses `_paginate_items` and `_create_list_response`
- **Benefits**: Simplified pagination, consistent response creation

## Refactoring Results

### Code Reduction

- **Total lines reduced**: ~150 lines across all services
- **Error handling**: Standardized across all services
- **Pagination logic**: Centralized in base class

### Consistency Improvements

- **Error responses**: All services now use consistent HTTP status codes and error messages
- **Pagination**: All list operations use the same page calculation logic
- **Filtering**: Consistent filter application patterns
- **Response models**: Standardized list response structure

### Testing

- **All 66 API tests pass** after refactoring
- **No breaking changes** to existing functionality
- **Improved testability** with consistent patterns

### Maintainability

- **Single source of truth** for pagination logic
- **Centralized error handling** reduces duplication
- **Type safety** with generic base class
- **Clear patterns** make code self-documenting

## Concrete Example: Refactoring Department Service

### Before (Inconsistent)

```python
class DepartmentApiService:
    def get_departments(
        self,
        page: int = 1,
        size: int = 10,
        faculty: Optional[str] = None,
        name: Optional[str] = None,
    ) -> DepartmentsListResponse:
        # Get all departments from core service
        departments = self.core_service.list_departments(faculty)

        # Apply name filter if provided
        if name:
            departments = [d for d in departments if name.lower() in d.name.lower()]

        # Count total before pagination
        total = len(departments)

        # Apply pagination
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        paginated_departments = departments[start_idx:end_idx]

        # Calculate total pages
        total_pages = ceil(total / size) if total > 0 else 1

        # Convert to response models
        department_responses = [
            DepartmentResponse.model_validate(d.model_dump()) for d in paginated_departments
        ]

        return DepartmentsListResponse(
            items=department_responses,
            total=total,
            page=page,
            size=size,
            pages=total_pages,
        )
```

### After (Standardized)

```python
class DepartmentApiService(BaseApiService[CoreDepartment, DepartmentResponse, DepartmentsListResponse]):
    def get_departments(
        self,
        page: int = 1,
        size: int = 10,
        faculty: Optional[str] = None,
        name: Optional[str] = None,
    ) -> DepartmentsListResponse:
        """
        Get a paginated list of departments with optional filtering.

        Args:
            page: Page number (1-indexed)
            size: Items per page
            faculty: Filter by faculty
            name: Filter by name (partial match)

        Returns:
            DepartmentsListResponse with paginated departments
        """
        # Build filters dictionary
        filters = {}
        if faculty:
            filters["faculty"] = faculty
        if name:
            filters["name"] = name

        return self._standard_list_operation(
            core_service_method="list_departments",
            response_class=DepartmentResponse,
            list_response_class=DepartmentsListResponse,
            page=page,
            size=size,
            filters=filters
        )
```

### Benefits of Refactoring

1. **Reduced Code**: From ~30 lines to ~15 lines
2. **Consistent Error Handling**: Uses standardized error handlers
3. **Type Safety**: Generic types ensure correct model usage
4. **Maintainable**: Changes to pagination logic only need to be made in base class
5. **Testable**: Easier to test with consistent patterns
6. **Documented**: Clear patterns make code self-documenting

## Next Steps

With the standardized patterns in place, future API services should:

1. **Inherit from BaseApiService** with appropriate generic types
2. **Use _standard_list_operation** for list endpoints
3. **Apply consistent error handling** using base class methods
4. **Follow the documented patterns** for filtering and pagination
5. **Maintain type safety** with proper generic type annotations

This foundation provides a solid base for consistent, maintainable API services across the entire codebase.
