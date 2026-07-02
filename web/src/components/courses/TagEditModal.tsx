import * as Dialog from '@kobalte/core/dialog'
import { createEffect, createSignal, For, Show } from 'solid-js'
import { courseService } from '../../api/services/course-service.js'
import type { Tag } from '../../api/types.js'
import { useTranslations } from '../../i18n'
import { Alert, Button, MagicButton } from '../ui'
import TagChip from './TagChip.jsx'

interface TagEditModalProps {
  isOpen: boolean
  courseId: number
  initialTags: Tag[]
  onSaved: (tags: Tag[]) => void
  onRegenerateQueued: () => void
  onCancel: () => void
}

const TagEditModal = (props: TagEditModalProps) => {
  const t = useTranslations()
  const [names, setNames] = createSignal<string[]>([])
  const [input, setInput] = createSignal('')
  const [error, setError] = createSignal('')
  const [isSaving, setIsSaving] = createSignal(false)
  const [isQueueing, setIsQueueing] = createSignal(false)

  // Reset draft state each time the modal opens
  createEffect(() => {
    if (props.isOpen) {
      setNames(props.initialTags.map((tag) => tag.name))
      setInput('')
      setError('')
    }
  })

  const handleOpenChange = (isOpen: boolean) => {
    if (!isOpen) props.onCancel()
  }

  const addFromInput = () => {
    const name = input().trim()
    if (!name) return
    const exists = names().some((n) => n.toLowerCase() === name.toLowerCase())
    if (!exists) setNames((prev) => [...prev, name])
    setInput('')
  }

  const removeName = (name: string) => {
    setNames((prev) => prev.filter((n) => n !== name))
  }

  const handleSave = async () => {
    setIsSaving(true)
    setError('')
    try {
      addFromInput()
      const saved = await courseService.updateCourseTags(props.courseId, names())
      props.onSaved(saved)
    } catch (err) {
      setError(err instanceof Error ? err.message : t().courseDetail.failedToSaveTags)
    } finally {
      setIsSaving(false)
    }
  }

  const handleRegenerate = async () => {
    setIsQueueing(true)
    setError('')
    try {
      await courseService.enqueueGenerateTags(props.courseId)
      props.onRegenerateQueued()
    } catch (err) {
      setError(err instanceof Error ? err.message : t().courseDetail.failedToSaveTags)
    } finally {
      setIsQueueing(false)
    }
  }

  return (
    <Dialog.Root open={props.isOpen} onOpenChange={handleOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay class="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm" />
        <div class="fixed inset-0 z-50 flex items-center justify-center p-4">
          <Dialog.Content class="arcane-card relative max-w-lg w-full shadow-xl rounded-lg">
            <div class="p-6">
              <Dialog.Title class="text-lg font-display font-semibold mb-3 text-primary">
                {t().courseDetail.tagsEditHeading}
              </Dialog.Title>
              <Dialog.Description class="mb-4 text-muted font-serif">
                {t().courseDetail.tagsEditDescription}
              </Dialog.Description>

              <Show when={error()}>
                <Alert variant="danger" class="mb-4">
                  {error()}
                </Alert>
              </Show>

              <div class="flex flex-wrap gap-2 mb-4 min-h-8">
                <For each={names()}>
                  {(name) => (
                    <TagChip
                      tag={{ id: 0, slug: name, name, language: '' }}
                      onRemove={() => {
                        removeName(name)
                      }}
                    />
                  )}
                </For>
              </div>

              <input
                type="text"
                value={input()}
                onInput={(e) => setInput(e.currentTarget.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    addFromInput()
                  }
                }}
                class="w-full p-3 mb-6 bg-surface border border-primary/20 rounded font-serif text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                placeholder={t().courseDetail.addTagPlaceholder}
                disabled={isSaving() || isQueueing()}
              />

              <div class="flex flex-wrap items-center justify-between gap-3">
                <MagicButton
                  variant="ghost"
                  onClick={() => void handleRegenerate()}
                  isLoading={isQueueing()}
                  loadingText={t().common.generating}
                >
                  {t().courseDetail.regenerateTags}
                </MagicButton>
                <div class="flex gap-3">
                  <Button variant="outline" onClick={props.onCancel} disabled={isSaving()}>
                    {t().common.cancel}
                  </Button>
                  <Button
                    variant="primary"
                    onClick={() => void handleSave()}
                    disabled={isSaving() || isQueueing()}
                  >
                    {isSaving() ? t().common.saving : t().common.save}
                  </Button>
                </div>
              </div>
            </div>
          </Dialog.Content>
        </div>
      </Dialog.Portal>
    </Dialog.Root>
  )
}

export default TagEditModal
