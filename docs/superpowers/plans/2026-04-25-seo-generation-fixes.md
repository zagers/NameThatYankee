# SEO and Generation Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Address PR review feedback for PR #83, fixing logic bugs in index rebuilding, restoring search metadata, and improving HTML source formatting.

**Architecture:** 
- `html_generator.py` will be modified to ensure the gallery is saved before the sync loop starts.
- `rebuild_index_page` will be hardened to ensure all clues are included even if JSON data is missing.
- `generate_gallery_snippet` will restore the `data-search-terms` attribute for robust gallery searching.
- Formatting improvements will be applied to `build_detail_page_html`.

**Tech Stack:** Python, BeautifulSoup

---

### Task 1: Fix Indentation and Indent Logic in Detail Page Generation

**Files:**
- Modify: `page-generator/html_generator.py:28-33`

- [ ] **Step 1: Use a cleaner loop for stat items to ensure consistent indentation**

```python
    # Generate career totals table rows
    stats_rows_html = ""
    for label, val in career_totals_data.items():
        stats_rows_html += f"""
                <div class="stat-item">
                    <span class="stat-label">{label}</span>
                    <span class="stat-value">{val}</span>
                </div>"""
```

- [ ] **Step 2: Commit**

```bash
git add page-generator/html_generator.py
git commit -m "fix: consistent indentation for stat items in detail pages"
```

---

### Task 2: Restore Gallery Search Metadata

**Files:**
- Modify: `page-generator/html_generator.py:355-375`
- Modify: `page-generator/html_generator.py:410-455`

- [ ] **Step 1: Update `generate_gallery_snippet` to include `data-search-terms`**

```python
def generate_gallery_snippet(i, date_str, formatted_date, search_terms):
    """
    Generates a single gallery card snippet with LCP-aware image loading.
    """
    # Only lazy load items below the fold (index > 5)
    loading_attr = 'loading="lazy"' if i > 5 else ''
    
    return f"""<div class="gallery-container" data-search-terms="{html.escape(search_terms)}">
                <a href="{date_str}" class="gallery-item">
```

- [ ] **Step 2: Fix `rebuild_index_page` loop to accumulate full search tokens and avoid skipping clues**

```python
            # Build search tokens for the gallery tile (Identity Logic fallback)
            search_tokens = [formatted_date.lower().replace(',', ''), player_name.lower()]
            
            # Load player name from detail page for search optimization
            detail_path = project_dir / f"{date_str}.html"
            if detail_path.exists():
                with open(detail_path, 'r', encoding='utf-8') as df:
                    d_soup = BeautifulSoup(df, 'html.parser')
                    # Try current standard #quiz-data first, fall back to legacy #search-data
                    quiz_data_el = d_soup.select_one('#quiz-data') or d_soup.select_one('#search-data')
                    if quiz_data_el:
                        try:
                            raw_json = quiz_data_el.get_text().strip()
                            if raw_json:
                                player_data = json.loads(raw_json)
                                p_name = player_data.get('name', '')
                                if not p_name:
                                    h2_el = d_soup.select_one('h2')
                                    p_name = h2_el.get_text().strip() if h2_el else ""
                                
                                if p_name:
                                    player_name = p_name
                                    if player_name.lower() not in search_tokens:
                                        search_tokens.append(player_name.lower())

                                # Extract teams and years for search tokens
                                teams = player_data.get('teams', [])
                                if not teams:
                                    teams = [entry.get('team', '') for entry in player_data.get('yearly_war', []) if entry.get('team')]
                                search_tokens.extend([t.lower() for t in teams])

                                years = player_data.get('years', [])
                                if not years:
                                    years = [entry.get('year', '') for entry in player_data.get('yearly_war', []) if entry.get('year')]
                                search_tokens.extend([str(y) for y in years])
                                
                                stats_summary.append({
                                    "date": date_str,
                                    "name": player_name,
                                    "nickname": player_data.get('nickname', ''),
                                    "teams": list(set(teams)),
                                    "years": list(set(years))
                                })
                        except (json.JSONDecodeError, AttributeError):
                            pass

            search_terms = " ".join(filter(None, search_tokens))
            snippet = generate_gallery_snippet(i, date_str, formatted_date, search_terms)
            gallery_tiles.append(snippet)
```

- [ ] **Step 3: Commit**

```bash
git add page-generator/html_generator.py
git commit -m "fix: restore gallery search metadata and prevent clue skipping"
```

---

### Task 3: Fix Index Page Rebuild and Footer Sync Loop

**Files:**
- Modify: `page-generator/html_generator.py:455-480`

- [ ] **Step 1: Save the modified gallery to `index.html` BEFORE starting the footer sync loop**

```python
    gallery_div.clear()
    for tile_html in gallery_tiles:
        tile_soup = BeautifulSoup(tile_html, 'html.parser')
        gallery_div.append(tile_soup)
        gallery_div.append('\n')
    
    # Save the updated index.html with new gallery tiles BEFORE the sync loop
    # This prevents the sync loop from re-reading a stale version of index.html
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
```

- [ ] **Step 2: Commit**

```bash
git add page-generator/html_generator.py
git commit -m "fix: ensure gallery updates are saved before footer sync loop"
```

---

### Task 4: Final Verification

- [ ] **Step 1: Run full regression suite**

Run: `./run_tests.sh`
Expected: ALL PASS

- [ ] **Step 2: Commit**

```bash
git commit --allow-empty -m "test: verified all PR review fixes pass regression"
```
