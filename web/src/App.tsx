import { Route } from '@solidjs/router'
import { type Component, lazy } from 'solid-js'
import { LoginPrompt, RequireAuth } from './auth/RequireAuth'
import { RequireRole } from './auth/RequireRole'
import Layout from './components/Layout'
import { useI18n } from './i18n/index.js'

// Fallback component for quickstart access denied
const QuickstartAccessDenied: Component = () => {
  const { t } = useI18n()
  return (
    <div class="container mx-auto p-4 text-center">
      <h2 class="text-2xl font-display mb-4">{t().quickstart.creatorAccessRequired}</h2>
      <p class="text-muted">{t().quickstart.creatorPrivilegesNeeded}</p>
    </div>
  )
}

// Lazily load page components
const Home = lazy(() => import('./pages/Home'))
const About = lazy(() => import('./pages/About'))
const Academics = lazy(() => import('./pages/Academics'))
const Departments = lazy(() => import('./pages/Departments'))
const DepartmentDetail = lazy(() => import('./pages/DepartmentDetail'))
const Professors = lazy(() => import('./pages/Professors'))
const ProfessorDetail = lazy(() => import('./pages/ProfessorDetail'))
const Courses = lazy(() => import('./pages/Courses'))
const CourseDetail = lazy(() => import('./pages/CourseDetail'))
const CourseTopics = lazy(() => import('./pages/CourseTopics'))
const TopicDetail = lazy(() => import('./pages/TopicDetail'))
const LectureDetail = lazy(() => import('./pages/LectureDetail'))
const LectureCreate = lazy(() => import('./pages/LectureCreate'))
const Profile = lazy(() => import('./pages/Profile'))
const Jobs = lazy(() => import('./pages/Jobs'))
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'))
const AdminSettings = lazy(() => import('./pages/AdminSettings'))
const AdminFeatured = lazy(() => import('./pages/AdminFeatured'))
const Stylebook = lazy(() => import('./pages/Stylebook'))
const Login = lazy(() => import('./pages/Login'))
const Quickstart = lazy(() => import('./pages/Quickstart'))

const App: Component = () => {
  return (
    <Route path="/" component={Layout}>
      <Route path="/" component={Home} />
      <Route path="/about" component={About} />
      <Route path="/academics" component={Academics} />
      <Route path="/stylebook" component={Stylebook} />
      <Route path="/login" component={Login} />

      {/* Quickstart route - requires creator role */}
      <Route
        path="/quickstart"
        component={() => (
          <RequireAuth fallback={<LoginPrompt />}>
            <RequireRole minRole="creator" fallback={<QuickstartAccessDenied />}>
              <Quickstart />
            </RequireRole>
          </RequireAuth>
        )}
      />

      {/* Profile route - requires authentication */}
      <Route
        path="/profile"
        component={() => (
          <RequireAuth fallback={<LoginPrompt />}>
            <Profile />
          </RequireAuth>
        )}
      />

      {/* Jobs route - requires admin role */}
      <Route
        path="/jobs"
        component={() => (
          <RequireAuth fallback={<LoginPrompt />}>
            <RequireRole
              minRole="admin"
              fallback={
                <div class="container mx-auto p-4 text-center">
                  Access denied. Admin role required.
                </div>
              }
            >
              <Jobs />
            </RequireRole>
          </RequireAuth>
        )}
      />

      {/* Admin Dashboard route - requires admin role */}
      <Route
        path="/admin"
        component={() => (
          <RequireAuth fallback={<LoginPrompt />}>
            <RequireRole
              minRole="admin"
              fallback={
                <div class="container mx-auto p-4 text-center">
                  Access denied. Admin role required.
                </div>
              }
            >
              <AdminDashboard />
            </RequireRole>
          </RequireAuth>
        )}
      />

      {/* Admin Settings route - requires admin role */}
      <Route
        path="/admin/settings"
        component={() => (
          <RequireAuth fallback={<LoginPrompt />}>
            <RequireRole
              minRole="admin"
              fallback={
                <div class="container mx-auto p-4 text-center">
                  Access denied. Admin role required.
                </div>
              }
            >
              <AdminSettings />
            </RequireRole>
          </RequireAuth>
        )}
      />

      {/* Admin Featured Content route - requires admin role */}
      <Route
        path="/admin/featured"
        component={() => (
          <RequireAuth fallback={<LoginPrompt />}>
            <RequireRole
              minRole="admin"
              fallback={
                <div class="container mx-auto p-4 text-center">
                  Access denied. Admin role required.
                </div>
              }
            >
              <AdminFeatured />
            </RequireRole>
          </RequireAuth>
        )}
      />

      {/* Departments routes */}
      <Route path="/departments" component={Departments} />
      <Route path="/departments/:id" component={DepartmentDetail} />

      {/* Professor routes */}
      <Route path="/professors" component={Professors} />
      <Route path="/professors/:id" component={ProfessorDetail} />

      {/* Courses routes */}
      <Route path="/courses" component={Courses} />
      <Route path="/courses/:id" component={CourseDetail} />
      <Route path="/courses/:id/topics" component={CourseTopics} />
      <Route path="/courses/:courseId/topics/:topicId" component={TopicDetail} />

      {/* Course Lectures routes */}
      <Route
        path="/courses/:courseId/topics/:topicId/lectures/new"
        component={() => (
          <RequireAuth fallback={<LoginPrompt />}>
            <LectureCreate />
          </RequireAuth>
        )}
      />
      <Route path="/courses/:courseId/lectures/:lectureId" component={LectureDetail} />
    </Route>
  )
}

export default App
