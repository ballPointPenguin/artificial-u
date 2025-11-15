# PWA Icons

This directory should contain the Progressive Web App icons in various sizes.

## Required Icons

The following icon sizes are needed (as defined in `/public/manifest.json`):

### Standard Icons

- icon-72x72.png
- icon-96x96.png
- icon-128x128.png
- icon-144x144.png
- icon-152x152.png
- icon-192x192.png
- icon-384x384.png
- icon-512x512.png

### Maskable Icons (for Android)

- icon-192x192-maskable.png
- icon-512x512-maskable.png

## Generating Icons

### Option 1: Using the Script (requires ImageMagick)

```bash
cd /home/user/artificial-u/web
./scripts/generate-icons.sh
```

Install ImageMagick first:

- Ubuntu/Debian: `sudo apt-get install imagemagick`
- macOS: `brew install imagemagick`

### Option 2: Online Generators

Use one of these online tools with the source PNG (`./AU-icon.png`):

1. **PWA Builder Image Generator**
   - URL: <https://www.pwabuilder.com/imageGenerator>
   - Upload the PNG
   - Download the generated icon pack
   - Extract to this directory

2. **Real Favicon Generator**
   - URL: <https://realfavicongenerator.net/>
   - Upload the PNG
   - Configure settings for PWA
   - Download and extract icons

### Option 3: Manual Creation

If you have design tools (Figma, Sketch, Photoshop):

1. Open `./AU-icon.png`
2. Export to PNG at each required size
3. For maskable icons, add 20% padding on all sides
4. Save files with the exact names listed above

## Design Guidelines

The icons should:

- Use the dark academia theme colors (#5d4037 background, #d4c5a0 foreground)
- Feature the "A" logo prominently
- Have a circular design matching the SVG
- For maskable icons, ensure the logo is centered with safe area padding

## Temporary Workaround

Until icons are generated, the app will:

- Fall back to the favicon.ico
- Display a browser warning about missing icons
- Still function as a PWA with limited install experience

The PWA will work, but installation prompts may not appear on all devices until proper PNG icons are provided.
