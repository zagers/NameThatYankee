# Special Tribute Search Logic Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update search logic in `js/galleryFilter.js` to support decade strings (e.g., "1980s") and allow searching special tribute puzzles by name.

**Architecture:** Update the `checkMatch` function with specialized conditional checks for decade patterns and special puzzle flags.

**Tech Stack:** JavaScript (ESM)

---

### Task 1: Setup Branch

**Files:**
- N/A

- [ ] **Step 1: Create and switch to new branch**

Run: `git checkout -b fix/search-logic-special-tribute`

---

### Task 2: Fix Decade Search Logic

**Files:**
- Modify: `js/galleryFilter.js`

- [ ] **Step 1: Update decade matching in checkMatch**

Update section 3 to handle 5-digit decade strings (e.g. "1980s") within the `puzzle.years` array.

```javascript
<<<<
            if (token.length === 3) { // e.g. "90s"
                const decadeDigit = token[0];
                if (puzzle.years.some(y => y.length === 4 && y[2] === decadeDigit)) return true;
            } else if (token.length === 5) { // e.g. "1990s"
====
            if (token.length === 3) { // e.g. "90s"
                const decadeDigit = token[0];
                if (puzzle.years.some(y => (y.length === 4 || y.length === 5) && y[2] === decadeDigit)) return true;
            } else if (token.length === 5) { // e.g. "1990s"
>>>>
```

---

### Task 3: Allow Searching Special Tributes by Name

**Files:**
- Modify: `js/galleryFilter.js`

- [ ] **Step 1: Update name/nickname matching logic**

Allow searching for special puzzles even if they aren't marked as completed.

```javascript
<<<<
        // 4. Check Name/Nickname (ONLY if solved)
        if (isCompleted) {
            if (puzzle.name.toLowerCase().includes(token)) return true;
====
        // 4. Check Name/Nickname (ONLY if solved or special)
        if (isCompleted || puzzle.isSpecial) {
            if (puzzle.name.toLowerCase().includes(token)) return true;
>>>>
```

---

### Task 4: Handle Specific Year Search for Decade Ranges

**Files:**
- Modify: `js/galleryFilter.js`

- [ ] **Step 1: Add year matching for decade strings**

Update section 3 to match a specific 4-digit year (e.g., "1989") if the puzzle has the corresponding decade string (e.g., "1980s").

```javascript
<<<<
        // 3. Check Years & Decades
        if (puzzle.years.includes(token)) return true;
        if (token.endsWith('s')) {
====
        // 3. Check Years & Decades
        if (puzzle.years.includes(token)) return true;
        if (token.length === 4 && !isNaN(token)) {
            const decadePrefix = token.substring(0, 3);
            if (puzzle.years.some(y => y.startsWith(decadePrefix) && y.endsWith('s'))) return true;
        }
        if (token.endsWith('s')) {
>>>>
```

---

### Task 5: Verification

**Files:**
- Read: `js/galleryFilter.js`

- [ ] **Step 1: Verify the checkMatch function**

Ensure the logic is clean and no syntax errors were introduced.

---

### Task 6: Commit Changes

**Files:**
- N/A

- [ ] **Step 1: Commit the fixes**

Run: `git add js/galleryFilter.js`
Run: `git commit -m "fix: update search logic to support special tribute items and decade strings"`
