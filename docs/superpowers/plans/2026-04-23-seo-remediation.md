# SEO Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve Google Search Console indexing errors by adding a static noindex tag to quiz pages, normalizing internal links to the root domain (`/`), and generating rich, descriptive titles for historical puzzle pages.

**Architecture:** 
1. `quiz.html` will have a static `<meta name="robots" content="noindex">` added to its `<head>`, and its canonical tag script will be simplified.
2. `manifest.json`, `js/analytics.js`, and `js/quiz.js` will be updated to point to `/` instead of `index.html`.
3. `page-generator/html_generator.py` will be updated to generate a richer `<title>` tag for the detail pages.

**Tech Stack:** HTML, JavaScript, Python

---

### Task 1: Add static noindex to quiz.html

**Files:**
- Modify: `quiz.html:20-40`

- [ ] **Step 1: Replace JS-based canonical/noindex with static tags**

```html
    <meta name="apple-mobile-web-app-title" content="NameThatYankee">
    
    <!-- Do not index interactive quiz states -->
    <meta name="robots" content="noindex">
    
    <script>
        (function() {
            const params = new URLSearchParams(window.location.search);
            const date = params.get('date');
            const canonical = document.createElement('link');
            canonical.rel = 'canonical';
            if (date && /^\d{4}-\d{2}-\d{2}$/.test(date)) {
                // Point canonical to the Reveal page
                canonical.href = 'https://namethatyankeequiz.com/' + date;
            } else {
                canonical.href = 'https://namethatyankeequiz.com/quiz';
            }
            document.head.appendChild(canonical);
        })();
    </script>
</head>
```

- [ ] **Step 2: Commit**

```bash
git add quiz.html
git commit -m "seo: add static noindex to quiz.html"
```

---

### Task 2: Normalize internal links to the root domain

**Files:**
- Modify: `manifest.json:4-6`
- Modify: `js/analytics.js:93-95`
- Modify: `js/analytics.js:130-132`
- Modify: `js/quiz.js:26-28`

- [ ] **Step 1: Update manifest.json**

```json
  "description": "Can you name this New York Yankee based on their career stats?",
  "start_url": "/",
  "display": "standalone",
```

- [ ] **Step 2: Update js/analytics.js (Team Filter)**

```javascript
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const clickedIndex = elements[0].index;
                    const teamAbbreviation = labels[clickedIndex];
                    window.location.href = `/?search=${teamAbbreviation}`;
                }
            }
```

- [ ] **Step 3: Update js/analytics.js (Decade Filter)**

```javascript
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const clickedIndex = elements[0].index;
                    const decade = originalDecades[clickedIndex]; // e.g., 1980
                    window.location.href = `/?decade=${decade}`;
                }
            }
```

- [ ] **Step 4: Update js/quiz.js**

```javascript
    if (params.get('reset') === 'true') {
        localStorage.removeItem('nameThatYankeeTotalScore');
        localStorage.removeItem('nameThatYankeeCompletedPuzzles');
        localStorage.removeItem('nameThatYankeeScoreBreakdown');
        alert('Your score and quiz history have been reset.');
        window.location.assign('/');
        return;
    }
```

- [ ] **Step 5: Run frontend tests to ensure no regressions**

```bash
npm run test
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add manifest.json js/analytics.js js/quiz.js
git commit -m "seo: normalize internal links to root domain"
```

---

### Task 3: Generate rich titles for historical pages

**Files:**
- Modify: `page-generator/html_generator.py:221-227`

- [ ] **Step 1: Update the detail page template title**

```python
    template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_name} Answer - {formatted_date} | Name That Yankee</title>
    <link rel="stylesheet" href="style.css">
```

- [ ] **Step 2: Run backend tests**

```bash
pytest tests/unit/page_generator/test_html_generator.py -v
```
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add page-generator/html_generator.py
git commit -m "seo: generate rich titles for historical puzzle pages"
```
