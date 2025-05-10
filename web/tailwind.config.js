/** @type {import('tailwindcss').Config} */
import kobalteTailwind from '@kobalte/tailwindcss' // Import the plugin

export default {
  content: [
    './index.html', // Added index.html
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: 'var(--color-primary)',
        secondary: 'var(--color-secondary)',
        accent: 'var(--color-accent)',
        background: 'var(--color-background)',
        foreground: 'var(--color-foreground)',
        muted: 'var(--color-muted)',
        border: 'var(--color-border)',
        surface: 'var(--color-surface)',
        // Status Colors
        info: 'var(--color-info)',
        'info-bg': 'var(--color-info-bg)',
        'info-border': 'var(--color-info-border)',
        success: 'var(--color-success)',
        'success-bg': 'var(--color-success-bg)',
        'success-border': 'var(--color-success-border)',
        warning: 'var(--color-warning)',
        'warning-bg': 'var(--color-warning-bg)',
        'warning-border': 'var(--color-warning-border)',
        danger: 'var(--color-danger)',
        'danger-bg': 'var(--color-danger-bg)',
        'danger-border': 'var(--color-danger-border)',
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'sans-serif'],
        serif: ['var(--font-serif)', 'serif'],
        display: ['var(--font-display)', 'serif'],
      },
      // Explicitly define border colors as a workaround for the same HSL variable issue
      borderColor: ({ theme }) => ({
        DEFAULT: theme('colors.border'), // Default border uses the 'border' color defined above
        primary: theme('colors.primary'),
        secondary: theme('colors.secondary'),
        accent: theme('colors.accent'),
        background: theme('colors.background'),
        foreground: theme('colors.foreground'),
        muted: theme('colors.muted'),
        surface: theme('colors.surface'),
        // Status Colors for borders
        info: theme('colors.info'),
        'info-border': theme('colors.info-border'),
        success: theme('colors.success'),
        'success-border': theme('colors.success-border'),
        warning: theme('colors.warning'),
        'warning-border': theme('colors.warning-border'),
        danger: theme('colors.danger'),
        'danger-border': theme('colors.danger-border'),
      }),
    },
  },
  plugins: [
    kobalteTailwind(), // Add the plugin instance
  ],
}
