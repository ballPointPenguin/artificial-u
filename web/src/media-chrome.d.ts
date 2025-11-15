// TypeScript declarations for Media Chrome custom elements
import 'solid-js'

declare module 'solid-js' {
  namespace JSX {
    interface IntrinsicElements {
      'media-controller': any
      'media-control-bar': any
      'media-play-button': any
      'media-seek-backward-button': any
      'media-seek-forward-button': any
      'media-mute-button': any
      'media-volume-range': any
      'media-time-range': any
      'media-time-display': any
      'media-playback-rate-button': any
      'media-loading-indicator': any
    }
  }
}
