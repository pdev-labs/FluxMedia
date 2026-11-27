# FluxMedia — Logo Guidelines

## 1. The logo

**Idea:** A play triangle whose lower edge lifts into a current, with a detached cyan wake. The mark keeps the
blue/cyan and the play/flow idea of the previous FluxMedia logo, but reduces it to two flat shapes and one
continuous curve.

**Versions:** horizontal (primary) · stacked · symbol-only · wordmark-only · app icon · favicon.

**Files:** `svg/` for screen and print masters, `png/` for ready-to-use raster exports, `favicon/` for the web icon
set. Use the SVG whenever the destination supports it.

## 2. Clear space

Keep a clear zone of **25% of the symbol height** on every side of the symbol. For the horizontal lockup, use the
**cap height of the wordmark** as the unit. The zone scales with the logo — never use a fixed distance.

Nothing else — text, rules, images, other logos — enters this zone.

## 3. Minimum size

| Version | Screen | Print |
| --- | --- | --- |
| Horizontal lockup | 160 px wide | 40 mm wide |
| Stacked lockup | 120 px wide | 30 mm wide |
| Wordmark only | 120 px wide | 30 mm wide |
| Symbol (full) | 32 px | 8 mm |
| Symbol (small cut) | 16 px | 5 mm |
| App icon | 48 dp (adaptive) | 12 mm |
| Favicon | 16 px | — |

Use `fluxmedia-symbol-small.svg` below 32 px: it drops the detached wake so the play shape stays clean.

## 4. Colour

| Name | HEX | RGB | CMYK (approx.) | Pantone (nearest) |
| --- | --- | --- | --- | --- |
| Flux Blue | `#0B6BFF` | 11 107 255 | 96 58 0 0 | 2727 C |
| Flux Cyan | `#00D4FF` | 0 212 255 | 100 17 0 0 | 306 C |
| Ink Navy | `#071A2F` | 7 26 47 | 85 45 0 82 | 539 C |
| White | `#FFFFFF` | 255 255 255 | 0 0 0 0 | — |
| Black | `#111111` | 17 17 17 | 0 0 0 93 | Black 6 C |

CMYK and Pantone values are starting points; confirm against a physical proof before a large print run.

**Approved pairs**

- Full colour on white or very light neutrals.
- White top + cyan wake + white wordmark on Ink Navy or near-black.
- Flux Blue monochrome on white.
- White monochrome on Ink Navy, Flux Blue or photography with a calm area.
- Black monochrome on white for one-colour print, embossing and etching.

Do not put the Flux Blue symbol on a mid-blue background; use the white version instead.

## 5. Typography

- **Wordmark:** Inter Bold (700), custom tight spacing, converted to outlines in every supplied file.
- **Brand and UI:** Inter for documents, slides and web where available; the system sans (Roboto on Android,
  `-apple-system`/Segoe UI on desktop) is the fallback. The app UI keeps the platform font.
- **Licence:** Inter is licensed under the SIL Open Font License 1.1. The outlined wordmark is part of the logo
  artwork; the font itself is not required to display it.

## 6. App icon and favicon

- **Background:** Ink Navy `#071A2F`.
- **Foreground:** white play shape + Flux Cyan wake.
- **Adaptive icon:** the symbol occupies 58 of the 108 dp canvas, inside the 66 dp safe zone:
  `brand/android/ic_launcher_foreground.xml` (also applied in the Android app repository).
- **Legacy launcher:** `brand/android/mipmap-mdpi` to `mipmap-xxxhdpi` at 48–192 px, plus round variants.
- **Play Store:** `fluxmedia-app-icon-store-512.png`, 512 × 512, full-bleed, no transparency.
- **Favicon:** the small cut (white play shape on an Ink Navy rounded tile) at 16, 32 and 48 px.

## 7. Don'ts

- Don't stretch, squash, rotate or skew the mark.
- Don't recolour outside the palette, add gradients, shadows, glows, outlines or bevels.
- Don't separate, reorder or resize the parts of a lockup.
- Don't place the full-colour mark on a busy photo without a container.
- Don't recreate the wordmark by typing it; use the outlined SVG.
- Don't use the symbol as a letter inside running text or as a bullet.
- Don't crop the symbol; keep the clear zone.

## 8. Files and contact

See [README.md](README.md) for the file index. Source and issues:
[github.com/pdev-labs/FluxMedia](https://github.com/pdev-labs/FluxMedia). The logo files are distributed with the
project under **GPL-3.0**; the FluxMedia name and logo are project trademarks, and the licence does not grant
trademark rights.
