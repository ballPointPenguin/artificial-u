import { useNavigate } from '@solidjs/router'
import { createEffect } from 'solid-js'

export default function AdminIndex() {
  const navigate = useNavigate()

  createEffect(() => {
    navigate('/admin/jobs', { replace: true })
  })

  return null
}
