import * as Dialog from '@kobalte/core/dialog'
import type { JSX } from 'solid-js'
import { Button } from './Button'

interface ConfirmationModalProps {
  isOpen: boolean
  title: string
  message: JSX.Element
  confirmText?: string
  cancelText?: string
  onConfirm: () => void
  onCancel: () => void
  isConfirming?: boolean
}

const ConfirmationModal = (props: ConfirmationModalProps) => {
  const handleOpenChange = (isOpen: boolean) => {
    if (!isOpen) {
      // This ensures that if Kobalte closes the dialog (e.g., Esc key, overlay click),
      // the parent's state (which controls props.isOpen) is updated via onCancel.
      props.onCancel()
    }
  }

  return (
    <Dialog.Root open={props.isOpen} onOpenChange={handleOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay class="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm" />
        {/* Added a flex container for centering the Dialog.Content */}
        <div class="fixed inset-0 z-50 flex items-center justify-center p-4" vaul-overlay="">
          <Dialog.Content class="arcane-card relative max-w-md w-full shadow-xl rounded-lg">
            {/* `relative` is added to Dialog.Content if Dialog.CloseButton needs absolute positioning within it */}
            <div class="p-6">
              <Dialog.Title class="text-lg font-display font-semibold mb-3 text-primary">
                {props.title}
              </Dialog.Title>
              <Dialog.Description class="mb-6 text-muted font-serif">
                {props.message}
              </Dialog.Description>

              <div class="flex justify-end space-x-3">
                <Dialog.CloseButton
                  class={[
                    'rounded font-serif tracking-wider transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary ui-disabled:opacity-50 ui-disabled:cursor-not-allowed cursor-pointer', // base classes from ui/Button
                    'bg-transparent text-primary border border-primary hover:bg-primary/10', // outline variant classes
                    'px-4 py-2', // md size classes
                  ].join(' ')}
                  disabled={props.isConfirming}
                >
                  {props.cancelText || 'Cancel'}
                </Dialog.CloseButton>
                <Button
                  onClick={props.onConfirm}
                  disabled={props.isConfirming}
                  class="bg-danger-bg hover:bg-danger text-foreground border-danger-border hover:shadow-glow"
                  // Note: This applies md size by default from ui/Button. If other sizes needed, pass size prop.
                >
                  {props.isConfirming
                    ? 'Processing...'
                    : props.confirmText || 'Delete'}
                </Button>
              </div>
            </div>
            {/* Example of an explicit close button if needed, styled separately */}
            {/* <Dialog.CloseButton class="absolute top-3 right-3 p-1 rounded-full hover:bg-surface-hover">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5 text-muted">
                <path fill-rule="evenodd" d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10Zm3.53-12.03a.75.75 0 0 0-1.06-1.06L12 10.94l-2.47-2.47a.75.75 0 0 0-1.06 1.06L10.94 12l-2.47 2.47a.75.75 0 1 0 1.06 1.06L12 13.06l2.47 2.47a.75.75 0 1 0 1.06-1.06L13.06 12l2.47-2.47Z" clip-rule="evenodd" />
              </svg>
            </Dialog.CloseButton> */}
          </Dialog.Content>
        </div>
      </Dialog.Portal>
    </Dialog.Root>
  )
}

export default ConfirmationModal
