# Metatheos Icons Setup

**Date:** 2025-12-29
**Version:** 0.5.0
**Status:** ✅ Complete

---

## Overview

Metatheos now has complete icon and branding integration across all platforms, including taskbar icons, window icons, app icons, and in-app logo display.

---

## Source Logo

**Location:** `/aequitas/assets/metatheos_logo.png`
**Format:** PNG
**Size:** 1024 x 1024 pixels
**File Size:** 1.2 MB
**Color Depth:** 8-bit/color RGB

This high-resolution logo is the source for all generated icons.

---

## Generated Icons

All platform-specific icons were generated using Tauri's built-in icon generator:

```bash
cd metatheos/metatheos-gui
cargo tauri icon /path/to/assets/metatheos_logo.png
```

### Icon Files Created

**Location:** `metatheos-gui/src-tauri/icons/`

#### Desktop Platforms (Linux, Windows, macOS)

**PNG Icons (Linux):**
- `32x32.png` - 2.4 KB - Taskbar icon (small)
- `64x64.png` - 8.3 KB - Taskbar icon (medium)
- `128x128.png` - 26.5 KB - App icon (standard)
- `128x128@2x.png` - 90.7 KB - App icon (HiDPI/Retina)
- `icon.png` - 347.7 KB - Primary icon (256x256)

**Windows Icons:**
- `icon.ico` - Multi-resolution ICO file
- `Square30x30Logo.png` through `Square310x310Logo.png` - Windows 10/11 tiles
- `StoreLogo.png` - Microsoft Store logo

**macOS Icons:**
- `icon.icns` - macOS icon bundle (all sizes)

#### Mobile Platforms (iOS, Android)

**iOS AppIcons:**
- `AppIcon-20x20@1x.png` through `AppIcon-512@2x.png`
- Complete set of all iOS icon sizes for different device resolutions

**Android Icons:**
- `mipmap-mdpi/` through `mipmap-xxxhdpi/` directories
- `ic_launcher.png` - Standard launcher icon
- `ic_launcher_round.png` - Circular launcher icon
- `ic_launcher_foreground.png` - Adaptive icon foreground

---

## Tauri Configuration

**File:** `metatheos-gui/src-tauri/tauri.conf.json`

### Icon References

```json
{
  "bundle": {
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ]
  }
}
```

**How It Works:**
- Tauri automatically selects the appropriate icon based on platform
- Linux uses PNG files
- Windows uses `icon.ico`
- macOS uses `icon.icns`
- High-DPI displays use `@2x` variants

---

## Web Display

### Public Assets

**Location:** `metatheos-gui/public/`

Two logo files are available for web display:

1. **`metatheos-icon.png`** (1.2 MB)
   - Used in HTML `<link rel="icon">`
   - Browser tab favicon
   - Bookmarks

2. **`metatheos-logo.png`** (1.2 MB)
   - Used in app UI (sidebar)
   - In-app branding
   - Can be used in documentation

### HTML Configuration

**File:** `metatheos-gui/index.html`

```html
<head>
  <link rel="icon" type="image/png" href="/metatheos-icon.png" />
  <title>Metatheos - Governance Engine</title>
</head>
```

**Browser Display:**
- Favicon appears in browser tab
- Shows in bookmarks
- Displays in history

---

## In-App Logo Display

### Sidebar Logo

**File:** `metatheos-gui/src/App.svelte`

The Metatheos logo is displayed in the sidebar header:

```svelte
<div class="p-6">
  <div class="flex items-center gap-3 mb-2">
    <img
      src="/metatheos-logo.png"
      alt="Metatheos Logo"
      class="w-10 h-10 rounded-lg"
    />
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
      Metatheos
    </h1>
  </div>
  <p class="text-sm text-gray-500 dark:text-gray-400 ml-13">Governance Engine</p>
</div>
```

**Visual Design:**
- Logo: 40x40 pixels (w-10 h-10)
- Rounded corners (rounded-lg)
- Positioned next to "Metatheos" text
- Consistent spacing with gap-3

**Result:**
```
┌────────────────────────────────┐
│  [LOGO]  Metatheos             │
│          Governance Engine     │
│                                │
│  📊 Dashboard                  │
│  📅 Daily                      │
│  🎯 Goals                      │
│  ...                           │
└────────────────────────────────┘
```

---

## Platform-Specific Display

### Linux (Arch)

**Taskbar/Panel:**
- Uses `32x32.png` or `64x64.png` (depends on panel size)
- Shows in application switcher (Alt+Tab)
- Appears in system tray

**Window Decoration:**
- Icon appears in window title bar
- Displayed in taskbar when app is running

**Application Launcher:**
- Uses `128x128.png` or higher resolution
- Shows in application menu/grid
- Gnome/KDE desktop integration

### Windows

**Taskbar:**
- Uses `icon.ico` (automatically selects appropriate size)
- Shows in taskbar when app is running
- Appears in Alt+Tab switcher

**Start Menu:**
- Square tile logos for Windows 10/11
- Multiple sizes for different tile sizes

**File Explorer:**
- Icon appears for Metatheos executable
- Shows in file associations

### macOS

**Dock:**
- Uses `icon.icns`
- Shows in Dock when app is running
- Appears in Launchpad

**Finder:**
- Icon appears in Applications folder
- Shows in Spotlight results

---

## Regenerating Icons

If you need to update the logo:

### 1. Update Source Logo

Replace `/aequitas/assets/metatheos_logo.png` with new design:
- **Requirements:**
  - PNG format
  - Minimum 512x512 pixels (1024x1024 recommended)
  - Square aspect ratio
  - Transparent background (optional but recommended)

### 2. Regenerate Icons

```bash
cd /path/to/aequitas/metatheos/metatheos-gui
cargo tauri icon /path/to/aequitas/assets/metatheos_logo.png
```

This will:
- Delete all existing icons in `src-tauri/icons/`
- Generate fresh icons for all platforms
- Preserve `tauri.conf.json` references

### 3. Update Public Assets

```bash
cp /path/to/assets/metatheos_logo.png public/metatheos-logo.png
cp /path/to/assets/metatheos_logo.png public/metatheos-icon.png
```

### 4. Rebuild

```bash
# Frontend
npm run build

# Full app
cargo build

# Or dev mode to test
cargo tauri dev
```

---

## Icon Sizes Reference

### Recommended Sizes for Source Logo

| Platform | Minimum | Recommended | Purpose |
|----------|---------|-------------|---------|
| Desktop  | 512x512 | 1024x1024   | All desktop icons |
| Web      | 256x256 | 512x512     | Favicon, web display |
| iOS      | 1024x1024 | 1024x1024 | App Store |
| Android  | 512x512 | 1024x1024   | Play Store |

### Generated Sizes

**Desktop:**
- 32x32 - Small taskbar
- 64x64 - Medium taskbar
- 128x128 - Standard app icon
- 256x256 - Large app icon
- 512x512 - HiDPI displays

**Windows Tiles:**
- 30x30, 44x44, 71x71, 89x89, 107x107
- 142x142, 150x150, 284x284, 310x310

**iOS:**
- 20x20, 29x29, 40x40, 60x60, 76x76
- @1x, @2x, @3x variants for Retina displays
- 83.5x83.5@2x for iPad Pro
- 512x512@2x for App Store

**Android:**
- mdpi: 48x48
- hdpi: 72x72
- xhdpi: 96x96
- xxhdpi: 144x144
- xxxhdpi: 192x192

---

## Testing Icon Display

### Browser (Dev Server)

```bash
cd metatheos-gui
npm run dev
```

**Check:**
- Browser tab shows Metatheos favicon
- Sidebar displays logo next to "Metatheos"

### Tauri Application

```bash
cd metatheos-gui
cargo tauri dev
```

**Check:**
- Window icon in title bar (Linux/Windows)
- Taskbar icon (all platforms)
- App switcher icon (Alt+Tab)
- Dock icon (macOS)
- Sidebar logo in app

### Production Build

```bash
cd metatheos-gui
cargo tauri build
```

**Linux (.deb, .AppImage):**
- Install package
- Check application menu icon
- Launch app and verify taskbar icon

**Windows (.exe, .msi):**
- Run installer
- Check Start Menu icon
- Launch app and verify taskbar icon

**macOS (.dmg, .app):**
- Install application
- Check Applications folder icon
- Launch and verify Dock icon

---

## Troubleshooting

### Icon Not Showing in Taskbar

**Problem:** App shows generic icon instead of Metatheos logo

**Solutions:**
1. Clear icon cache:
   ```bash
   # Linux
   gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor

   # Or rebuild
   cargo tauri build
   ```

2. Check `tauri.conf.json` has correct icon paths
3. Verify icons exist in `src-tauri/icons/`
4. Restart desktop environment

### Sidebar Logo Not Displaying

**Problem:** Broken image in sidebar

**Solutions:**
1. Check file exists: `metatheos-gui/public/metatheos-logo.png`
2. Verify path in `App.svelte`: `src="/metatheos-logo.png"`
3. Rebuild frontend: `npm run build`
4. Clear browser cache

### Favicon Not Showing

**Problem:** Browser tab shows default icon

**Solutions:**
1. Check `public/metatheos-icon.png` exists
2. Verify `index.html` has `<link rel="icon">`
3. Hard refresh browser (Ctrl+Shift+R)
4. Clear browser cache

### Icons Appear Blurry

**Problem:** Icons look pixelated or low quality

**Solutions:**
1. Regenerate from higher resolution source (1024x1024)
2. Ensure source logo is PNG (not compressed JPEG)
3. Use HiDPI variants (@2x icons)

---

## Best Practices

### Logo Design

✅ **Do:**
- Use high resolution (1024x1024 minimum)
- Square aspect ratio
- Transparent background for flexibility
- Simple, recognizable design
- Works well at small sizes (32x32)
- Sufficient contrast for dark/light themes

❌ **Don't:**
- Use text in logo (hard to read at small sizes)
- Complex gradients (may not scale well)
- Very thin lines (invisible at small sizes)
- Too many colors (simplicity scales better)

### File Organization

```
metatheos/
├── assets/
│   └── metatheos_logo.png           # Source (1024x1024)
│
├── metatheos-gui/
│   ├── public/
│   │   ├── metatheos-icon.png       # Web favicon
│   │   └── metatheos-logo.png       # In-app display
│   │
│   └── src-tauri/
│       ├── icons/                    # Generated icons
│       │   ├── 32x32.png
│       │   ├── 64x64.png
│       │   ├── 128x128.png
│       │   ├── icon.icns
│       │   ├── icon.ico
│       │   └── ... (all platforms)
│       │
│       └── tauri.conf.json          # Icon references
```

---

## Icon Checklist

Use this checklist when updating icons:

**Source Logo:**
- [ ] PNG format
- [ ] 1024x1024 pixels
- [ ] Square aspect ratio
- [ ] Transparent background (if applicable)
- [ ] Located at `/assets/metatheos_logo.png`

**Generation:**
- [ ] Run `cargo tauri icon /path/to/logo.png`
- [ ] Verify icons created in `src-tauri/icons/`
- [ ] Copy to `public/metatheos-logo.png`
- [ ] Copy to `public/metatheos-icon.png`

**Configuration:**
- [ ] `tauri.conf.json` references correct icon paths
- [ ] `index.html` has favicon link
- [ ] `App.svelte` displays logo in sidebar

**Testing:**
- [ ] `npm run build` succeeds
- [ ] `cargo build` succeeds
- [ ] Browser favicon displays correctly
- [ ] Sidebar logo displays correctly
- [ ] `cargo tauri dev` shows icon in window/taskbar
- [ ] Production build shows correct icons

---

## Version History

**v0.5.0** (2025-12-29)
- Initial icon setup
- Generated all platform icons from source logo
- Added sidebar logo display
- Configured favicon
- Complete platform coverage (Linux, Windows, macOS, iOS, Android)

---

## References

- [Tauri Icon Documentation](https://tauri.app/v1/guides/features/icons)
- [Icon Design Guidelines](https://developer.apple.com/design/human-interface-guidelines/app-icons)
- [Android Icon Guidelines](https://developer.android.com/google-play/resources/icon-design-specifications)

---

**Icons Setup Complete!** ✅

All Metatheos branding assets are now properly configured for all platforms.
