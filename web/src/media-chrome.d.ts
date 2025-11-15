// TypeScript declarations for Media Chrome custom elements
import 'solid-js'

declare module 'solid-js' {
  namespace JSX {
    interface IntrinsicElements {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      'media-controller': any
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      'media-control-bar': any
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      'media-play-button': any
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      'media-seek-backward-button': any
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      'media-seek-forward-button': any
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      'media-mute-button': any
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      'media-volume-range': any
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      'media-time-range': any
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      'media-time-display': any
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      'media-playback-rate-button': any
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      'media-loading-indicator': any
    }
  }
}
