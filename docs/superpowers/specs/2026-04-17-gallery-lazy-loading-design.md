# Gallery Lazy Loading & Rendering Optimization Design

**Goal:** Improve initial page load performance and rendering smoothness for the archive gallery by deferring off-screen image downloads and layout work.

**Architecture:** A hybrid approach using native browser features:
1.  **Image Optimization:** Use the `loading="lazy"` and `decoding="async"` attributes on all gallery images.
2.  **Rendering Optimization:** Use the CSS `content-visibility: auto` property on gallery containers to skip rendering of off-screen elements.
3.  **Stability:** Use `contain-intrinsic-size` to provide placeholder dimensions for off-screen containers, preventing scrollbar "jumping."
4.  **Automation:** Update the Python generation pipeline to include these standards in all future puzzle pages.

**Tech Stack:** HTML5, CSS3, Python (Jinja2/string templates).

---

## Components

### 1. Frontend - HTML (`index.html`)
Update all `<img>` tags within `.gallery-container` to include performance-oriented attributes.

```html
<!-- Example of optimized tag -->
<img alt="..." src="..." loading="lazy" decoding="async" />
```

### 2. Frontend - CSS (`style.css`)
Optimize the layout engine for the gallery grid.

```css
.gallery-container {
  /* Skip rendering when off-screen */
  content-visibility: auto;
  /* Maintain scrollbar stability (standard card height) */
  contain-intrinsic-size: auto 450px;
}
```

### 3. Automation - Python (`page-generator/html_generator.py`)
Ensure the template used for adding new puzzles to the gallery remains compliant with these standards.

## Testing Strategy

### 1. Functional Verification
- Verify that `loading="lazy"` and `decoding="async"` attributes are present on all gallery images in the DOM.
- Verify that `.gallery-container` has the correct CSS properties.

### 2. Automated Tests (TDD)
- **Frontend (Vitest):** Create a test to check for the presence of lazy loading attributes on gallery images.
- **Automation (Pytest):** Update or create a test to ensure the `html_generator.py` produces optimized HTML tags.

## Alternatives Considered
- **Approach 1 (Native Only):** Simple but doesn't solve DOM rendering weight.
- **Approach 3 (JS Virtualization):** Highly performant but adds significant complexity and risks breaking search/filter logic.
