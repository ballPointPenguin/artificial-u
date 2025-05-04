import { type JSX, Show, createEffect } from 'solid-js'
import { Button } from './ui/Button'

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
  // Handle body overflow
  createEffect(() => {
    if (props.isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'auto'
    }

    return () => {
      document.body.style.overflow = 'auto'
    }
  })

  return (
    <Show when={props.isOpen}>
      <div class="fixed inset-0 z-50 overflow-y-auto bg-black bg-opacity-50 flex items-center justify-center">
        <div class="relative arcane-card max-w-md w-full mx-4 md:mx-auto shadow-xl">
          <div class="p-6">
            <h3 class="text-lg font-semibold mb-3 text-parchment-100">{props.title}</h3>
            <div class="mb-6 text-parchment-300">{props.message}</div>

            <div class="flex justify-end space-x-3">
              <Button
                type="button"
                variant="outline"
                onClick={props.onCancel}
                disabled={props.isConfirming}
              >
                {props.cancelText || 'Cancel'}
              </Button>
              <Button
                type="button"
                variant="primary"
                onClick={props.onConfirm}
                disabled={props.isConfirming}
                class="bg-red-800/50 hover:bg-red-700/50 border-red-500/50 text-red-100 hover:shadow-glow"
              >
                {props.isConfirming ? 'Processing...' : props.confirmText || 'Delete'}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </Show>
  )
}

export default ConfirmationModal
