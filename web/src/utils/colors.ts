/**
 * Converts an HSL color string (e.g., "30deg 25% 60%") to a CSS-parsable HSL string (e.g., "hsl(30deg, 25%, 60%)").
 * @param hslString The HSL string from themeProperties.
 * @returns A CSS HSL color string, or an empty string if parsing fails.
 */
export function hslStringToCss(hslString: string): string {
  if (!hslString || typeof hslString !== 'string') {
    // console.warn('Invalid hslString input:', hslString)
    return '' // Return a default or empty string for invalid input
  }

  // Regular expression to capture H, S, L parts. Assumes hue might or might not have 'deg'.
  // It expects format like "<hue>deg <saturation>% <lightness>%" or "<hue> <saturation>% <lightness>%"
  const parts = hslString.trim().split(/\s+/)

  if (parts.length === 3) {
    let [h, s, l] = parts

    // Ensure hue has 'deg' if it's just a number, otherwise assume it includes it or is a variable
    if (!isNaN(Number.parseFloat(h)) && !h.includes('deg')) {
      h = `${h}deg`
    }

    // Validate saturation and lightness are percentages
    if (!s.includes('%') || !l.includes('%')) {
      // console.warn('Invalid HSL string format (S or L missing %):', hslString)
      return ''
    }

    return `hsl(${h}, ${s}, ${l})`
  } else {
    // console.warn('Invalid HSL string format (not 3 parts):', hslString)
    return '' // Return empty or a default color if parsing fails
  }
}
