# Artificial-U Frontend

This directory contains the SolidJS frontend for the Artificial-U project.

## Setup

1. Navigate to the `web` directory:

   ```bash
   cd web
   ```

2. Install dependencies:

   ```bash
   pnpm install
   ```

## Development

To start the development server:

```bash
pnpm dev
```

This will typically start the server on `http://localhost:5173`.

### Available Commands

```bash
# Start development server
pnpm dev

# Build for production
pnpm build

# Preview production build locally
pnpm preview

# Lint code with ESLint
pnpm lint

# Format code with Biome
pnpm format
```

## Testing

This project uses Vitest for testing. The following test commands are available:

```bash
# Run tests
pnpm test

# Run tests in watch mode
pnpm test:watch

# Run tests with coverage
pnpm test:coverage
```

### Test Structure

- Component tests are located next to their component files with a `.test.tsx` extension
- Utility tests are located next to their utility files with a `.test.ts` extension
- Test utilities are located in `src/test/` directory
