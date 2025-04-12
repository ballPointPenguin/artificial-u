import { type Component, lazy } from 'solid-js'
import { Route } from '@solidjs/router'
import Layout from './components/Layout' // Import the Layout component

// Lazily load page components
const Home = lazy(() => import('./pages/Home'))
const About = lazy(() => import('./pages/About'))

const App: Component = () => {
  return (
    // Use Route with the Layout component
    <Route path="/" component={Layout}>
      {/* Nested routes rendered inside Layout's {props.children} */}
      <Route path="/" component={Home} />
      <Route path="/about" component={About} />
    </Route>
  )
}

export default App
