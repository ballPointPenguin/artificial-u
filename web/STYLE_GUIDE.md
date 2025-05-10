# UI, Styling, and Theming Guide

This document outlines the styling and theming architecture of the Artificial University web application. It aims to provide guidance for developers contributing to or debugging the UI.

## Core Philosophy

The styling approach prioritizes:

- **Utility-First CSS**: Leveraging Tailwind CSS v4 for rapid development and maintainable styles.
- **Themability**: A flexible system allowing for multiple visual themes, managed through CSS custom properties and JavaScript.
- **Modern CSS**: Utilizing modern CSS features via PostCSS.
- **Component-Based Structure**: Using SolidJS and Kobalte UI for a consistent component library.

## Core Technologies

- **Tailwind CSS v4**: The primary CSS framework.
  - Configuration: `tailwind.config.js`
  - Tailwind utilizes a utility-first approach. Styles are primarily applied directly in the HTML/JSX markup.
  - It is configured to use CSS variables for colors, fonts, etc., enabling dynamic theming.
- **PostCSS**: Used for CSS preprocessing.
  - Configuration: `postcss.config.mjs`
  - Key plugins include:
    - `postcss-color-hsl`: Allows using HSL color functions.
    - `postcss-preset-env`: Enables modern CSS features, transpiling them for broader compatibility (Stage 3 features are enabled).
- **BiomeJS**: Used for code formatting. Run `pnpm run format` to format.
- **ESLint**: Used for linting. Run `pnpm run lint` to check code. Configuration is in `./eslint.config.js`.

## Theming System

The application supports multiple themes, allowing for distinct visual appearances.

- **Theme Definition**:
  - Themes are defined in `src/utils/theme.ts`.
  - Each theme (e.g., `dark-academia`, `vaporwave`, `cosmic-horror`, `techno-occult`) specifies a set of properties, primarily HSL color strings for base colors (primary, secondary, accent, background, text, border, surface) and status colors (info, success, warning, danger, and their background/border variants).
  - The `themeProperties` object maps theme names to their respective `ThemeProperties` interface.
- **Theme Application**:
  - The current theme is managed by a SolidJS store created in `src/utils/theme.ts`.
  - The `applyThemeToDOM` function in `src/utils/theme.ts` dynamically adds a class like `theme-<name>` (e.g., `theme-dark-academia`) to the `<html>` element in `index.html`.
  - This class then activates the corresponding theme variables defined in `src/index.css`.
- **CSS Custom Properties (Variables)**:
  - Global theme variables are defined within the `@theme { ... }` block in `src/index.css`. These include font families, background images, shadows, and animations.
  - Theme-specific HSL base components (e.g., `--theme-bg-h`, `--theme-bg-s`, `--theme-bg-l`) are defined for each theme class (e.g., `.theme-dark-academia`, `.theme-vaporwave`) and for the `:root` (defaulting to dark-academia).
  - Semantic color variables (e.g., `--color-background`, `--color-primary`, `--color-info`) are derived using these HSL components, allowing them to change based on the active theme.
  - For example: `--color-background: hsl(var(--theme-bg-h) var(--theme-bg-s) var(--theme-bg-l));`
- **Accessing Theme Variables**:
  - In CSS: `var(--variable-name)`
  - In JavaScript: `getThemeVariable(variableName)` from `src/utils/theme.ts`.

## Semantic Colors

A consistent set of semantic color names are used throughout the application, derived from the active theme's base HSL values. These are defined in `src/index.css` and mapped in `tailwind.config.js`.

- **Base Semantic Colors**:
  - `primary`: For primary actions, important elements.
  - `secondary`: For secondary actions, alternative elements.
  - `accent`: For highlighting, links, or specific callouts.
  - `background`: The main page background color.
  - `foreground`: The primary text color.
  - `muted`: For less emphasized text or UI elements.
  - `border`: Default border color.
  - `surface`: Background color for cards, modals, or distinct UI surfaces.
- **Status Colors**: For alerts, notifications, and validation states. Each has a main color, a background variant (`-bg`), and a border variant (`-border`).
  - `info`
  - `success`
  - `warning`
  - `danger`

These semantic colors are then available as Tailwind utility classes (e.g., `bg-primary`, `text-foreground`, `border-danger-border`).

## Component Styling

- **Kobalte UI**: A UI library providing accessible and unstyled components.
  - Its Tailwind plugin (`@kobalte/tailwindcss`) is used to provide base styles and data attributes for styling.
- **Custom Components**: Located in `src/components/ui/`.
  - These components (e.g., `Button.tsx`, `Card.tsx`, `Alert.tsx`) are styled using Tailwind utility classes, leveraging the semantic color system.
  - Variants and states are handled through props and conditional class application.
- **Stylebook**: `src/pages/Stylebook.tsx` serves as a visual catalog and testing ground for UI components, showcasing their variants and how they respond to the current theme. This is an excellent resource for understanding available components and their intended appearance.

## Fonts

- Three main font families are defined in `src/index.css` and `tailwind.config.js`:
  - `--font-serif`: "Cormorant Garamond" (default body font)
  - `--font-display`: "Cinzel" (for headings)
  - `--font-sans`: "Inter" (for UI elements or specific sans-serif needs)
- Google Fonts are imported at the top of `src/index.css`.

## Global Styles

- Base HTML element styles, default link styles, and scrollbar styling are defined in the `@layer base` section of `src/index.css`.
- Custom utility classes like `text-shadow-arcane` and `text-shadow-golden` are defined using the `@utility` directive in `src/index.css`.

## Workflow & Best Practices

- **File Structure**:
  - Global styles and theme definitions: `src/index.css`
  - Theme logic: `src/utils/theme.ts`
  - Tailwind configuration: `tailwind.config.js`
  - PostCSS configuration: `postcss.config.mjs`
  - Reusable UI components: `src/components/ui/`
  - Page-specific components: `src/components/` (e.g., `FeaturedFaculty.tsx`)
  - Component showcase: `src/pages/Stylebook.tsx`
- **Development**:
  - Utilize the `Stylebook.tsx` page to experiment with and verify component styles across different themes.
  - Adhere to the `web-code` guidelines (ESM, TypeScript, Vite, SolidJS, `.js`/`.jsx` suffixes for local imports).
  - Remember the `greenfield` development philosophy: move fast, refactor aggressively, and prioritize iteration speed.
  - Run `pnpm run format` and `pnpm run lint` regularly.
- **Adding New Styles/Components**:
  - Prefer Tailwind utility classes for styling.
  - If new global styles or variables are needed, add them to `src/index.css`, considering how they fit into the existing theming system.
  - When creating new components, ensure they respect the semantic color system and are adaptable to different themes.

## Key Files for Reference

- `src/index.css`: Master CSS file defining themes, custom properties, global styles, and custom utilities.
- `src/utils/theme.ts`: JavaScript logic for managing and applying themes.
- `tailwind.config.js`: Tailwind CSS configuration, including mappings for semantic colors and fonts.
- `postcss.config.mjs`: PostCSS plugin configuration.
- `src/pages/Stylebook.tsx`: Visual gallery and testbed for UI components.
- `src/components/ui/`: Directory containing custom, reusable UI components.
- `index.html`: Initial theme class application on the `<html>` tag.

This guide should help in understanding and contributing to the UI and styling aspects of the application.
