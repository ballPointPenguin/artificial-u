# Course Topics Refactor Implementation

Refactor course data model to store weekly lecture topics in a structured `JSONB` field instead of relying solely on the free-text `syllabus` field. This will improve reliability for lecture generation.

## Tasks (amend as needed)

- [x] **Database Migration**: Add a `topics` column of type `JSONB` (nullable=True) to the `courses` table using Alembic.
- [x] **SQLAlchemy Model**: Update `artificial_u/models/database.py::CourseModel` to include the `topics` column (`sqlalchemy.dialects.postgresql.JSONB`).
- [x] **Pydantic Model**: Update `artificial_u/models/core.py::Course` to include `topics: Optional[List[Dict[str, Any]]]` (or a more specific nested Pydantic model).
- [x] **Repository**: Update `artificial_u/models/repositories/course.py` CRUD methods (`create`, `get`, `list`, `update`) to handle the new `topics` field.
- [x] **Course Service**: Modify `artificial_u/services/course_service.py`:
  - [x] Integrate topic generation using `get_course_topics_prompt`.
  - [x] Parse the generated topic structure (XML).
  - [x] Convert parsed topics to the JSON format for the `topics` field.
  - [x] Store topics in `course.topics` before saving.
- [ ] **Professor/Department Requirements**: Modify `artificial_u/services/course_service.py` to require that professor and department details are provided when creating a course.
- [ ] **Summary of Existing Courses**: Modify `artificial_u/services/course_service.py` to generate a summary of existing courses when creating a new course. This should be a list of courses within the same department. Each course should include the code, title, description, and the professor's name.
- [ ] **Limits**: Impose limits on the numbers of topics, weeks, and lectures per week.
- [ ] **Web UI**: Update the course creation/editing form in the web UI (`web/src/...`) to accommodate the new `topics` structure (display and potentially allow editing).
- [ ] **Testing**: Update unit and integration tests to reflect the new data structure and service logic.

## Future Tasks

- [ ] Consider adding database constraints or checks for the `topics` JSON structure.
- [ ] Explore more advanced JSONB querying if needed for future features.

## Implementation Plan

1. **Schema Change**: Introduce the `topics` JSONB column to the `courses` table via an Alembic migration.
2. **Model Updates**: Reflect the schema change in both SQLAlchemy and Pydantic models.
3. **Data Access Layer**: Ensure the Course repository correctly reads and writes the new `topics` field.
4. **Service Logic**:
    - Refactor `CourseService.create_course` to orchestrate topic generation, parsing, and storage.
    - Implement logic for handling cases where professor/department details are also requested for generation alongside the course. This likely involves calling `ProfessorService.generate_professor_profile` and potentially a similar function for departments, then associating the *generated data* (not saved IDs) with the course object being returned.
5. **API/UI**: Modify API endpoints and the frontend form to handle the structured topics.
6. **Testing**: Thoroughly test the entire flow from course creation (with/without generated prof/dept) through topic storage and retrieval.

### Relevant Files

- `alembic/versions/`: New migration file will be created here.
- `artificial_u/models/database.py`: Update `CourseModel`.
- `artificial_u/models/core.py`: Update `Course` Pydantic model.
- `artificial_u/models/repositories/course.py`: Update CRUD methods.
- `artificial_u/services/course_service.py`: Major logic changes for creation/generation.
- `artificial_u/services/professor_service.py`: Potentially minor adjustments if needed for coordinated generation.
- `artificial_u/prompts/courses.py`: Adjust prompts and potentially helper functions.
- `web/src/...`: Update relevant UI components for course form.
- `tests/`: Update relevant unit and integration tests.
