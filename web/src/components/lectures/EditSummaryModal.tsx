import * as Dialog from '@kobalte/core/dialog'
import { createSignal } from 'solid-js'
import { Button } from '../ui/Button'

interface EditSummaryModalProps {
  isOpen: boolean
  initialSummary: string
  onSave: (newSummary: string) => Promise<void>
  onCancel: () => void
  isSaving?: boolean
}

const EditSummaryModal = (props: EditSummaryModalProps) => {
  const [editedSummary, setEditedSummary] = createSignal(props.initialSummary)

  const handleOpenChange = (isOpen: boolean) => {
    if (!isOpen) {
      props.onCancel()
    }
  }

  const handleSave = async () => {
    await props.onSave(editedSummary())
  }

  // Reset the edited summary when the modal opens
  const handleAfterOpen = () => {
    setEditedSummary(props.initialSummary)
  }

  return (
    <Dialog.Root open={props.isOpen} onOpenChange={handleOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay class="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm" />
        <div class="fixed inset-0 z-50 flex items-center justify-center p-4" vaul-overlay="">
          <Dialog.Content
            class="arcane-card relative max-w-2xl w-full shadow-xl rounded-lg"
            onMount={handleAfterOpen}
          >
            <div class="p-6">
              <Dialog.Title class="text-lg font-display font-semibold mb-3 text-primary">
                Edit Lecture Summary
              </Dialog.Title>
              <Dialog.Description class="mb-4 text-muted font-serif">
                Edit the summary for this lecture. Changes will be saved immediately.
              </Dialog.Description>

              <div class="mb-6">
                <textarea
                  value={editedSummary()}
                  onInput={(e) => setEditedSummary(e.currentTarget.value)}
                  class="w-full h-64 p-3 bg-surface border border-primary/20 rounded font-serif text-foreground resize-y focus:outline-none focus:ring-2 focus:ring-primary/50"
                  placeholder="Enter lecture summary..."
                  disabled={props.isSaving}
                />
              </div>

              <div class="flex justify-end space-x-3">
                <Dialog.CloseButton
                  class={[
                    'rounded font-serif tracking-wider transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary ui-disabled:opacity-50 ui-disabled:cursor-not-allowed cursor-pointer',
                    'bg-transparent text-primary border border-primary hover:bg-primary/10',
                    'px-4 py-2',
                  ].join(' ')}
                  disabled={props.isSaving}
                >
                  Cancel
                </Dialog.CloseButton>
                <Button onClick={handleSave} disabled={props.isSaving} variant="primary">
                  {props.isSaving ? 'Saving...' : 'Save Changes'}
                </Button>
              </div>
            </div>
          </Dialog.Content>
        </div>
      </Dialog.Portal>
    </Dialog.Root>
  )
}

export default EditSummaryModal
