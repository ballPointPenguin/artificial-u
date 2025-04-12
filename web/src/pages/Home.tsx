import { Tabs } from '@kobalte/core'
import { For, Show, createResource, createSignal } from 'solid-js'
import ApiInfo from '../components/ApiInfo'

// Mock data for dashboard - In a real app, this would come from an API
const getDashboardData = async () => {
  // Simulate API loading time
  await new Promise((resolve) => setTimeout(resolve, 500))

  return {
    stats: {
      totalDepartments: 12,
      totalProfessors: 64,
      totalCourses: 186,
      totalStudents: 2450,
    },
    departments: [
      {
        id: 1,
        name: 'Computer Science',
        professorCount: 8,
        courseCount: 24,
        fundingPercentage: 92,
      },
      {
        id: 2,
        name: 'Mathematics',
        professorCount: 7,
        courseCount: 18,
        fundingPercentage: 84,
      },
      {
        id: 3,
        name: 'Physics',
        professorCount: 6,
        courseCount: 15,
        fundingPercentage: 76,
      },
      {
        id: 4,
        name: 'Biology',
        professorCount: 9,
        courseCount: 22,
        fundingPercentage: 88,
      },
    ],
    recentProfessors: [
      {
        id: 1,
        name: 'Dr. Alan Turing',
        department: 'Computer Science',
        courses: 3,
        rating: 4.8,
      },
      {
        id: 2,
        name: 'Dr. Marie Curie',
        department: 'Physics',
        courses: 2,
        rating: 4.9,
      },
      {
        id: 3,
        name: 'Dr. Richard Feynman',
        department: 'Physics',
        courses: 4,
        rating: 4.7,
      },
      {
        id: 4,
        name: 'Dr. Ada Lovelace',
        department: 'Mathematics',
        courses: 3,
        rating: 4.6,
      },
    ],
  }
}

const Home = () => {
  const [activeTabIndex, setActiveTabIndex] = createSignal('0')
  const [dashboardData] = createResource(getDashboardData)

  return (
    <div class="space-y-8">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 mb-2">
          University Dashboard
        </h1>
        <p class="text-gray-600">
          Welcome to Artificial University's administrative dashboard.
        </p>
      </div>

      {/* Stats Cards */}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Show when={dashboardData()}>
          {(data) => {
            // Make sure data is properly dereferenced
            const stats = data()
            return (
              <>
                <div class="bg-white rounded-lg shadow-sm overflow-hidden">
                  <div class="flex items-center">
                    <div class="bg-blue-500 p-4 flex items-center justify-center">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-6 w-6 text-white"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        aria-hidden="true"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                        />
                      </svg>
                    </div>
                    <div class="p-4 flex-1">
                      <p class="text-sm font-medium text-gray-500">
                        Departments
                      </p>
                      <p class="text-2xl font-semibold text-gray-900">
                        {stats.stats.totalDepartments}
                      </p>
                    </div>
                  </div>
                </div>

                <div class="bg-white rounded-lg shadow-sm overflow-hidden">
                  <div class="flex items-center">
                    <div class="bg-green-500 p-4 flex items-center justify-center">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-6 w-6 text-white"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        aria-hidden="true"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                        />
                      </svg>
                    </div>
                    <div class="p-4 flex-1">
                      <p class="text-sm font-medium text-gray-500">
                        Professors
                      </p>
                      <p class="text-2xl font-semibold text-gray-900">
                        {stats.stats.totalProfessors}
                      </p>
                    </div>
                  </div>
                </div>

                <div class="bg-white rounded-lg shadow-sm overflow-hidden">
                  <div class="flex items-center">
                    <div class="bg-purple-500 p-4 flex items-center justify-center">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-6 w-6 text-white"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        aria-hidden="true"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                        />
                      </svg>
                    </div>
                    <div class="p-4 flex-1">
                      <p class="text-sm font-medium text-gray-500">Courses</p>
                      <p class="text-2xl font-semibold text-gray-900">
                        {stats.stats.totalCourses}
                      </p>
                    </div>
                  </div>
                </div>

                <div class="bg-white rounded-lg shadow-sm overflow-hidden">
                  <div class="flex items-center">
                    <div class="bg-yellow-500 p-4 flex items-center justify-center">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-6 w-6 text-white"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        aria-hidden="true"
                      >
                        <path d="M12 14l9-5-9-5-9 5 9 5z" />
                        <path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998a12.078 12.078 0 01.665-6.479L12 14z" />
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998a12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222"
                        />
                      </svg>
                    </div>
                    <div class="p-4 flex-1">
                      <p class="text-sm font-medium text-gray-500">Students</p>
                      <p class="text-2xl font-semibold text-gray-900">
                        {stats.stats.totalStudents}
                      </p>
                    </div>
                  </div>
                </div>
              </>
            )
          }}
        </Show>
      </div>

      {/* Department and Professor Details Tabs */}
      <div class="bg-white rounded-lg shadow-md">
        <div class="p-6">
          <Tabs.Root
            value={activeTabIndex()}
            onChange={(value) => setActiveTabIndex(value)}
            class="w-full"
          >
            <Tabs.List
              class="flex space-x-1 border-b border-gray-200 mb-6"
              aria-label="Dashboard Sections"
            >
              <Tabs.Trigger
                value="0"
                class="px-4 py-2 text-gray-600 hover:text-blue-600 border-b-2 border-transparent data-[selected]:border-blue-600 data-[selected]:text-blue-600 font-medium"
              >
                Departments
              </Tabs.Trigger>
              <Tabs.Trigger
                value="1"
                class="px-4 py-2 text-gray-600 hover:text-blue-600 border-b-2 border-transparent data-[selected]:border-blue-600 data-[selected]:text-blue-600 font-medium"
              >
                Professors
              </Tabs.Trigger>
              <Tabs.Trigger
                value="2"
                class="px-4 py-2 text-gray-600 hover:text-blue-600 border-b-2 border-transparent data-[selected]:border-blue-600 data-[selected]:text-blue-600 font-medium"
              >
                API Status
              </Tabs.Trigger>
            </Tabs.List>

            <Tabs.Content value="0" class="space-y-6">
              <h3 class="text-lg font-medium text-gray-900">
                Department Overview
              </h3>
              <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                  <thead class="bg-gray-50">
                    <tr>
                      <th
                        scope="col"
                        class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        Department
                      </th>
                      <th
                        scope="col"
                        class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        Professors
                      </th>
                      <th
                        scope="col"
                        class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        Courses
                      </th>
                      <th
                        scope="col"
                        class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        Funding
                      </th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    <For each={dashboardData()?.departments || []}>
                      {(department) => (
                        <tr>
                          <td class="px-6 py-4 whitespace-nowrap">
                            <div class="text-sm font-medium text-gray-900">
                              {department.name}
                            </div>
                          </td>
                          <td class="px-6 py-4 whitespace-nowrap">
                            <div class="text-sm text-gray-500">
                              {department.professorCount}
                            </div>
                          </td>
                          <td class="px-6 py-4 whitespace-nowrap">
                            <div class="text-sm text-gray-500">
                              {department.courseCount}
                            </div>
                          </td>
                          <td class="px-6 py-4 whitespace-nowrap">
                            <div class="w-full bg-gray-200 rounded-full h-2.5">
                              <div
                                class="bg-blue-600 h-2.5 rounded-full"
                                style={{
                                  width: `${String(department.fundingPercentage)}%`,
                                }}
                              />
                              <div class="text-xs font-medium text-gray-700 mt-1">
                                {department.fundingPercentage}%
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </For>
                  </tbody>
                </table>
              </div>
            </Tabs.Content>

            <Tabs.Content value="1" class="space-y-6">
              <h3 class="text-lg font-medium text-gray-900">
                Recent Professors
              </h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <For each={dashboardData()?.recentProfessors || []}>
                  {(professor) => (
                    <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div class="flex justify-between">
                        <div>
                          <h4 class="text-lg font-medium text-gray-900">
                            {professor.name}
                          </h4>
                          <p class="text-sm text-gray-500">
                            {professor.department}
                          </p>
                        </div>
                        <div class="flex items-center bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs font-medium">
                          {professor.rating.toFixed(1)} / 5.0
                        </div>
                      </div>
                      <div class="mt-3 text-sm text-gray-600">
                        <p>Teaching {professor.courses} courses</p>
                      </div>
                    </div>
                  )}
                </For>
              </div>
            </Tabs.Content>

            <Tabs.Content value="2" class="space-y-6">
              <h3 class="text-lg font-medium text-gray-900">API Status</h3>
              <div class="max-w-xl">
                <ApiInfo />
              </div>
            </Tabs.Content>
          </Tabs.Root>
        </div>
      </div>
    </div>
  )
}

export default Home
