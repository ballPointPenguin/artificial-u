import { useNavigate } from '@solidjs/router'
import { onSettled } from 'solid-js'

export default function AdminIndex() {
  const navigate = useNavigate()

  onSettled(() => {
    navigate('/admin/jobs', { replace: true })
  })

  return null
}
