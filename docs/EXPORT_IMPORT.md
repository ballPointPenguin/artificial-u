# Course Export / Import

Admins can export a course to a zip and import it into this or another instance
(e.g. laptop → production).

## Export

`POST /api/v1/courses/{id}/export` (admin) enqueues an `export_course` job; the job
result holds the download URL, asset counts and any `warnings` (assets that couldn't
be fetched). The UI button is on the course detail page.

Archive layout (format `2.0`, see `artificial_u/services/course_bundle.py`):

```
manifest.json  course.json  professor.json  department.json  topics.json  lectures.json
assets/{course,professor,audio,transcripts,timelines,lecture_images}/...
```

Records carry an `assets` map (role → archive path). Lecture image timelines are
rewritten so slide URLs point at archive paths, making them portable. Ids in the
archive are source-instance ids and are only used for linking inside the archive.

## Import

Admin UI: **Admin → Import**. Two steps so conflicts can be resolved first:

1. `POST /api/v1/courses/import/analyze` (multipart `file`) stages the zip in the exports
   bucket under `imports/` and returns an `upload_key` plus a plan: course-code conflict,
   matching department / professor candidates / voices, connected courses, warnings.
2. `POST /api/v1/courses/import` `{upload_key, resolutions}` enqueues an `import_course`
   job (single attempt). Poll `GET /api/v1/jobs/{id}`.

Resolutions: `course_code` (`replace` | `rename` + `new_code` | `cancel`, required when the
code exists), `professor` (`reuse` + `professor_id` | `create`), `hidden`.

Matching is by natural key, never by id: department by code then name, professor by name
(reuse is the default if one exists), voices by provider id (recreated from archived
metadata when missing), connected courses by code, tags by name+language.
Imported records are attributed to the importing admin.

- **Replace** builds the new course under a temporary code, then deletes the old one and
  its assets and swaps the code in, so a failed import doesn't cost you the existing course.
  Assets that reuse the same storage keys are overwritten in place.
- **Rename** re-keys audio/images under the new code.
- A failed import rolls back the partial course, uploaded files, and any
  professor/department it created.

## Compatibility

Archives are `MAJOR.MINOR`. Importers accept any major ≤ the current one, ignore unknown
fields and default missing ones, so old exports keep importing as the model grows (format
`1.0` archives, which have no `assets` map, are upgraded on read). Newer-major archives are
rejected with a clear message. When changing the export, add fields as optional and bump
MINOR; only bump MAJOR for changes an older reader can't ignore.

## Deleting a course

`DELETE /api/v1/courses/{id}` refuses courses that still have lectures. Admins get
`DELETE /api/v1/courses/{id}/purge`, which also removes lectures, topics and stored files
(professors, departments and voices are kept). The course page uses it for admins.
