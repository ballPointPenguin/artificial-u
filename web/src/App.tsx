import type { RouteSectionProps } from '@solidjs/router'
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
const Browse = lazy(() => import('./pages/Browse'))
const Academics = lazy(() => import('./pages/Academics'))
const Departments = lazy(() => import('./pages/Departments'))
const DepartmentDetail = lazy(() => import('./pages/DepartmentDetail'))
const Professors = lazy(() => import('./pages/Professors'))
const ProfessorDetail = lazy(() => import('./pages/ProfessorDetail'))
const ProfessorVoice = lazy(() => import('./pages/ProfessorVoice'))
const Courses = lazy(() => import('./pages/Courses'))
const CourseDetail = lazy(() => import('./pages/CourseDetail'))
const CourseTopics = lazy(() => import('./pages/CourseTopics'))
const TopicDetail = lazy(() => import('./pages/TopicDetail'))
const LectureDetail = lazy(() => import('./pages/LectureDetail'))
const LectureCreate = lazy(() => import('./pages/LectureCreate'))
const Profile = lazy(() => import('./pages/Profile'))
const AdminLayout = lazy(() => import('./pages/admin/AdminLayout'))
const AdminIndex = lazy(() => import('./pages/admin/AdminIndex'))
const AdminUsers = lazy(() => import('./pages/admin/AdminUsers'))
const AdminSettings = lazy(() => import('./pages/admin/AdminSettings'))
const AdminFeatured = lazy(() => import('./pages/admin/AdminFeatured'))
const AdminJobs = lazy(() => import('./pages/admin/AdminJobs'))
const AdminLectures = lazy(() => import('./pages/admin/AdminLectures'))
const Search = lazy(() => import('./pages/Search'))
const AboutPrivacy = lazy(() => import('./pages/AboutPrivacy'))
const AboutTerms = lazy(() => import('./pages/AboutTerms'))
const AboutAiEthics = lazy(() => import('./pages/AboutAiEthics'))
const AboutPricing = lazy(() => import('./pages/AboutPricing'))
const AboutFaq = lazy(() => import('./pages/AboutFaq'))
const Stylebook = lazy(() => import('./pages/Stylebook'))
const Login = lazy(() => import('./pages/Login'))
const Quickstart = lazy(() => import('./pages/Quickstart'))

const AdminRoute: Component<RouteSectionProps> = (props) => (
  <RequireAuth fallback={<LoginPrompt />}>
    <RequireRole
      minRole="admin"
      fallback={
        <div class="container mx-auto p-4 text-center">Access denied. Admin role required.</div>
      }
    >
      <AdminLayout {...props} />
    </RequireRole>
  </RequireAuth>
)

const App: Component = () => {
  return (
    <Route path="/" component={Layout}>
      <Route path="/" component={Home} />
      <Route path="/about" component={About} />
      <Route path="/about/privacy" component={AboutPrivacy} />
      <Route path="/about/terms" component={AboutTerms} />
      <Route path="/about/ai-ethics" component={AboutAiEthics} />
      <Route path="/about/pricing" component={AboutPricing} />
      <Route path="/about/faq" component={AboutFaq} />
      <Route path="/academics" component={Academics} />
      <Route path="/search" component={Search} />
      <Route path="/browse" component={Browse} />
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
              {/* Canonical admin jobs route is /admin/jobs; keep /jobs for compatibility */}
              <AdminJobs />
            </RequireRole>
          </RequireAuth>
        )}
      />

      {/* Admin routes - requires admin role */}
      <Route path="/admin" component={AdminRoute}>
        <Route path="/" component={AdminIndex} />
        <Route path="/users" component={AdminUsers} />
        <Route path="/featured" component={AdminFeatured} />
        <Route path="/settings" component={AdminSettings} />
        <Route path="/jobs" component={AdminJobs} />
        <Route path="/lectures" component={AdminLectures} />
      </Route>

      {/* Departments routes */}
      <Route path="/departments" component={Departments} />
      <Route path="/departments/:id" component={DepartmentDetail} />

      {/* Professor routes */}
      <Route path="/professors" component={Professors} />
      <Route path="/professors/:id" component={ProfessorDetail} />
      <Route
        path="/professors/:id/voice"
        component={() => (
          <RequireAuth fallback={<LoginPrompt />}>
            <RequireRole
              minRole="creator"
              fallback={
                <div class="container mx-auto p-4 text-center">
                  Access denied. Creator role required.
                </div>
              }
            >
              <ProfessorVoice />
            </RequireRole>
          </RequireAuth>
        )}
      />

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
