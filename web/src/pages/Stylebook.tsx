import { type Component, createSignal } from 'solid-js'
import { Alert } from '../components/ui/Alert'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardFooter, CardHeader } from '../components/ui/Card'
import { MagicButton } from '../components/ui/MagicButton'
import { Input } from '../components/ui/TextField'
import { Tooltip } from '../components/ui/Tooltip'

const Stylebook: Component = () => {
  const [inputValue, setInputValue] = createSignal('')
  const isInputInvalid = () => inputValue().length > 0 && inputValue().length < 3

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

      {/* TextField (Input) Section */}
      <section>
        <h2 class="text-2xl font-display text-accent mb-6 border-b border-border/50 pb-2">
          TextField (Input)
        </h2>
        <Card>
          <CardContent class="space-y-6">
            <Input
              label="Default Input"
              placeholder="Enter text..."
              helperText="This is helper text."
            />
            <Input
              label="Input with Error"
              placeholder="Enter at least 3 chars..."
              value={inputValue()}
              onChange={setInputValue}
              error={isInputInvalid() ? 'Must be at least 3 characters' : undefined}
              helperText="Example with validation."
            />
            <Input label="Disabled Input" placeholder="Cannot edit" disabled />
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

      {/* Add more component sections here as needed */}
    </div>
  )
}

export default Stylebook
