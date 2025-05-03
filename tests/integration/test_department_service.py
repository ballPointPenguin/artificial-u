"""
Integration tests for DepartmentService.
"""

from unittest.mock import MagicMock

import pytest

from artificial_u.models.core import Course, Professor
from artificial_u.models.repositories import RepositoryFactory
from artificial_u.services import DepartmentService
from artificial_u.utils import DepartmentNotFoundError, DependencyError


@pytest.fixture
def repository_factory():
    """Create a repository factory that uses the test database."""
    # The DATABASE_URL will be picked up from .env.test
    return RepositoryFactory()


@pytest.fixture
def department_service(repository_factory):
    """Create a DepartmentService with mocked professor and course services."""
    professor_service = MagicMock()
    course_service = MagicMock()
    return DepartmentService(
        repository_factory=repository_factory,
        professor_service=professor_service,
        course_service=course_service,
    )


@pytest.mark.integration
class TestDepartmentService:
    """Integration tests for DepartmentService."""

    def test_create_and_get_department(self, department_service):
        """Test creating and retrieving a department."""
        # Create a new department
        dept = department_service.create_department(
            name="Computer Science",
            code="CS",
            faculty="Engineering",
            description="Study of computation",
        )

        # Verify it was created with an ID
        assert dept.id is not None
        assert dept.name == "Computer Science"
        assert dept.code == "CS"

        # Retrieve the department and verify
        retrieved = department_service.get_department(dept.id)
        assert retrieved.id == dept.id
        assert retrieved.name == "Computer Science"
        assert retrieved.code == "CS"

    def test_update_department(self, department_service):
        """Test updating a department."""
        # Create a department
        dept = department_service.create_department(
            name="Economics", code="ECON", faculty="Business"
        )

        # Update the department
        updated = department_service.update_department(
            dept.id, {"name": "Economics and Finance", "code": "ECONFIN"}
        )

        # Verify updates
        assert updated.name == "Economics and Finance"
        assert updated.code == "ECONFIN"

        # Retrieve to confirm persistence
        retrieved = department_service.get_department(dept.id)
        assert retrieved.name == "Economics and Finance"
        assert retrieved.code == "ECONFIN"

    def test_list_departments(self, department_service):
        """Test listing departments with/without faculty filter."""
        # Create departments in different faculties
        department_service.create_department(name="Physics", code="PHYS", faculty="Science")
        department_service.create_department(name="Mathematics", code="MATH", faculty="Science")
        department_service.create_department(name="History", code="HIST", faculty="Arts")

        # List all departments
        all_depts = department_service.list_departments()
        assert len(all_depts) >= 3  # At least our 3 (could be more if DB has existing data)

        # List by faculty
        science_depts = department_service.list_departments(faculty="Science")
        assert len(science_depts) >= 2
        codes = [d.code for d in science_depts]
        assert "PHYS" in codes
        assert "MATH" in codes

        arts_depts = department_service.list_departments(faculty="Arts")
        assert len(arts_depts) >= 1
        assert any(d.code == "HIST" for d in arts_depts)

    def test_get_department_not_found(self, department_service):
        """Test getting a non-existent department raises appropriate error."""
        with pytest.raises(DepartmentNotFoundError):
            department_service.get_department("999999")

    def test_department_with_professors(self, department_service, repository_factory):
        """Test department with professors - creates professors, checks dependencies."""
        # Create a department
        dept = department_service.create_department(
            name="Chemistry", code="CHEM", faculty="Science"
        )

        # Create a professor in this department
        professor = Professor(
            name="Dr. Jane Smith",
            title="Associate Professor",
            department_id=dept.id,
            specialization="Organic Chemistry",
        )
        professor = repository_factory.professor.create(professor)

        # Get department professors
        professors = department_service.get_department_professors(dept.id)
        assert len(professors) >= 1
        assert any(p.id == professor.id for p in professors)

        # Test dependency protection - shouldn't be able to delete department with professors
        with pytest.raises(DependencyError):
            department_service.delete_department(dept.id)

    def test_department_with_courses(self, department_service, repository_factory):
        """Test department with courses - creates courses, checks dependencies."""
        # Create a department
        dept = department_service.create_department(name="Biology", code="BIO", faculty="Science")

        # Create a course in this department
        course = Course(
            code="BIO101",
            title="Introduction to Biology",
            department_id=dept.id,
            level="Undergraduate",
            credits=3,
            description="Basic biology concepts",
            lectures_per_week=2,
            total_weeks=14,
            topics=[{"name": "Cell Biology"}, {"name": "Genetics"}],
        )
        course = repository_factory.course.create(course)

        # Get department courses
        courses = department_service.get_department_courses(dept.id)
        assert len(courses) >= 1
        assert any(c.id == course.id for c in courses)

        # Test dependency protection - shouldn't be able to delete department with courses
        with pytest.raises(DependencyError):
            department_service.delete_department(dept.id)

    def test_delete_department(self, department_service):
        """Test deleting a department with no dependencies."""
        # Create a temporary department
        dept = department_service.create_department(
            name="Temp Dept",
            code="TEMP-DELETE",  # Use unique code to avoid conflicts
            faculty="Test",
        )

        # Delete it
        result = department_service.delete_department(dept.id)
        assert result is True

        # Verify it's gone
        with pytest.raises(DepartmentNotFoundError):
            department_service.get_department(dept.id)
