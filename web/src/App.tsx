import { Route } from '@solidjs/router'
import { type Component, lazy } from 'solid-js'
import Layout from './components/Layout'

// Lazily load page components
const Home = lazy(() => import('./pages/Home'))
const About = lazy(() => import('./pages/About'))
const Departments = lazy(() => import('./pages/Departments'))
const DepartmentDetail = lazy(() => import('./pages/DepartmentDetail'))
const Professors = lazy(() => import('./pages/Professors'))
const ProfessorDetail = lazy(() => import('./pages/ProfessorDetail'))
const Courses = lazy(() => import('./pages/Courses'))
const CourseDetail = lazy(() => import('./pages/CourseDetail'))
const Stylebook = lazy(() => import('./pages/Stylebook'))

const App: Component = () => {
  return (
    <Route path="/" component={Layout}>
      <Route path="/" component={Home} />
      <Route path="/about" component={About} />
      <Route path="/stylebook" component={Stylebook} />

      {/* Departments routes */}
      <Route path="/departments" component={Departments} />
      <Route path="/departments/:id" component={DepartmentDetail} />

      {/* Professor routes */}
      <Route path="/professors" component={Professors} />
      <Route path="/professors/:id" component={ProfessorDetail} />

      {/* Courses routes */}
      <Route path="/courses" component={Courses} />
      <Route path="/courses/:id" component={CourseDetail} />

      {/* Course Topics routes */}
      {/* Course Lectures routes */}
    </Route>
  )
}

export default App
