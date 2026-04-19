# Stats Summary Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement consolidated `stats_summary.json` generation during the index rebuild process to support future analytics.

**Architecture:** Modify `rebuild_index_page` in `html_generator.py` to extract player name, teams, and years from each historical HTML file and save it to a JSON file in the project root.

**Tech Stack:** Python, BeautifulSoup, JSON.

---

### Task 1: Update `rebuild_index_page` in `html_generator.py`

**Files:**
- Modify: `page-generator/html_generator.py`

- [ ] **Step 1: Implement the logic in `rebuild_index_page`**

```python
def rebuild_index_page(project_dir: Path):
    # ... existing code ...
    gallery_tiles = []
    stats_summary = []  # Added initialization
    date_pattern = re.compile(r"clue-(\d{4}-\d{2}-\d{2})\.webp")
    # ... existing team_name_map ...

    for i, clue_file in enumerate(all_clue_files):
        match = date_pattern.search(clue_file.name)
        if match:
            date_str = match.group(1)
            try:
                # ... existing date processing ...
                
                # New logic to collect stats
                player_name = "Unknown"
                teams = []
                years = []
                
                if detail_page_path.exists():
                    with open(detail_page_path, 'r', encoding='utf-8') as detail_f:
                        detail_soup = BeautifulSoup(detail_f, 'html.parser')
                    
                    # Extract name from <h2>
                    h2_el = detail_soup.find('h2')
                    if h2_el:
                        player_name = h2_el.get_text(strip=True)
                    
                    # Extract search data (reusing existing search data extraction logic)
                    search_data_div = detail_soup.find('div', id='search-data')
                    if search_data_div:
                        search_data_str = search_data_div.string or "{}"
                        search_data = json.loads(search_data_str)
                        teams = search_data.get('teams', [])
                        years = search_data.get('years', [])
                        
                        # ... existing search_terms logic ...

                # Collect into stats_summary
                stats_summary.append({
                    'date': date_str,
                    'name': player_name,
                    'teams': teams,
                    'years': years
                })

                # ... existing gallery snippet generation ...
            except ValueError:
                print(f"⚠️  Warning: Skipping file with invalid date format: {clue_file.name}")
    
    # ... existing index.html writing logic ...

    # Save the consolidated stats
    stats_path = project_dir / "stats_summary.json"
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats_summary, f, indent=2)
    print(f"✅ stats_summary.json generated with {len(stats_summary)} entries.")

    print("✅ index.html rebuilt successfully.")
```

- [ ] **Step 2: Run the test to verify it passes**

Run: `.venv/bin/pytest test_automation.py::test_rebuild_index_generates_stats_summary -v`
Expected: PASS

- [ ] **Step 3: Commit the changes**

```bash
git add page-generator/html_generator.py
git commit -m "feat: implement stats_summary.json generation in rebuild_index_page"
```
