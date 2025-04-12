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

const App: Component = () => {
  return (
    <Route path="/" component={Layout}>
      <Route path="/" component={Home} />
      <Route path="/about" component={About} />

      {/* Academic routes */}
      <Route path="/academics">
        {/* Departments routes */}
        <Route path="/departments" component={Departments} />
        <Route path="/departments/:id" component={DepartmentDetail} />

        {/* Professor routes */}
        <Route path="/professors" component={Professors} />
        <Route path="/professors/:id" component={ProfessorDetail} />
      </Route>
    </Route>
  )
}

export default App
