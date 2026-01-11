# PWA Features

This application is now a Progressive Web App (PWA) that can be installed on mobile devices including iPhones and Android phones.

## Features

### Installation
- **Add to Home Screen**: Users can install the app on their mobile devices
- **Standalone Mode**: Runs in fullscreen mode without browser UI
- **App Icon**: Custom fan control icon appears on home screen

### Mobile Optimization
- **iOS Support**: Full support for iPhone/iPad with Apple-specific meta tags
- **Android Support**: Native app-like experience on Android devices
- **Portrait Orientation**: Optimized for portrait mode usage
- **Theme Color**: Purple gradient theme color (#667eea) matches app design
- **Viewport Optimization**: Touch-optimized with no user scaling for app-like feel

### Offline Capabilities
- **Service Worker**: Caches essential assets for offline access
- **Network-First Strategy**: Always tries to fetch fresh data from API
- **Graceful Degradation**: Falls back to cached content when offline
- **API Error Handling**: Shows appropriate errors when network is unavailable

### Icons and Assets
The PWA includes comprehensive icon sets for all platforms:
- **Favicon**: 32x32 favicon.ico for browser tabs
- **Apple Touch Icon**: 180x180 for iOS devices
- **PWA Icons**: Multiple sizes (72x72, 96x96, 128x128, 144x144, 152x152, 192x192, 384x384, 512x512)
- **Maskable Icons**: Icons work with Android adaptive icons

## How to Install

### iPhone/iPad
1. Open the app in Safari
2. Tap the Share button (square with arrow)
3. Scroll down and tap "Add to Home Screen"
4. Tap "Add" in the top right
5. The app icon will appear on your home screen

### Android
1. Open the app in Chrome
2. Tap the menu button (three dots)
3. Tap "Install app" or "Add to Home Screen"
4. Confirm the installation
5. The app icon will appear on your home screen

### Desktop
1. Open the app in Chrome, Edge, or other PWA-compatible browser
2. Look for the install icon in the address bar
3. Click it and confirm installation
4. The app will open in its own window

## Technical Details

### Manifest (manifest.json)
- Defines app name, icons, and display settings
- Configures standalone display mode
- Sets theme and background colors
- Specifies portrait orientation preference

### Service Worker (sw.js)
- Implements intelligent caching strategy
- Network-first for API calls (always fresh data)
- Cache fallback for offline scenarios
- Automatic cache updates and cleanup

### Meta Tags
- Viewport configuration for mobile devices
- Theme color for browser UI
- Apple-specific tags for iOS integration
- Web app capability declarations

## Browser Compatibility

- ✅ Chrome (Desktop & Mobile)
- ✅ Edge (Desktop & Mobile)
- ✅ Safari (Desktop & Mobile)
- ✅ Firefox (Desktop & Mobile)
- ✅ Samsung Internet
- ✅ Opera

## Benefits

1. **Quick Access**: Launch directly from home screen
2. **App-Like Experience**: Fullscreen mode without browser UI
3. **Offline Support**: View cached interface when offline
4. **Fast Loading**: Cached assets load instantly
5. **Native Feel**: Behaves like a native mobile app
6. **Low Bandwidth**: Reduced data usage from caching
