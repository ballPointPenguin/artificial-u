# Progressive Web App (PWA) Setup

This document describes the PWA capabilities that have been added to the Artificial University web application.

## Overview

The application is now configured as a Progressive Web App (PWA), which provides:

- **Installability**: Users can install the app on their devices (mobile and desktop)
- **Offline Support**: Core functionality works without an internet connection
- **App-like Experience**: Full-screen mode, custom splash screen, and native-like feel
- **Update Management**: Automatic service worker updates with user prompts
- **Performance**: Caching strategies for faster load times and reduced bandwidth usage

## Features Implemented

### 1. Web App Manifest

**File**: `web/public/manifest.json`

Defines the app's metadata including:

- App name and short name
- Theme colors matching the dark academia theme (`#5d4037`)
- Display mode (standalone for full-screen experience)
- Icon sizes for various devices (72x72 to 512x512)
- Orientation preference (portrait for mobile)
- Categories (education, productivity)

### 2. Service Worker Configuration

**File**: `web/vite.config.ts`

Configured with `vite-plugin-pwa` using Workbox for:

#### Caching Strategies

- **CacheFirst** for static assets (fonts, images)
  - Google Fonts: Cached for 365 days
  - Images: Cached for 30 days, up to 100 entries

- **NetworkFirst** for API calls
  - 10-second network timeout
  - Falls back to cache if network fails
  - Cached for 5 minutes, up to 50 entries

#### Service Worker Features

- Automatic precaching of all JS, CSS, HTML, and image files
- Runtime caching for external resources
- Development mode enabled for testing
- Prompt-based update strategy (user control)

### 3. Mobile Optimization

**File**: `web/index.html`

Added meta tags for:

- Proper viewport settings with safe area support
- Apple mobile web app capabilities
- Theme colors for address bar theming
- Apple touch icons
- PWA manifest link

### 4. Update & Install Prompts

**File**: `web/src/utils/pwa.tsx`

Two components for PWA management:

#### PWAUpdatePrompt

- Notifies users when a new version is available
- Provides "Update Now" or "Later" options
- Automatically reloads the app when updating

#### InstallPWAPrompt

- Displays installation prompt on supported browsers
- Shows when the app meets PWA criteria
- Can be dismissed for later

**Integration**: Both components are included in `Layout.tsx` and appear as fixed-position alerts.

### 5. Offline Fallback

**File**: `web/public/offline.html`

A standalone offline page that:

- Shows when users navigate to uncached pages while offline
- Provides a branded experience matching the app theme
- Auto-reloads when connectivity is restored
- Includes visual offline indicator

### 6. Icon Generation

**File**: `web/scripts/generate-icons.sh`

Bash script to generate PWA icons from the source SVG:

- Creates standard icons (72x72 to 512x512)
- Generates maskable icons for Android
- Uses ImageMagick or suggests online alternatives

### 7. CSS Animations

**File**: `web/src/index.css`

Added animations for PWA prompts:

- `slide-up`: Smooth entry animation for notifications
- `pulse`: Attention-grabbing animation for status indicators

## Usage

### Installation Testing

1. **Development Mode**:

   ```bash
   cd web
   pnpm dev
   ```

   The PWA will work in dev mode with the service worker enabled.

2. **Production Build**:

   ```bash
   cd web
   pnpm build
   pnpm preview
   ```

   Test the full PWA experience with optimized assets.

3. **Testing Installation**:
   - Open the app in Chrome/Edge (desktop or mobile)
   - Look for the install icon in the address bar
   - Or use the install prompt when it appears
   - On iOS Safari, use "Add to Home Screen" from the share menu

### Generating Icons

Before deploying, generate the app icons:

```bash
cd web
./scripts/generate-icons.sh
```

This requires ImageMagick. If not available, use an online tool:

- [PWA Builder Image Generator](https://www.pwabuilder.com/imageGenerator)
- [Real Favicon Generator](https://realfavicongenerator.net/)

Place generated icons in `web/public/icons/`.

### Testing Offline Functionality

1. Install the app or open in a browser
2. Open DevTools > Application > Service Workers
3. Check "Offline" to simulate no connectivity
4. Navigate around the app - cached pages should work
5. Try accessing an uncached page - should show offline.html

### Clearing Cache During Development

If you need to clear the service worker cache:

1. Open DevTools > Application > Service Workers
2. Click "Unregister" next to the service worker
3. Application > Storage > Clear site data
4. Reload the page

## Configuration

### Customizing Cache Strategies

Edit `web/vite.config.ts` to modify caching behavior:

```typescript
workbox: {
  runtimeCaching: [
    {
      urlPattern: /your-pattern/,
      handler: 'NetworkFirst', // or CacheFirst, StaleWhileRevalidate
      options: {
        cacheName: 'your-cache-name',
        expiration: {
          maxEntries: 50,
          maxAgeSeconds: 60 * 60 * 24, // 24 hours
        },
      },
    },
  ],
}
```

### Customizing the Manifest

Edit `web/public/manifest.json` to change:

- App name and description
- Theme colors
- Display mode
- Orientation
- Categories

### Customizing Update Behavior

In `web/vite.config.ts`, change `registerType`:

- `'prompt'`: Ask user before updating (current)
- `'autoUpdate'`: Update automatically without prompting
- `'skip'`: Don't register the service worker automatically

## Browser Support

### Full PWA Support

- Chrome/Edge 79+ (Android/Desktop)
- Safari 16.4+ (iOS/macOS)
- Firefox 108+ (Android/Desktop)
- Samsung Internet 12+

### Partial Support

- Safari iOS 11.3+ (Add to Home Screen, limited offline)
- Safari macOS 11.3+ (Limited PWA features)

### Not Supported

- Internet Explorer
- Older mobile browsers

## Deployment Considerations

### HTTPS Required

PWAs require HTTPS in production. Localhost works for development.

### Service Worker Scope

The service worker controls all routes under its scope (root `/`).

### Cache Invalidation

The service worker automatically updates when you deploy new code. Users get a prompt to reload.

### Asset Precaching

All built assets are automatically precached. Be mindful of total cache size.

### API Caching

API responses are cached for 5 minutes. Adjust in `vite.config.ts` if needed.

## Troubleshooting

### Service Worker Not Registering

- Check browser console for errors
- Ensure you're using HTTPS or localhost
- Clear browser cache and try again
- Check DevTools > Application > Service Workers

### Icons Not Showing

- Verify icons exist in `web/public/icons/`
- Check manifest.json icon paths
- Clear cache and reinstall the app
- Validate manifest in DevTools > Application > Manifest

### Update Prompt Not Appearing

- Check that `registerType` is set to `'prompt'`
- Verify the service worker detects changes
- Check browser console for PWA update logs

### Offline Mode Not Working

- Check DevTools > Application > Cache Storage
- Verify assets are being cached
- Check service worker status
- Review network requests in offline mode

## Future Enhancements

Potential improvements to consider:

1. **Push Notifications**: Notify users of new lectures or courses
2. **Background Sync**: Queue actions when offline, sync when online
3. **Share Target API**: Share content to the app from other apps
4. **App Shortcuts**: Add shortcuts to common actions
5. **Screenshots**: Add app screenshots to manifest for better install prompts
6. **Periodic Background Sync**: Automatically fetch new content
7. **File Handling**: Open specific file types with the app
8. **Web Share API**: Share lectures and courses from the app

## Resources

- [MDN PWA Guide](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps)
- [Vite PWA Plugin Docs](https://vite-pwa-org.netlify.app/)
- [Workbox Documentation](https://developer.chrome.com/docs/workbox/)
- [Web.dev PWA Checklist](https://web.dev/pwa-checklist/)
- [PWA Builder](https://www.pwabuilder.com/)

## Testing Checklist

Before deploying:

- [ ] Generate all required icon sizes
- [ ] Test installation on Chrome (desktop)
- [ ] Test installation on Chrome (Android)
- [ ] Test installation on Safari (iOS)
- [ ] Test offline functionality
- [ ] Test service worker updates
- [ ] Verify manifest is valid
- [ ] Check all icons load correctly
- [ ] Test on various screen sizes
- [ ] Verify theme colors match design
- [ ] Test update prompt workflow
- [ ] Test install prompt workflow
- [ ] Check Lighthouse PWA score (aim for 100)

## Maintenance

### Regular Tasks

1. Monitor service worker errors in production
2. Review and optimize cache strategies
3. Keep vite-plugin-pwa updated
4. Test PWA functionality after major updates
5. Monitor cache size and adjust limits
6. Review and update manifest as app evolves
