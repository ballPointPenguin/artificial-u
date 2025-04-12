import ProfessorList from '../components/professors/ProfessorList'

export default function ProfessorsPage() {
  return (
    <main class="container mx-auto p-4">
      <h1 class="text-3xl font-display mb-6 text-parchment-100 text-shadow-golden">
        Professors
      </h1>
      <ProfessorList />
    </main>
  )
}
