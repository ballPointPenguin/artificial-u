import type { Component } from 'solid-js'
import ApiInfo from '../components/ApiInfo'

const Home: Component = () => {
  return (
    <div>
      <h2 class="text-2xl font-bold mb-6">Home Page</h2>
      <p class="mb-8">Welcome to Artificial University!</p>

      <div class="max-w-xl">
        <ApiInfo />
      </div>
    </div>
  )
}

export default Home
