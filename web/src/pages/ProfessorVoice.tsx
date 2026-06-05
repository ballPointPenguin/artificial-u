import { A, useParams } from '@solidjs/router'
import ProfessorVoice from '../components/professors/ProfessorVoice'
import { useTranslations } from '../i18n'

export default function ProfessorVoicePage() {
  const params = useParams<{ id: string }>()
  const t = useTranslations()

  return (
    <main class="container mx-auto p-4">
      <A
        href={`/professors/${params.id}`}
        class="text-accent hover:text-accent/80 mb-4 inline-block"
      >
        {t().professorDetail.backToProfessor}
      </A>
      <ProfessorVoice />
    </main>
  )
}
