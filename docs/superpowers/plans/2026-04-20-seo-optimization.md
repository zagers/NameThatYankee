# SEO Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate indexing onto "Reveal" pages, fix duplicate canonical issues on `quiz.html`, and clean up crawl errors like 404s and extension inconsistencies.

**Architecture:** Script-based dynamic SEO for `quiz.html`, `nofollow` for quiz links, and extensionless URL enforcement in the page generator.

**Tech Stack:** HTML, JavaScript, Python.

---

### Task 1: Fix `quiz.html` Canonical and Meta Tags

**Files:**
- Modify: `quiz.html`

- [ ] **Step 1: Write the failing test**

The current tests likely don't check for multiple canonicals or the specific SEO script behavior. Create a test case in `tests/unit/page_generator/test_seo_metadata.py` (or a relevant test file) that validates the canonical behavior for `quiz.html`.

- [ ] **Step 2: Remove hardcoded canonical link**

Remove the static canonical tag from `quiz.html`.

```html
<link rel="canonical" href="https://namethatyankeequiz.com/quiz">
```

- [ ] **Step 3: Update dynamic SEO script**

Update the script in `quiz.html` to set the correct canonical (pointing to the Reveal page for dated quizzes) and add a `noindex` tag.

```javascript
        (function() {
            const params = new URLSearchParams(window.location.search);
            const date = params.get('date');
            const canonical = document.createElement('link');
            canonical.rel = 'canonical';
            if (date && /^\d{4}-\d{2}-\d{2}$/.test(date)) {
                // Point canonical to the Reveal page
                canonical.href = 'https://namethatyankeequiz.com/' + date;
                // Add noindex for dated quiz pages
                const meta = document.createElement('meta');
                meta.name = 'robots';
                meta.content = 'noindex';
                document.head.appendChild(meta);
            } else {
                canonical.href = 'https://namethatyankeequiz.com/quiz';
            }
            document.head.appendChild(canonical);
        })();
```

- [ ] **Step 4: Commit**

```bash
git add quiz.html
git commit -m "seo: update quiz.html canonical and add noindex for dated quiz pages"
```

### Task 2: Update Gallery Generator for Search Engine Hinting

**Files:**
- Modify: `page-generator/html_generator.py`

- [ ] **Step 1: Add rel="nofollow" to Quiz link in gallery snippet**

Update `generate_gallery_snippet` in `page-generator/html_generator.py` to add `rel="nofollow"` to the quiz action link.

```python
                        <a href="quiz?date={date_str}" class="action-link quiz-link" rel="nofollow">
```

- [ ] **Step 2: Commit**

```bash
git add page-generator/html_generator.py
git commit -m "seo: add nofollow to quiz links in gallery generator"
```

### Task 3: Update `robots.txt`

**Files:**
- Modify: `robots.txt`

- [ ] **Step 1: Add Disallow rule for dated quiz pages**

Add `Disallow: /*?date=` to `robots.txt` to discourage crawling of dynamic quiz URLs.

```text
User-agent: *
Allow: /
Disallow: /*?date=
```

- [ ] **Step 2: Commit**

```bash
git add robots.txt
git commit -m "seo: disallow dated quiz pages in robots.txt"
```

### Task 4: Cleanup `2000-01-01` Placeholder Data

**Files:**
- Delete: `images/clue-2000-01-01.webp`
- Delete: `images/answer-2000-01-01.webp` (if it exists)
- Modify: `test_yankee_site.py` (update test date if needed)

- [ ] **Step 1: Delete placeholder images**

Remove the `2000-01-01` images so the generator no longer includes them in the gallery.

```bash
rm images/clue-2000-01-01.webp
# Check if answer image exists and remove it
[ -f images/answer-2000-01-01.webp ] && rm images/answer-2000-01-01.webp
```

- [ ] **Step 2: Update E2E test to use a valid test date**

If `test_yankee_site.py` relies on `2000-01-01`, update it to use a date that's guaranteed to be in the dataset (like `2025-07-23` or a dedicated test fixture date).

- [ ] **Step 3: Commit**

```bash
git rm images/clue-2000-01-01.webp
git commit -m "seo: remove 2000-01-01 placeholder data and update tests"
```

### Task 5: Final Rebuild and Verification

- [ ] **Step 1: Run project-wide tests**

```bash
./run_tests.sh
```

- [ ] **Step 2: Regenerate the site index**

Run the automation to rebuild `index.html` with the new changes (extensionless URLs, nofollow, etc.).

```bash
python3 page-generator/main.py --rebuild-index
```

- [ ] **Step 3: Commit regenerated index.html**

```bash
git add index.html
git commit -m "seo: rebuild index.html with new SEO hints and cleanup"
```
