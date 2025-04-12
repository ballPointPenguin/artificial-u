import { Route } from '@solidjs/router'
import { type Component, lazy } from 'solid-js'
import Layout from './components/Layout' // Import the Layout component

// Lazily load page components
const Home = lazy(() => import('./pages/Home'))
const About = lazy(() => import('./pages/About'))
const Departments = lazy(() => import('./pages/Departments'))
const DepartmentDetail = lazy(() => import('./pages/DepartmentDetail'))

const App: Component = () => {
  return (
    // Use Route with the Layout component
    <Route path="/" component={Layout}>
      {/* Nested routes rendered inside Layout's {props.children} */}
      <Route path="/" component={Home} />
      <Route path="/about" component={About} />

      {/* Academic routes */}
      <Route path="/academics">
        {/* Departments routes */}
        <Route path="/departments" component={Departments} />
        <Route path="/departments/:id" component={DepartmentDetail} />
      </Route>

      {/* Keep old direct routes for backward compatibility */}
      <Route path="/departments" component={Departments} />
      <Route path="/departments/:id" component={DepartmentDetail} />
    </Route>
  )
}

export default App
