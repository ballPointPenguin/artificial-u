import { A } from '@solidjs/router'
import ProfessorDetail from '../components/professors/ProfessorDetail'

export default function ProfessorDetailPage() {
  return (
    <main class="container mx-auto p-4">
      <A
        href="/academics/professors"
        class="text-mystic-400 hover:text-mystic-300 mb-4 inline-block"
      >
        &larr; Back to Professors
      </A>
      <ProfessorDetail />
    </main>
  )
}
