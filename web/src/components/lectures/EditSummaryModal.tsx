import * as Dialog from '@kobalte/core/dialog'
import { createEffect, createSignal } from 'solid-js'
import { useTranslations } from '../../i18n'
import { Button } from '../ui/Button'

interface EditSummaryModalProps {
  isOpen: boolean
  initialSummary: string
  onSave: (newSummary: string) => Promise<void>
  onCancel: () => void
  isSaving?: boolean
}

const EditSummaryModal = (props: EditSummaryModalProps) => {
  const t = useTranslations()
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
  createEffect(() => {
    if (props.isOpen) {
      setEditedSummary(props.initialSummary)
    }
  })

  return (
    <Dialog.Root open={props.isOpen} onOpenChange={handleOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay class="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm" />
        <div class="fixed inset-0 z-50 flex items-center justify-center p-4" vaul-overlay="">
          <Dialog.Content class="arcane-card relative max-w-2xl w-full shadow-xl rounded-lg">
            <div class="p-6">
              <Dialog.Title class="text-lg font-display font-semibold mb-3 text-primary">
                {t().lectureDetail.editSummaryHeading}
              </Dialog.Title>
              <Dialog.Description class="mb-4 text-muted font-serif">
                {t().lectureDetail.editSummaryDescription}
              </Dialog.Description>

              <div class="mb-6">
                <textarea
                  value={editedSummary()}
                  onInput={(e) => setEditedSummary(e.currentTarget.value)}
                  class="w-full h-64 p-3 bg-surface border border-primary/20 rounded font-serif text-foreground resize-y focus:outline-none focus:ring-2 focus:ring-primary/50"
                  placeholder={t().lectureDetail.editSummaryPlaceholder}
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
                  {t().common.cancel}
                </Dialog.CloseButton>
                <Button
                  onClick={() => void handleSave()}
                  disabled={props.isSaving}
                  variant="primary"
                >
                  {props.isSaving ? t().common.saving : t().lectureDetail.form.saveChanges}
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
