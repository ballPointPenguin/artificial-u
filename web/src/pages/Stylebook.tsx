import { type Component, createSignal } from 'solid-js'
import type { SelectOption } from '../components/ui'
import {
  Alert,
  Badge,
  Button,
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  ConfirmationModal,
  Form,
  FormActions,
  FormField,
  Input,
  MagicButton,
  Select,
  Textarea,
  Tooltip,
} from '../components/ui'

const Stylebook: Component = () => {
  const [inputValue, setInputValue] = createSignal('')
  const [anotherInputValue, setAnotherInputValue] = createSignal('Initial Value')
  const [numberValue, setNumberValue] = createSignal<number | null>(42)
  const [textareaValue, setTextareaValue] = createSignal('This is a textarea.')
  const [selectValue, setSelectValue] = createSignal<string | number | null>(null)
  const [selectDisabledValue, setSelectDisabledValue] = createSignal<string | number | null>('opt2')

  const isInputInvalid = () => inputValue().length > 0 && inputValue().length < 3

  // State for ConfirmationModal
  const [isModalOpen, setIsModalOpen] = createSignal(false)
  const [isProcessing, setIsProcessing] = createSignal(false)

  const handleModalConfirm = () => {
    console.log('Modal confirmed')
    setIsProcessing(true)
    setTimeout(() => {
      setIsProcessing(false)
      setIsModalOpen(false)
    }, 1500) // Simulate async action
  }

  const handleModalCancel = () => {
    console.log('Modal cancelled')
    setIsModalOpen(false)
    setIsProcessing(false) // Reset processing state if cancelled during processing
  }

  const sampleSelectOptions: SelectOption[] = [
    { value: 'opt1', label: 'Option 1' },
    { value: 'opt2', label: 'Option 2' },
    { value: 'opt3', label: 'Option 3 (Disabled)', disabled: true },
    { value: 4, label: 'Option 4 (Number)' },
  ]

  const handleFormSubmit = (e: SubmitEvent) => {
    e.preventDefault() // Already handled by Form component if onSubmit is provided
    console.log('Stylebook Form Submitted', {
      inputValue: inputValue(),
      anotherInputValue: anotherInputValue(),
      numberValue: numberValue(),
      textareaValue: textareaValue(),
      selectValue: selectValue(),
    })
  }

  return (
    <div class="p-8 space-y-12">
      <header>
        <h1 class="text-4xl font-display text-primary mb-2">Component Stylebook</h1>
        <p class="text-lg text-muted">
          A laboratory for experimenting with UI components and themes.
        </p>
      </header>

      {/* Buttons Section */}
      <section>
        <h2 class="text-2xl font-display text-accent mb-6 border-b border-border/50 pb-2">
          Buttons
        </h2>
        <Card>
          <CardContent class="space-y-4">
            <h3 class="text-xl font-semibold text-foreground/80">Standard Button Variants</h3>
            <div class="flex flex-wrap gap-4 items-center">
              <Button variant="primary">Primary Button</Button>
              <Button variant="secondary">Secondary Button</Button>
              <Button variant="outline">Outline Button</Button>
              <Button variant="ghost">Ghost Button</Button>
              <Button variant="link">Link Button</Button>
            </div>
            <h3 class="text-xl font-semibold text-foreground/80 mt-6">Button Sizes</h3>
            <div class="flex flex-wrap gap-4 items-center">
              <Button variant="primary" size="sm">
                Small Primary
              </Button>
              <Button variant="secondary" size="md">
                Medium Secondary
              </Button>
              <Button variant="outline" size="lg">
                Large Outline
              </Button>
            </div>
            <h3 class="text-xl font-semibold text-foreground/80 mt-6">Disabled States</h3>
            <div class="flex flex-wrap gap-4 items-center">
              <Button variant="primary" disabled>
                Primary Disabled
              </Button>
              <Button variant="secondary" disabled>
                Secondary Disabled
              </Button>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* MagicButton Section */}
      <section>
        <h2 class="text-2xl font-display text-accent mb-6 border-b border-border/50 pb-2">
          Magic Button
        </h2>
        <Card>
          <CardContent class="space-y-4">
            <div class="flex flex-wrap gap-4 items-center">
              <MagicButton>Magic Primary (Default)</MagicButton>
              <MagicButton variant="secondary">Magic Secondary</MagicButton>
              <MagicButton isLoading={true} loadingText="Conjuring...">
                Magic Loading
              </MagicButton>
              <MagicButton iconOnly={true}>Magic Icon</MagicButton>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Cards Section */}
      <section>
        <h2 class="text-2xl font-display text-accent mb-6 border-b border-border/50 pb-2">Cards</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card bordered hover>
            <CardHeader>
              <h3 class="text-xl font-semibold text-foreground">Bordered & Hover Card</h3>
            </CardHeader>
            <CardContent>
              <p class="text-muted">This card has a border and a hover shadow effect.</p>
            </CardContent>
            <CardFooter>
              <p class="text-sm text-accent">Footer Action</p>
            </CardFooter>
          </Card>
          <Card>
            <CardHeader>
              <h3 class="text-xl font-semibold text-foreground">Simple Card</h3>
            </CardHeader>
            <CardContent>
              <p class="text-muted">
                This is a simple card without explicit border or hover props.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Alerts Section */}
      <section>
        <h2 class="text-2xl font-display text-accent mb-6 border-b border-border/50 pb-2">
          Alerts
        </h2>
        <Card>
          <CardContent class="space-y-4">
            <Alert variant="default" title="Default Notice">
              This is a standard notification.
            </Alert>
            <Alert variant="info" title="Information">
              Your profile has been updated.
            </Alert>
            <Alert variant="success" title="Success!">
              Your changes were saved successfully.
            </Alert>
            <Alert variant="warning" title="Warning">
              Please check your input before submitting.
            </Alert>
            <Alert variant="danger" title="Error">
              Failed to process your request.
            </Alert>
          </CardContent>
        </Card>
      </section>

      {/* Badge Section */}
      <section>
        <h2 class="text-2xl font-display text-accent mb-6 border-b border-border/50 pb-2">
          Badges
        </h2>
        <Card>
          <CardContent class="flex flex-wrap gap-4 items-center">
            <Badge variant="default">Default</Badge>
            <Badge variant="outline">Outline</Badge>
            <Badge variant="secondary">Secondary</Badge>
            <Badge variant="success">Success</Badge>
            <Badge variant="danger">Danger</Badge>
          </CardContent>
        </Card>
      </section>

      {/* Tooltip Section */}
      <section>
        <h2 class="text-2xl font-display text-accent mb-6 border-b border-border/50 pb-2">
          Tooltips
        </h2>
        <Card>
          <CardContent class="flex flex-wrap gap-8 items-center">
            <Tooltip content="This is a tooltip.">
              <Button variant="outline">Hover Me (Top)</Button>
            </Tooltip>
            <Tooltip content="Another tooltip example." side="right">
              <Button variant="outline">Hover Me (Right)</Button>
            </Tooltip>
            <Tooltip
              content={
                <span>
                  With <b>HTML</b> content!
                </span>
              }
              side="bottom"
            >
              <Button variant="outline">Hover Me (Bottom)</Button>
            </Tooltip>
          </CardContent>
        </Card>
      </section>

      {/* Confirmation Modal Section */}
      <section>
        <h2 class="text-2xl font-display text-accent mb-6 border-b border-border/50 pb-2">
          Confirmation Modal
        </h2>
        <Card>
          <CardContent class="space-y-4">
            <p class="text-muted">
              Click the button below to test the Kobalte-based Confirmation Modal.
            </p>
            <Button variant="secondary" onClick={() => setIsModalOpen(true)}>
              Open Confirmation Modal
            </Button>
          </CardContent>
        </Card>
        <ConfirmationModal
          isOpen={isModalOpen()}
          title="Confirm Action"
          message={
            <p>
              Are you sure you want to proceed with this action? This cannot be undone.
              <br />
              <strong class="text-warning">Please consider the implications.</strong>
            </p>
          }
          confirmText="Yes, Proceed"
          cancelText="No, Go Back"
          onConfirm={handleModalConfirm}
          onCancel={handleModalCancel}
          isConfirming={isProcessing()}
        />
      </section>

      {/* Form Components Section */}
      <section>
        <h2 class="text-2xl font-display text-accent mb-6 border-b border-border/50 pb-2">
          Form Components
        </h2>
        <Card>
          <CardHeader>
            <h3 class="text-xl font-semibold text-foreground">Form Elements Showcase</h3>
          </CardHeader>
          <CardContent>
            <Form onSubmit={handleFormSubmit}>
              <FormField
                label="Text Input (Required)"
                name="textInput"
                required
                error={isInputInvalid() ? 'Min 3 chars' : null}
                helperText="Enter at least 3 characters."
              >
                <Input
                  name="textInput" // Name must match FormField for association
                  value={inputValue()}
                  onInput={(e) => setInputValue(e.currentTarget.value)}
                  placeholder="e.g., Professor Snape"
                  required
                />
              </FormField>

              <FormField label="Another Text Input" name="anotherInput">
                <Input
                  name="anotherInput"
                  value={anotherInputValue()}
                  onInput={(e) => setAnotherInputValue(e.currentTarget.value)}
                  placeholder="Some other text"
                />
              </FormField>

              <FormField label="Number Input" name="numberInput" helperText="Enter a number.">
                <Input
                  name="numberInput"
                  type="number"
                  value={numberValue() === null ? undefined : String(numberValue())}
                  onInput={(e) => {
                    const val = e.currentTarget.value
                    setNumberValue(val === '' ? null : Number(val))
                  }}
                  placeholder="e.g., 42"
                />
              </FormField>

              <FormField label="Disabled Input" name="disabledInput">
                <Input name="disabledInput" value="Cannot change me" disabled />
              </FormField>

              <FormField label="Textarea" name="textareaInput" helperText="Enter a longer text.">
                <Textarea
                  name="textareaInput"
                  value={textareaValue()}
                  onInput={(e) => setTextareaValue(e.currentTarget.value)}
                  placeholder="Describe your master plan..."
                  rows={4}
                />
              </FormField>

              <FormField label="Select Dropdown" name="selectInput" required>
                <Select
                  name="selectInput"
                  options={sampleSelectOptions}
                  value={selectValue()}
                  onChange={setSelectValue}
                  placeholder="-- Choose an Option --"
                  required
                />
              </FormField>
              <p class="text-sm text-muted mt-1 mb-4">Selected value: {selectValue() ?? 'None'}</p>

              <FormField label="Disabled Select" name="disabledSelect">
                <Select
                  name="disabledSelect"
                  options={sampleSelectOptions}
                  value={selectDisabledValue()}
                  onChange={setSelectDisabledValue} // Still allow change for testing UI reaction
                  placeholder="-- Cannot Choose --"
                  disabled
                />
              </FormField>

              <FormActions>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    console.log('Clear clicked')
                  }}
                >
                  Clear (Dummy)
                </Button>
                <MagicButton type="submit" isLoading={isProcessing()} loadingText="Submitting...">
                  Submit Form
                </MagicButton>
              </FormActions>
            </Form>
          </CardContent>
        </Card>
      </section>

      {/* Homepage Patterns Section */}
      <section>
        <h2 class="text-2xl font-display text-accent mb-6 border-b border-border/50 pb-2">
          Homepage Patterns
        </h2>

        {/* Section Labels */}
        <Card class="mb-6">
          <CardContent class="space-y-4">
            <h3 class="text-xl font-semibold text-foreground/80">Section Labels</h3>
            <p class="text-muted text-sm">
              Used above section headings for category context (e.g., "Featured Lectures").
            </p>
            <div class="space-y-4">
              <div>
                <span class="section-label">Recently Added</span>
                <h2 class="text-2xl font-display text-foreground">Latest Lectures</h2>
              </div>
              <div>
                <span class="section-label">Explore</span>
                <h2 class="text-2xl font-display text-foreground">Browse Departments</h2>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Stat Numbers */}
        <Card class="mb-6">
          <CardContent class="space-y-4">
            <h3 class="text-xl font-semibold text-foreground/80">Stat Counters</h3>
            <p class="text-muted text-sm">
              Large display numbers for the stats strip. Two sizes: default and small.
            </p>
            <div class="flex flex-wrap gap-12 items-end">
              <div class="text-center">
                <span class="stat-number animate-count-up">42</span>
                <p class="text-sm text-muted mt-1">Courses</p>
              </div>
              <div class="text-center">
                <span class="stat-number animate-count-up">186</span>
                <p class="text-sm text-muted mt-1">Lectures</p>
              </div>
              <div class="text-center">
                <span class="stat-number animate-count-up">73</span>
                <p class="text-sm text-muted mt-1">Hours of Audio</p>
              </div>
            </div>
            <div class="flex flex-wrap gap-8 items-end mt-6">
              <div class="text-center">
                <span class="stat-number-sm">42</span>
                <p class="text-xs text-muted mt-1">Small variant</p>
              </div>
              <div class="text-center">
                <span class="stat-number-sm">186</span>
                <p class="text-xs text-muted mt-1">Small variant</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tags / Department Labels */}
        <Card class="mb-6">
          <CardContent class="space-y-4">
            <h3 class="text-xl font-semibold text-foreground/80">Tags &amp; Department Labels</h3>
            <p class="text-muted text-sm">
              Colored tags for department labels on lecture cards. Teal and coral variants, plus
              standard badges for comparison.
            </p>
            <div class="flex flex-wrap gap-3 items-center">
              <span class="tag-teal inline-block rounded px-2.5 py-0.5 text-xs font-sans font-medium">
                Computer Science
              </span>
              <span class="tag-coral inline-block rounded px-2.5 py-0.5 text-xs font-sans font-medium">
                Philosophy
              </span>
              <span class="tag-teal inline-block rounded px-2.5 py-0.5 text-xs font-sans font-medium">
                Neuroscience
              </span>
              <span class="tag-coral inline-block rounded px-2.5 py-0.5 text-xs font-sans font-medium">
                Music
              </span>
              <Badge variant="default">Default Badge</Badge>
              <Badge variant="outline">Outline Badge</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Card Hover Lift */}
        <Card class="mb-6">
          <CardContent class="space-y-4">
            <h3 class="text-xl font-semibold text-foreground/80">Card Hover Lift</h3>
            <p class="text-muted text-sm">
              Cards with the <code class="text-accent">card-hover-lift</code> utility rise on hover.
            </p>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div class="card-hover-lift rounded-lg border border-border bg-surface p-4 cursor-pointer">
                <span class="tag-teal inline-block rounded px-2 py-0.5 text-xs font-sans font-medium mb-2">
                  Physics
                </span>
                <h4 class="font-display text-foreground">Quantum Mechanics 101</h4>
                <p class="text-sm text-muted mt-1">Dr. Richard Feynstone</p>
                <p class="text-xs text-muted mt-2">12 min</p>
              </div>
              <div class="card-hover-lift rounded-lg border border-border bg-surface p-4 cursor-pointer">
                <span class="tag-coral inline-block rounded px-2 py-0.5 text-xs font-sans font-medium mb-2">
                  Philosophy
                </span>
                <h4 class="font-display text-foreground">The Ethics of AGI</h4>
                <p class="text-sm text-muted mt-1">Prof. Helena Marsh</p>
                <p class="text-xs text-muted mt-2">18 min</p>
              </div>
              <div class="card-hover-lift rounded-lg border border-border bg-surface p-4 cursor-pointer">
                <span class="tag-teal inline-block rounded px-2 py-0.5 text-xs font-sans font-medium mb-2">
                  Neuroscience
                </span>
                <h4 class="font-display text-foreground">Memory &amp; Learning</h4>
                <p class="text-sm text-muted mt-1">Dr. Amara Osei</p>
                <p class="text-xs text-muted mt-2">22 min</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Section Backgrounds */}
        <Card class="mb-6">
          <CardContent class="space-y-4">
            <h3 class="text-xl font-semibold text-foreground/80">Section Backgrounds</h3>
            <p class="text-muted text-sm">
              Alternating section backgrounds for visual rhythm. Compare{' '}
              <code class="text-accent">bg-background</code>,{' '}
              <code class="text-accent">bg-surface</code>, and{' '}
              <code class="text-accent">bg-surface-alt</code>.
            </p>
            <div class="space-y-0 rounded-lg overflow-hidden border border-border">
              <div class="bg-background p-4">
                <p class="text-sm font-sans">bg-background — page default</p>
              </div>
              <div class="bg-surface p-4">
                <p class="text-sm font-sans">bg-surface — cards, elevated elements</p>
              </div>
              <div class="bg-surface-alt p-4">
                <p class="text-sm font-sans">bg-surface-alt — alternating sections</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* CTA Banner */}
        <Card class="mb-6">
          <CardContent class="space-y-4">
            <h3 class="text-xl font-semibold text-foreground/80">CTA Banner</h3>
            <p class="text-muted text-sm">
              A call-to-action panel with gradient background and border glow.
            </p>
          </CardContent>
        </Card>
        <div class="cta-banner mb-6">
          <div class="max-w-2xl">
            <h2 class="text-2xl font-display text-foreground mb-3">Create Your Own Courses</h2>
            <p class="text-muted mb-6">
              Pick any subject, customize your professor, and generate complete lecture series with
              AI — all with natural-sounding audio.
            </p>
            <div class="flex flex-wrap gap-3">
              <Button variant="primary">Get Started Free</Button>
              <Button variant="outline">Learn More</Button>
            </div>
          </div>
        </div>

        {/* Fade-in Animation */}
        <Card>
          <CardContent class="space-y-4">
            <h3 class="text-xl font-semibold text-foreground/80">Animations</h3>
            <p class="text-muted text-sm">
              <code class="text-accent">animate-fade-in</code> for section entrance,{' '}
              <code class="text-accent">animate-count-up</code> for stat numbers (shown above).
            </p>
            <div class="animate-fade-in rounded-lg border border-border bg-surface p-6">
              <p class="text-foreground">
                This element uses <code class="text-accent">animate-fade-in</code>.
              </p>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  )
}

export default Stylebook
