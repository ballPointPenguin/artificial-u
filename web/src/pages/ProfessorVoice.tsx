import { A, useParams } from '@solidjs/router'
import ProfessorVoice from '../components/professors/ProfessorVoice'

export default function ProfessorVoicePage() {
  const params = useParams<{ id: string }>()
  return (
    <main class="container mx-auto p-4">
      <A
        href={`/professors/${params.id}`}
        class="text-accent hover:text-accent/80 mb-4 inline-block"
      >
        &larr; Back to Professor
      </A>
      <ProfessorVoice />
    </main>
  )
}
