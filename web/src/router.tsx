import { createRouter, type RouteSectionProps } from '@solidjs/router'
import { type Component, lazy } from 'solid-js'
import { LoginPrompt, RequireAuth } from './auth/RequireAuth'
import { RequireRole } from './auth/RequireRole'
import Layout from './components/Layout'
import { useI18n } from './i18n/index.js'

const QuickstartAccessDenied: Component = () => {
  const { t } = useI18n()
  return (
    <div class="container mx-auto p-4 text-center">
      <h2 class="text-2xl font-display mb-4">{t().quickstart.creatorAccessRequired}</h2>
      <p class="text-muted">{t().quickstart.creatorPrivilegesNeeded}</p>
    </div>
  )
}

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
const AdminImport = lazy(() => import('./pages/admin/AdminImport'))
const Search = lazy(() => import('./pages/Search'))
const AboutPrivacy = lazy(() => import('./pages/AboutPrivacy'))
const AboutTerms = lazy(() => import('./pages/AboutTerms'))
const AboutAiEthics = lazy(() => import('./pages/AboutAiEthics'))
const AboutPricing = lazy(() => import('./pages/AboutPricing'))
const AboutFaq = lazy(() => import('./pages/AboutFaq'))
const Stylebook = lazy(() => import('./pages/Stylebook'))
const Login = lazy(() => import('./pages/Login'))
const Quickstart = lazy(() => import('./pages/Quickstart'))

type AnyRouteComponent = Component<RouteSectionProps>

const withAuth = (Page: AnyRouteComponent): AnyRouteComponent => {
  return (props) => (
    <RequireAuth fallback={<LoginPrompt />}>
      <Page {...props} />
    </RequireAuth>
  )
}

const withCreator = (Page: AnyRouteComponent): AnyRouteComponent => {
  return (props) => (
    <RequireAuth fallback={<LoginPrompt />}>
      <RequireRole minRole="creator" fallback={<QuickstartAccessDenied />}>
        <Page {...props} />
      </RequireRole>
    </RequireAuth>
  )
}

const AdminAccessDenied: Component = () => (
  <div class="container mx-auto p-4 text-center">Access denied. Admin role required.</div>
)

const withAdmin = (Page: AnyRouteComponent): AnyRouteComponent => {
  return (props) => (
    <RequireAuth fallback={<LoginPrompt />}>
      <RequireRole minRole="admin" fallback={<AdminAccessDenied />}>
        <Page {...props} />
      </RequireRole>
    </RequireAuth>
  )
}

const CreatorAccessDenied: Component = () => (
  <div class="container mx-auto p-4 text-center">Access denied. Creator role required.</div>
)

const withCreatorRole = (Page: AnyRouteComponent): AnyRouteComponent => {
  return (props) => (
    <RequireAuth fallback={<LoginPrompt />}>
      <RequireRole minRole="creator" fallback={<CreatorAccessDenied />}>
        <Page {...props} />
      </RequireRole>
    </RequireAuth>
  )
}

export const Router = createRouter({
  routes: [
    {
      path: '/',
      component: Layout,
      children: [
        { path: '/', component: Home },
        { path: '/about', component: About },
        { path: '/about/privacy', component: AboutPrivacy },
        { path: '/about/terms', component: AboutTerms },
        { path: '/about/ai-ethics', component: AboutAiEthics },
        { path: '/about/pricing', component: AboutPricing },
        { path: '/about/faq', component: AboutFaq },
        { path: '/academics', component: Academics },
        { path: '/search', component: Search },
        { path: '/browse', component: Browse },
        { path: '/stylebook', component: Stylebook },
        { path: '/login', component: Login },
        { path: '/quickstart', component: withCreator(Quickstart) },
        { path: '/profile', component: withAuth(Profile) },
        // Canonical admin jobs route is /admin/jobs; keep /jobs for compatibility
        { path: '/jobs', component: withAdmin(AdminJobs) },
        {
          path: '/admin',
          component: withAdmin(AdminLayout),
          children: [
            { path: '/', component: AdminIndex },
            { path: '/users', component: AdminUsers },
            { path: '/featured', component: AdminFeatured },
            { path: '/settings', component: AdminSettings },
            { path: '/jobs', component: AdminJobs },
            { path: '/lectures', component: AdminLectures },
            { path: '/import', component: AdminImport },
          ],
        },
        { path: '/departments', component: Departments },
        { path: '/departments/:id', component: DepartmentDetail },
        { path: '/professors', component: Professors },
        { path: '/professors/:id', component: ProfessorDetail },
        { path: '/professors/:id/voice', component: withCreatorRole(ProfessorVoice) },
        { path: '/courses', component: Courses },
        { path: '/courses/:id', component: CourseDetail },
        { path: '/courses/:id/topics', component: CourseTopics },
        { path: '/courses/:courseId/topics/:topicId', component: TopicDetail },
        {
          path: '/courses/:courseId/topics/:topicId/lectures/new',
          component: withAuth(LectureCreate),
        },
        { path: '/courses/:courseId/lectures/:lectureId', component: LectureDetail },
      ],
    },
  ],
})
