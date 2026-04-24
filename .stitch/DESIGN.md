# Design System Strategy: The Kinetic Vault

## 1. Overview & Creative North Star
The "Kinetic Vault" is the creative North Star for this design system. It moves away from the "flat" aesthetic of modern admin dashboards toward a high-density, institutional environment that feels heavy, secure, and technologically advanced. 

The system treats the UI not as a flat canvas, but as a sophisticated instrument carved from dark obsidian and layered with glass. By utilizing a high-density layout paired with sharp, precision-engineered corners (2px-4px), we evoke the feeling of a Bloomberg terminal reimagined for the modern era. We break the "template" look by favoring **intentional asymmetry** and **tonal layering** over standard grid lines, ensuring the trader feels immersed in a bespoke, professional-grade environment.

## 2. Colors & Surface Architecture
The color palette is engineered for prolonged focus. The deep-dark base minimizes eye strain, while high-chroma accents provide immediate cognitive shortcuts for financial signals.

### Color Mapping
- **Primary (`#bbc3ff`)**: Electric Blue. Reserved for "Information" and "Focus" states.
- **Secondary (`#4edea3`)**: Emerald Green. Used exclusively for "Buy," "Positive Delta," and "Growth."
- **Tertiary (`#ffb3ad`)**: Crimson Red. Used for "Sell," "Negative Delta," and "Risk."
- **Neutral/Surface**: Built on the `#0f131d` base, providing the "ink" for our dark canvas.

### The "No-Line" Rule
To achieve a premium, editorial feel, **1px solid borders are strictly prohibited for sectioning.** Boundaries between functional areas must be created through:
- **Tonal Shifts:** A `surface-container-low` panel sitting on a `surface` background.
- **Negative Space:** Using the spacing scale to define visual groups.
- **Inner Shadows:** Creating a "carved" effect that defines the edge without a stroke.

### Surface Hierarchy & Nesting
Treat the interface as a physical stack of materials.
1.  **The Base:** `surface` (#0f131d) — The bottom-most layer.
2.  **The Tray:** `surface-container-low` — Used for the main sidebar or navigation background.
3.  **The Instrument:** `surface-container` — The default for main terminal modules (Order Book, Charting).
4.  **The Highlight:** `surface-container-highest` — Used for active tabs or secondary modules within a container.

### The "Glass & Gradient" Rule
Floating panels (modals, context menus, tooltips) must use a **Glassmorphism** effect. Utilize a semi-transparent `surface-bright` with a 12px-20px backdrop blur. For primary CTAs, apply a subtle linear gradient from `primary` to `primary-container` to provide "soul" and depth that a flat color lacks.

## 3. Typography
The typography is a dual-engine system designed for maximum legibility of both intent (UI) and data (Numbers).

- **Sans-Serif (Inter):** Used for all UI labels, headlines, and instructional text. It is clean, modern, and invisible.
- **Monospace (JetBrains Mono / SF Mono):** Mandatory for all tickers, price points, trade volumes, and timestamps. This ensures that columns of numbers align perfectly, facilitating rapid scanning of data verticality.

### The Hierarchy
- **Display/Headline:** Use `headline-sm` (1.5rem) for main asset headers (e.g., "BTC/USDT").
- **Title:** `title-sm` (1rem) for module headers.
- **Body:** `body-sm` (0.75rem) is the workhorse for high-density terminal data.
- **Label:** `label-sm` (0.6875rem) for secondary metadata, using `on-surface-variant` to reduce visual noise.

## 4. Elevation & Depth
In a high-density environment, traditional drop shadows create "muddiness." This system uses **Tonal Layering** and **Ambient Insets**.

### The Layering Principle
Depth is achieved by "stacking" the surface tiers. To make a module stand out, do not add a shadow; instead, move it up one level in the surface-container hierarchy (e.g., place a `surface-container-high` card inside a `surface-container-low` layout).

### Ambient Shadows
When a floating effect is required (e.g., a dropdown), use an extra-diffused shadow:
- **Blur:** 24px-32px.
- **Opacity:** 8%.
- **Color:** A tinted version of the surface color, never pure black.

### The "Ghost Border" Fallback
If high-contrast accessibility requires a border, use the **Ghost Border**: the `outline-variant` token at 15% opacity. It provides a "hint" of an edge without breaking the "No-Line" rule.

## 5. Components

### Buttons
- **Primary:** Sharp corners (4px). Background: `primary-container`. Text: `on-primary-container`. High-contrast, bold weight.
- **Secondary/Tertiary:** No background. Use `ghost-borders` on hover only. 
- **Action Buttons (Buy/Sell):** Full-bleed `secondary_container` (Green) and `tertiary_container` (Red). These must be the most visually "heavy" elements on the screen.

### Data Grids & Lists
- **No Dividers:** Forbid horizontal lines between rows. 
- **Separation:** Use `surface-container-low` for alternating row backgrounds or simply rely on 4px vertical padding and `body-sm` typography to maintain a clean scan-line.
- **Density:** Tight vertical rhythm is encouraged. "Institutional" means seeing more data at once.

### Input Fields
- **The "Drilled-in" Look:** Use a 2px inner shadow to make input fields look recessed into the interface. 
- **State:** Active states should use a 1px `primary` border (the only exception to the no-line rule) to indicate focus.

### Ticker Chips
- Use `surface-container-highest` for the background with `0.25rem` (4px) rounding.
- Use the Monospace font for the value.
- Indicator: A small 4px circle of `secondary` (Up) or `tertiary` (Down) next to the value.

## 6. Do's and Don'ts

### Do
- **Do** use Monospace for every single numeric value on the screen.
- **Do** use high-contrast text (`on-surface`) for critical price data.
- **Do** embrace density; empty space should feel intentional, not like a "lack of content."
- **Do** use `surface-container-lowest` for the background of chart areas to give them a "sunken" feel.

### Don't
- **Don't** use rounded corners larger than 8px; keep the terminal sharp and professional.
- **Don't** use 100% opaque, high-contrast borders to separate modules.
- **Don't** use standard "Admin Panel" cards with white backgrounds.
- **Don't** use generic icons; use high-stroke-weight, technical iconography that matches the sharp-cornered aesthetic.
