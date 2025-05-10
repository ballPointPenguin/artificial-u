export default {
  plugins: {
    // Tailwind CSS is handled by the @tailwindcss/vite plugin.
    // It internally adds the necessary Tailwind PostCSS plugin.

    'postcss-color-hsl': {},
    'postcss-preset-env': {
      stage: 3, // Using Stage 3 for better modern CSS support
      features: {
        // custom-properties: false, // Let Tailwind and browsers handle custom props
        // 'nesting-rules': true, // If you decide to use CSS nesting
      },
    },
  },
}
