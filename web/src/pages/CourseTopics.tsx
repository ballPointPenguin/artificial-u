import { A, useParams } from '@solidjs/router'
import { type Component, createResource, Show } from 'solid-js'
import { courseService } from '../api/services/course-service.js'
import { CourseTopicsList } from '../components/topics/CourseTopicsList.jsx'
import { useTranslations } from '../i18n/index.js'

const CourseTopics: Component = () => {
  const t = useTranslations()
  const params = useParams()
  // Ensure params.id exists and is a valid number string before parsing
  const courseId = params.id ? Number.parseInt(params.id, 10) : Number.NaN

  // Check if courseId is a valid number before creating resources
  const isValidId = !Number.isNaN(courseId)

  const [courseData] = createResource(
    () => (isValidId ? courseId : null), // Pass null if ID is invalid
    courseService.getCourse
  )

  return (
    <div class="container mx-auto p-6">
      <Show
        when={isValidId}
        fallback={<div class="text-parchment-100">{t().courseDetail.invalidCourseId}</div>}
      >
        <Show
          when={!courseData.loading}
          fallback={
            <div class="text-parchment-200 font-serif p-4">{t().courseDetail.loadingCourse}</div>
          }
        >
          <Show
            when={courseData()}
            fallback={
              <div class="arcane-card p-6 text-center">{t().courseDetail.courseNotFound}</div>
            }
          >
            {(course) => (
              <div>
                <div class="flex items-center justify-between gap-2 mb-6">
                  <A
                    href={`/courses/${String(courseId)}`}
                    class="text-mystic-400 hover:text-mystic-300 transition-colors"
                  >
                    ← {t().courseDetail.backToCourse}
                  </A>
                </div>

                <div class="mb-6">
                  <h1 class="text-3xl font-display text-parchment-100 mb-2">
                    {t()
                      .courseDetail.topicsForCourse.replace('{code}', course().code)
                      .replace('{title}', course().title)}
                  </h1>
                  <p class="text-parchment-300 font-serif">
                    {t().courseDetail.manageTopicsDescription}
                  </p>
                </div>

                <CourseTopicsList courseId={courseId} />
              </div>
            )}
          </Show>
        </Show>
      </Show>
    </div>
  )
}

export default CourseTopics
