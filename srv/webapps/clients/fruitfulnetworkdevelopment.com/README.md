# fruitfulnetworkdevelopment.com
Website for Fruitful Network Development

## Mycite Framework
The Mycite concept separates profile data from presentation so any host can share and reinterpret the same information.

### Goals
1. Provide a standardized profile schema (Compendium, Oeuvre, Anthology) stored in `msn_<userId>.json` alongside the site.
2. Let creative frontends render that schema freely without layout constraints.
3. Enable third parties (directories, co-ops, marketplaces) to consume the same JSON and display consistent views.

### Rationale
- A single canonical JSON profile ensures interoperability across sites and future extensions.
- Free-form frontends can evolve without changing the underlying data contract.
- New sections (videos, certifications, links, grouped projects) can be added to the JSON without breaking existing renderers.

---

## Design Principles

This frontend follows a modular CSS architecture that combines multiple methodologies to create a maintainable, scalable, and performant codebase. The design principles below guide the organization and structure of all stylesheets and components.

### ITCSS (Inverted Triangle CSS)

**What ITCSS Asserts:**

ITCSS is a methodology for organizing CSS files in a specific order of increasing specificity and explicitness. The "inverted triangle" metaphor represents how CSS rules become more specific and explicit as you move down the layers. The methodology prevents specificity conflicts and ensures predictable cascade behavior by enforcing a strict layer order:

1. **Settings** - Design tokens (variables, colors, sizing) with no CSS output
2. **Tools** - Mixins, functions, and preprocessor tools
3. **Generic** - Reset/normalize styles (low specificity, broad scope)
4. **Elements** - Base HTML element styles (unclassed elements)
5. **Objects** - Layout patterns and structural classes (OOCSS)
6. **Components** - UI components and modules (BEM)
7. **Utilities** - Helper classes and overrides (highest specificity)

The key principle is that each layer can only be overridden by layers below it, preventing specificity wars and making the cascade predictable.

**Application in This Project:**

The CSS architecture strictly follows ITCSS layer order. All stylesheets are organized in `assets/css/` with `main.css` importing layers in the correct sequence:

- `settings.css` - All CSS custom properties (design tokens)
- `tools.css` - Reserved for future mixins/helpers
- `generic.css` - Universal box-sizing reset
- `elements.css` - Base styles for `html`, `body`, `button`, `input`
- `objects.css` - Layout patterns (`.o-container`, `.o-section`, `.o-main-content`)
- `components/*.css` - Individual component files (header, hero, footer, etc.)
- `utilities.css` - Utility classes and state classes

This structure ensures that design tokens are defined first, base styles are applied broadly, and component-specific styles can safely override without conflicts.

---

### SMACSS (Scalable and Modular Architecture for CSS)

**What SMACSS Asserts:**

SMACSS provides a framework for categorizing CSS rules into five distinct categories to improve maintainability and scalability:

1. **Base** - Default styles for HTML elements (resets, normalize, element defaults)
2. **Layout** - Major structural components that divide the page into sections
3. **Module** - Reusable, modular components that can exist independently
4. **State** - Styles that describe how modules or layouts look in a particular state
5. **Theme** - Visual styling that can be swapped to change the look and feel

SMACSS emphasizes that modules should be independent and portable, with state classes used to modify appearance or behavior. The methodology also promotes naming conventions that make the purpose of each rule clear.

**Application in This Project:**

SMACSS categories map to ITCSS layers in this project:

- **Base** → `generic.css` + `elements.css` (resets and element defaults)
- **Layout** → `objects.css` (OOCSS layout patterns)
- **Module** → `components/*.css` (BEM-named components)
- **State** → Hybrid approach: global `.is-*` classes for JS hooks/cross-component states, BEM modifiers for component-specific states
- **Theme** → `settings.css` (design tokens can be swapped to change themes)

State management follows SMACSS principles: global state classes like `.is-scrolled` and `.is-active` are used for JavaScript-driven states that affect multiple components, while BEM modifiers (e.g., `.c-hero--large`) handle component-specific variations.

---

### OOCSS (Object-Oriented CSS)

**What OOCSS Asserts:**

OOCSS promotes reusable, modular CSS by following two main principles:

1. **Separate Structure from Skin** - Visual properties (colors, borders, backgrounds) should be separated from structural properties (width, height, positioning, margins). This allows mixing and matching visual styles with structural patterns.

2. **Separate Container from Content** - Styles should not depend on their location in the DOM. A button should look the same whether it's in a header or footer. This prevents location-specific overrides and promotes reusability.

OOCSS encourages creating small, reusable "objects" or patterns that can be combined to build complex interfaces. These objects are typically layout-focused (media objects, grids, wrappers) rather than content-specific.

**Application in This Project:**

OOCSS is applied specifically to the **Objects layer** (ITCSS layer 5). Layout patterns are defined as reusable objects with the `.o-` prefix:

- `.o-main-content` - Main content wrapper
- `.o-section-container` - Container for full-width sections
- `.o-section` - Individual section block
- `.o-container` - Generic content container with max-width and padding
- `.o-container--grid` - Grid variant of container
- `.o-container--center` - Centered variant of container

These objects are structure-only and contain no visual styling (colors, backgrounds). They can be combined with any component to create layouts. Components (BEM) handle visual styling and content-specific behavior, while objects handle structure and positioning.

This separation ensures that layout patterns remain reusable and don't create "shadow versions" of the same object in different contexts.

---

### BEM (Block Element Modifier)

**What BEM Asserts:**

BEM is a naming convention for CSS classes that makes them more readable, maintainable, and self-documenting. The methodology structures class names into three parts:

1. **Block** - A standalone, meaningful component (e.g., `button`, `menu`, `card`)
2. **Element** - A part of a block that has no standalone meaning (e.g., `button__icon`, `menu__item`)
3. **Modifier** - A variation of a block or element (e.g., `button--primary`, `menu__item--active`)

BEM syntax: `.block__element--modifier`

Key principles:
- Blocks are independent and can be moved anywhere
- Elements belong to their block and cannot be used independently
- Modifiers represent different states or variations
- No nesting in class names (flat structure)
- Classes should be self-documenting

**Application in This Project:**

All UI components use BEM naming with the `.c-` prefix (for "component") to distinguish from objects:

- `.c-header` (block)
  - `.c-header__inner` (element)
  - `.c-header__left` (element)
  - `.c-header__nav-button` (element)
  - `.c-header__nav-button.is-active` (element with state)

- `.c-hero` (block)
  - `.c-hero__content` (element)
  - `.c-hero__title` (element)

- `.c-table` (block)
  - `.c-table__inner` (element)
  - `.c-table__table` (element)
  - `.c-table__header` (element)

Each component is in its own file (`components/header.css`, `components/hero.css`, etc.), making it easy to locate and modify component-specific styles. BEM naming ensures that styles are scoped to their component and won't accidentally affect other parts of the page.

Modifiers are used for component variations (e.g., `.c-divider--vision`), while global state classes (`.is-*`) are used for JavaScript-driven states that may affect multiple components.

---

### Progressive Enhancement

**What Progressive Enhancement Asserts:**

Progressive Enhancement is a web design strategy that starts with a solid foundation of basic functionality that works for all users, then adds enhanced features for users with more capable browsers or devices. The core principles are:

1. **Start with Content** - HTML should contain all essential content and structure
2. **Add Presentation** - CSS enhances the visual presentation but doesn't break functionality if unavailable
3. **Add Behavior** - JavaScript enhances interactivity but doesn't break core functionality if unavailable

The strategy ensures that:
- Content is accessible to all users, regardless of browser capabilities
- Basic functionality works without JavaScript
- Enhanced features gracefully degrade when JavaScript is disabled
- The site works on any device or browser, from basic to advanced

This approach prioritizes accessibility, performance, and resilience over relying on specific browser features or JavaScript execution.

**Application in This Project:**

Progressive Enhancement is enforced throughout the frontend:

**HTML-First Content:**
- All content (including tables) is written directly in HTML, not generated by JavaScript
- Navigation uses standard anchor links that work without JavaScript
- All images and text are in the HTML source

**CSS Enhancements:**
- Visual styling enhances the presentation but doesn't break layout if CSS fails
- Responsive design uses CSS media queries (no JavaScript required)
- CSS custom properties provide theming capabilities

**JavaScript Enhancements:**
- Table sorting is added via JavaScript but tables display and are readable without it
- Header scroll state (transparency) is a visual enhancement, not required for functionality
- Navigation active states are visual indicators, navigation links work without JavaScript
- All JavaScript is consolidated in `enhancements.js` and degrades gracefully

**Specific Examples:**
- Tables: Fully functional HTML tables that display all data. JavaScript adds sorting capability with visual indicators (sort arrows) only when JS is available.
- Navigation: Standard page navigation works via links. JavaScript adds active state highlighting and smooth transitions.
- Responsive sizing: CSS custom properties are set via JavaScript for dynamic header height, but fallback values in CSS ensure the site works without JS.

This ensures the site is accessible, performant, and works for all users regardless of their browser capabilities or JavaScript availability.

---

## Project Structure

```
frontend/
├── index.html
├── research.html
├── logistics.html
├── webservices.html
├── demo.html
├── assets/
│   ├── css/
│   │   ├── main.css              # Main stylesheet (imports all layers)
│   │   ├── settings.css          # ITCSS Layer 1: Design tokens
│   │   ├── tools.css             # ITCSS Layer 2: Mixins/helpers
│   │   ├── generic.css           # ITCSS Layer 3: Reset/normalize
│   │   ├── elements.css          # ITCSS Layer 4: Base element styles
│   │   ├── objects.css            # ITCSS Layer 5: Layout patterns (OOCSS)
│   │   ├── utilities.css         # ITCSS Layer 7: Utility classes
│   │   └── components/           # ITCSS Layer 6: UI components (BEM)
│   │       ├── header.css
│   │       ├── hero.css
│   │       ├── hero-footer.css
│   │       ├── section-cards.css
│   │       ├── section-pills.css
│   │       ├── section-offer.css
│   │       ├── timeline.css
│   │       ├── timeline-multi-year.css
│   │       ├── divider.css
│   │       ├── footer.css
│   │       └── table.css
│   ├── js/
│   │   └── enhancements.js       # All JavaScript enhancements
│   └── imgs/                     # Image assets
└── msn_<userId>.json             # Mycite manifest
```

## File Organization Principles

- **One component per file** - Each component has its own CSS file for maintainability
- **Layer order enforced** - `main.css` imports files in strict ITCSS order
- **BEM naming for components** - All component classes use `.c-` prefix and BEM syntax
- **OOCSS naming for objects** - All layout classes use `.o-` prefix
- **State classes** - Global `.is-*` for JS hooks, BEM modifiers for component states
- **No inline styles** - All styles are in external stylesheets
- **No JavaScript injection** - All HTML is inlined in pages (no dynamic component loading)
