import { useNavigate } from '@solidjs/router'
import { Shuffle } from 'lucide-solid'
import { type Component, createSignal } from 'solid-js'
import { courseService } from '../../api/services/course-service.js'
import { MagicButton } from '../ui'

interface SurpriseMeProps {
  language: string
  tags: string[]
  label: string
  loadingLabel: string
}

/**
 * Pulls a random record from the crate: picks a random offset within the
 * current filters and navigates to that course.
 */
const SurpriseMe: Component<SurpriseMeProps> = (props) => {
  const navigate = useNavigate()
  const [isPicking, setIsPicking] = createSignal(false)

  const pickRandom = async () => {
    setIsPicking(true)
    try {
      const first = await courseService.listCourses({
        page: 1,
        size: 1,
        language: props.language,
        tags: props.tags,
      })
      if (first.total < 1) return
      const offset = Math.floor(Math.random() * first.total)
      const picked =
        offset === 0
          ? first
          : await courseService.listCourses({
              page: offset + 1,
              size: 1,
              language: props.language,
              tags: props.tags,
            })
      if (picked.items.length === 0) return
      navigate(`/courses/${String(picked.items[0].id)}`)
    } finally {
      setIsPicking(false)
    }
  }

  return (
    <MagicButton
      variant="ghost"
      onClick={() => void pickRandom()}
      isLoading={isPicking()}
      loadingText={props.loadingLabel}
    >
      <span class="inline-flex items-center gap-2">
        <Shuffle size={14} />
        {props.label}
      </span>
    </MagicButton>
  )
}

export default SurpriseMe
