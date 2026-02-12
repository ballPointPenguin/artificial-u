import { createEffect, createResource, createSignal, For, on, Show } from 'solid-js'
import { departmentService } from '../api/services/department-service'
import { featuredService } from '../api/services/featured-service'
import { lectureService } from '../api/services/lecture-service'
import { professorService } from '../api/services/professor-service'
import type { Department, FeaturedItem, Lecture, LectureList, Professor } from '../api/types'
import { Button, Card } from '../components/ui'

type ItemType = 'lecture' | 'professor' | 'department'

// --- Search result types ---
interface SearchResult {
  id: number
  label: string
  sublabel: string
}

export default function AdminFeatured() {
  const [activeTab, setActiveTab] = createSignal<ItemType>('lecture')
  const [searchQuery, setSearchQuery] = createSignal('')
  const [searchResults, setSearchResults] = createSignal<SearchResult[]>([])
  const [searching, setSearching] = createSignal(false)
  const [successMsg, setSuccessMsg] = createSignal<string | null>(null)
  const [errorMsg, setErrorMsg] = createSignal<string | null>(null)

  // Resolved names for featured items: "lecture:42" -> "The Ethics of AGI"
  const [resolvedNames, setResolvedNames] = createSignal<Record<string, string>>({})

  // Fetch featured items for current tab
  const [featured, { refetch }] = createResource(
    () => activeTab(),
    (itemType) => featuredService.listFeatured({ item_type: itemType, language: 'en' })
  )

  // Resolve names whenever featured items change
  createEffect(
    on(featured, (items) => {
      if (!items || items.length === 0) return
      const tab = activeTab()
      for (const item of items) {
        const key = `${item.item_type}:${String(item.item_id)}`
        // Skip if already resolved
        if (resolvedNames()[key]) continue
        void resolveName(tab, item.item_id, key)
      }
    })
  )

  const resolveName = async (itemType: ItemType, itemId: number, key: string) => {
    try {
      let name = `#${String(itemId)}`
      if (itemType === 'lecture') {
        const lecture = await lectureService.getLecture(itemId)
        name = lecture.title
      } else if (itemType === 'professor') {
        const prof = await professorService.getProfessor(itemId)
        name = prof.name
      } else {
        const dept = await departmentService.getDepartment(itemId)
        name = dept.name
      }
      setResolvedNames((prev) => ({ ...prev, [key]: name }))
    } catch {
      setResolvedNames((prev) => ({ ...prev, [key]: `#${String(itemId)} (not found)` }))
    }
  }

  const getItemName = (item: FeaturedItem): string => {
    const key = `${item.item_type}:${String(item.item_id)}`
    return resolvedNames()[key] ?? `Loading #${String(item.item_id)}...`
  }

  // --- Flash messages ---
  const flash = (msg: string, isError = false) => {
    if (isError) {
      setErrorMsg(msg)
      setTimeout(() => setErrorMsg(null), 5000)
    } else {
      setSuccessMsg(msg)
      setTimeout(() => setSuccessMsg(null), 3000)
    }
  }

  // --- Search ---
  const handleSearch = async () => {
    const q = searchQuery().trim()
    if (!q) {
      setSearchResults([])
      return
    }

    setSearching(true)
    try {
      const tab = activeTab()
      let results: SearchResult[] = []

      if (tab === 'lecture') {
        const resp: LectureList = await lectureService.listLectures({
          page: 1,
          size: 20,
          search: q,
        })
        results = resp.items.map((l: Lecture) => ({
          id: l.id,
          label: l.title,
          sublabel: `ID ${String(l.id)} · ${l.audio_url ? 'Has audio' : 'No audio'}`,
        }))
      } else if (tab === 'professor') {
        const resp = await professorService.listProfessors({
          page: 1,
          size: 20,
          name: q,
        })
        results = resp.items.map((p: Professor) => ({
          id: p.id,
          label: p.name,
          sublabel: `ID ${String(p.id)}${p.specialization ? ` · ${p.specialization}` : ''}`,
        }))
      } else {
        const resp = await departmentService.listDepartments({
          page: 1,
          size: 20,
          name: q,
        })
        results = resp.items.map((d: Department) => ({
          id: d.id,
          label: d.name,
          sublabel: `ID ${String(d.id)} · ${d.code}`,
        }))
      }

      // Filter out items already featured
      const featuredIds = new Set((featured() ?? []).map((f: FeaturedItem) => f.item_id))
      results = results.filter((r) => !featuredIds.has(r.id))

      setSearchResults(results)
    } catch (err) {
      flash(err instanceof Error ? err.message : 'Search failed', true)
    } finally {
      setSearching(false)
    }
  }

  // --- Add featured ---
  const handleAdd = async (itemId: number) => {
    try {
      await featuredService.addFeatured({
        item_type: activeTab(),
        item_id: itemId,
        language: 'en',
      })
      flash(`Added to featured`)
      void refetch()
      // Remove from search results
      setSearchResults((prev) => prev.filter((r) => r.id !== itemId))
    } catch (err) {
      flash(err instanceof Error ? err.message : 'Failed to add', true)
    }
  }

  // --- Remove featured ---
  const handleRemove = async (featuredId: number) => {
    try {
      await featuredService.removeFeatured(featuredId)
      flash(`Removed from featured`)
      void refetch()
    } catch (err) {
      flash(err instanceof Error ? err.message : 'Failed to remove', true)
    }
  }

  // --- Update order ---
  const handleOrderChange = async (featuredId: number, newOrder: number) => {
    try {
      await featuredService.updateOrder(featuredId, newOrder)
      void refetch()
    } catch (err) {
      flash(err instanceof Error ? err.message : 'Failed to update order', true)
    }
  }

  // --- Tab labels ---
  const tabs: { key: ItemType; label: string }[] = [
    { key: 'lecture', label: 'Lectures' },
    { key: 'professor', label: 'Professors' },
    { key: 'department', label: 'Departments' },
  ]

  return (
    <div class="container mx-auto px-4 py-8 max-w-4xl">
      <h1 class="text-3xl font-display text-primary mb-2">Featured Content</h1>
      <p class="text-muted mb-8 font-serif">
        Manage which lectures, professors, and departments appear on the homepage.
      </p>

      {/* Flash messages */}
      <Show when={successMsg()}>
        <div class="mb-4 p-3 rounded bg-success-bg border border-success-border text-success">
          {successMsg()}
        </div>
      </Show>
      <Show when={errorMsg()}>
        <div class="mb-4 p-3 rounded bg-danger-bg border border-danger-border text-danger">
          {errorMsg()}
        </div>
      </Show>

      {/* Tabs */}
      <div class="flex gap-2 mb-6 border-b border-border pb-2">
        <For each={tabs}>
          {(tab) => (
            <button
              type="button"
              class={`px-4 py-2 rounded-t font-sans text-sm transition-colors ${
                activeTab() === tab.key
                  ? 'bg-primary text-on-primary font-semibold'
                  : 'text-muted hover:text-foreground hover:bg-surface'
              }`}
              onClick={() => {
                setActiveTab(tab.key)
                setSearchQuery('')
                setSearchResults([])
              }}
            >
              {tab.label}
            </button>
          )}
        </For>
      </div>

      {/* Current featured items */}
      <Card class="mb-8">
        <h2 class="text-xl font-display text-primary mb-4">
          Featured {tabs.find((t) => t.key === activeTab())?.label}
        </h2>

        <Show when={featured.loading}>
          <p class="text-muted text-sm">Loading...</p>
        </Show>

        <Show when={!featured.loading && (featured() ?? []).length === 0}>
          <p class="text-muted text-sm italic">
            No featured {activeTab()}s yet. Use the search below to add some.
          </p>
        </Show>

        <Show when={(featured() ?? []).length > 0}>
          <div class="space-y-2">
            <For each={featured()}>
              {(item: FeaturedItem) => (
                <div class="flex items-center gap-3 p-3 rounded border border-border bg-surface">
                  <div class="flex-1 min-w-0">
                    <div class="font-serif text-foreground truncate">{getItemName(item)}</div>
                    <div class="text-muted text-xs">ID {String(item.item_id)}</div>
                  </div>
                  <div class="flex items-center gap-1 shrink-0">
                    <label class="text-muted text-xs" for={`order-${String(item.id)}`}>
                      Order
                    </label>
                    <input
                      id={`order-${String(item.id)}`}
                      type="number"
                      class="arcane-input w-16 text-center text-sm py-1 px-2"
                      value={item.display_order}
                      onChange={(e) => {
                        const val = Number.parseInt(e.currentTarget.value, 10)
                        if (!Number.isNaN(val)) void handleOrderChange(item.id, val)
                      }}
                    />
                  </div>
                  <Button variant="danger" size="sm" onClick={() => void handleRemove(item.id)}>
                    Remove
                  </Button>
                </div>
              )}
            </For>
          </div>
        </Show>
      </Card>

      {/* Search and add */}
      <Card>
        <h2 class="text-xl font-display text-primary mb-4">
          Add {tabs.find((t) => t.key === activeTab())?.label}
        </h2>

        <div class="flex gap-2 mb-4">
          <input
            type="text"
            class="arcane-input flex-1"
            placeholder={`Search ${activeTab()}s by name or title...`}
            value={searchQuery()}
            onInput={(e) => setSearchQuery(e.currentTarget.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') void handleSearch()
            }}
          />
          <Button
            variant="secondary"
            onClick={() => void handleSearch()}
            disabled={searching() || !searchQuery().trim()}
          >
            {searching() ? 'Searching...' : 'Search'}
          </Button>
        </div>

        <Show when={searchResults().length > 0}>
          <div class="space-y-2">
            <For each={searchResults()}>
              {(result) => (
                <div class="flex items-center justify-between p-3 rounded border border-border bg-surface">
                  <div class="flex-1 min-w-0">
                    <div class="font-serif text-foreground truncate">{result.label}</div>
                    <div class="text-muted text-xs">{result.sublabel}</div>
                  </div>
                  <Button variant="primary" size="sm" onClick={() => void handleAdd(result.id)}>
                    Add
                  </Button>
                </div>
              )}
            </For>
          </div>
        </Show>

        <Show when={searchResults().length === 0 && searchQuery().trim() && !searching()}>
          <p class="text-muted text-sm italic">No results found.</p>
        </Show>
      </Card>
    </div>
  )
}
