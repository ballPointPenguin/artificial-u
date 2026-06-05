import { A } from '@solidjs/router'
import ProfessorDetail from '../components/professors/ProfessorDetail'
import { ShareButton } from '../components/ui'
import { useTranslations } from '../i18n'

export default function ProfessorDetailPage() {
  const t = useTranslations()

  return (
    <main class="container mx-auto p-4">
      <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
        <A href="/professors" class="text-accent hover:text-accent/80 inline-block">
          {t().professorDetail.backToProfessors}
        </A>
        <ShareButton
          url={`${window.location.origin}${window.location.pathname}`.replace(
            '/professors/',
            '/share/professors/'
          )}
        />
      </div>
      <ProfessorDetail />
    </main>
  )
}
