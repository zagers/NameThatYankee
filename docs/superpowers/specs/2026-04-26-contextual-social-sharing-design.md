# Spec: Contextual Social Sharing Branding

**Date:** 2026-04-26
**Topic:** Improving social media previews for shared links.

## Goal
Replace the hardcoded, often incorrect social media preview (OG:image) with a consistent branding image across the entire site, while using contextual descriptions for the archive vs. individual puzzles.

## Assets
- **Branding Image:** `images/social-card.webp` (A "Bubble Gum Pack" branding image used in Yankees broadcasts).

## Changes

### 1. Global Assets
- Ensure `images/social-card.webp` is used as the primary `og:image` and `twitter:image` for all pages.

### 2. Archive Page (`index.html`)
- **OG Title:** "Name That Yankee Archive"
- **OG Description:** "Come see this archive of ALL Name That Yankee puzzles! Test your knowledge of Bronx Bombers history."
- **OG Image:** `https://namethatyankeequiz.com/images/social-card.webp`

### 3. Quiz Interface (`quiz.html`)
- **OG Title:** "Name That Yankee Quiz"
- **OG Description:** "Check out this Name That Yankee puzzle! Can you name this player based on their career stats?"
- **OG Image:** `https://namethatyankeequiz.com/images/social-card.webp`

### 4. Page Generator (`page-generator/html_generator.py`)
- Update the `build_detail_page_html` template to use the new branding.
- **OG Title:** "Name That Yankee - {formatted_date}"
- **OG Description:** "Check out this Name That Yankee puzzle! Can you name this player based on their career stats?"
- **OG Image:** `https://namethatyankeequiz.com/images/social-card.webp`

### 5. Historical Migration
- A one-time script (or manual batch update) to update the `og:description` and `og:image` tags in all 160+ existing historical `.html` files (e.g., `2025-07-23.html`).

## Testing Strategy
- **Visual Inspection:** Verify `<meta>` tags in `index.html`, `quiz.html`, and generated historical pages.
- **Simulator Check:** Use a social media preview debugger (like OpenGraph.xyz) if possible, or verify local file source.
- **Regression:** Ensure no other SEO tags (canonical, titles) are negatively impacted.
