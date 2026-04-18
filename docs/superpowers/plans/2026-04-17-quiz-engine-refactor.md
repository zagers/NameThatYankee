# Quiz Engine Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the monolithic quiz logic into a testable, decoupled `QuizEngine` module.

**Architecture:** Extracts game logic (scoring, normalization, state) into a "pure" `QuizEngine` class. The UI (`quiz.js`) acts as a driver, passing input to the engine and updating the DOM based on returned `Result` objects.

**Tech Stack:** JavaScript (ESM), Vitest, JSDOM.

---

### Task 0: Deferred Header Fix

**Files:**
- Modify: `index.html:1-5`

- [ ] **Step 1: Add ABOUTME header to `index.html`**

```html
<!-- ABOUTME: Main archives page for Name That Yankee trivia. -->
<!-- ABOUTME: Displays a gallery of historical puzzles with search and filter capabilities. -->
<!DOCTYPE html>
<html lang="en">
```

- [ ] **Step 2: Commit**

```bash
git add index.html
git commit -m "docs: add missing ABOUTME header to index.html"
```

---

### Task 1: Initialize QuizEngine Module

**Files:**
- Create: `js/quizEngine.js`
- Test: `tests/js/quizEngine.test.js`

- [ ] **Step 1: Create the skeleton for `js/quizEngine.js`**

```javascript
// ABOUTME: Pure logic engine for the Name That Yankee quiz.
// ABOUTME: Handles scoring, normalization, and game state without DOM dependencies.

export class QuizEngine {
    #answer;
    #nickname;

    constructor(answer, clues, nickname = "") {
        if (!answer) throw new Error("QuizEngine requires a valid answer");
        this.#answer = answer;
        this.#nickname = nickname;
        this.clues = clues;
        this.currentClueIndex = 0;
        this.isComplete = false;
        this.previousGuesses = new Set();
    }

    normalize(text) {
        if (!text) return '';
        return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
    }

    calculateScore(index) {
        const points = [10, 7, 4, 1, 0];
        return points[index] !== undefined ? points[index] : 0;
    }
}
```

- [ ] **Step 2: Create the initial test file `tests/js/quizEngine.test.js`**

```javascript
import { describe, it, expect, beforeEach } from 'vitest';
import { QuizEngine } from '../../js/quizEngine.js';

describe('QuizEngine', () => {
    let engine;
    const answer = "Derek Jeter";
    const clues = ["Clue 1", "Clue 2", "Clue 3"];

    beforeEach(() => {
        engine = new QuizEngine(answer, clues);
    });

    describe('Normalization', () => {
        it('should normalize casing and diacritics', () => {
            expect(engine.normalize("Déreck Jétèr")).toBe("dereck jeter");
        });

        it('should trim whitespace', () => {
            expect(engine.normalize("  Derek Jeter  ")).toBe("derek jeter");
        });
    });

    describe('Scoring', () => {
        it('should return correct scores for each clue index', () => {
            expect(engine.calculateScore(0)).toBe(10);
            expect(engine.calculateScore(2)).toBe(4);
            expect(engine.calculateScore(4)).toBe(0);
        });
    });
});
```

- [ ] **Step 3: Run tests to verify setup**

Run: `npm test tests/js/quizEngine.test.js`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add js/quizEngine.js tests/js/quizEngine.test.js
git commit -m "feat: initialize QuizEngine module and basic unit tests"
```

---

### Task 2: Implement Guess Validation (TDD)

**Files:**
- Modify: `js/quizEngine.js`
- Modify: `tests/js/quizEngine.test.js`

- [ ] **Step 1: Write failing test for `submitGuess`**

Add to `tests/js/quizEngine.test.js`:
```javascript
    describe('submitGuess', () => {
        const allPlayers = ["Derek Jeter", "Alex Rodriguez", "Mariano Rivera"];

        it('should return CORRECT for a match', () => {
            const result = engine.submitGuess("Derek Jeter", allPlayers);
            expect(result.status).toBe('CORRECT');
            expect(result.score).toBe(10);
            expect(engine.isComplete).toBe(true);
        });

        it('should return INCORRECT_VALID_PLAYER for a wrong but valid player', () => {
            const result = engine.submitGuess("Alex Rodriguez", allPlayers);
            expect(result.status).toBe('INCORRECT_VALID_PLAYER');
            expect(engine.currentClueIndex).toBe(1);
            expect(engine.isComplete).toBe(false);
        });

        it('should return INVALID_PLAYER for a name not in the list', () => {
            const result = engine.submitGuess("Not A Player", allPlayers);
            expect(result.status).toBe('INVALID_PLAYER');
            expect(engine.currentClueIndex).toBe(0); // No penalty
        });

        it('should return DUPLICATE_GUESS for repeated wrong answers', () => {
            engine.submitGuess("Alex Rodriguez", allPlayers);
            const result = engine.submitGuess("Alex Rodriguez", allPlayers);
            expect(result.status).toBe('DUPLICATE_GUESS');
            expect(engine.currentClueIndex).toBe(1); // No double penalty
        });
    });
```

- [ ] **Step 2: Run tests and verify failure**

Run: `npm test tests/js/quizEngine.test.js`
Expected: FAIL (submitGuess is not a function)

- [ ] **Step 3: Implement `submitGuess` in `js/quizEngine.js`**

```javascript
    submitGuess(guess, allPlayers) {
        if (this.isComplete) return { status: 'LOCKED' };

        const normalizedGuess = this.normalize(guess);
        const normalizedAnswer = this.normalize(this.#answer);
        const normalizedNickname = this.normalize(this.#nickname);

        if (normalizedGuess === normalizedAnswer || (normalizedNickname && normalizedGuess === normalizedNickname)) {
            this.isComplete = true;
            return {
                status: 'CORRECT',
                score: this.calculateScore(this.currentClueIndex),
                clueIndex: this.currentClueIndex,
                gameOver: true
            };
        }

        if (this.previousGuesses.has(normalizedGuess)) {
            return { status: 'DUPLICATE_GUESS', clueIndex: this.currentClueIndex };
        }

        const normalizedPlayers = allPlayers.map(p => this.normalize(p));
        if (normalizedPlayers.includes(normalizedGuess)) {
            this.previousGuesses.add(normalizedGuess);
            this.currentClueIndex++;
            const gameOver = this.currentClueIndex >= this.clues.length;
            if (gameOver) this.isComplete = true;
            
            return {
                status: 'INCORRECT_VALID_PLAYER',
                clueIndex: this.currentClueIndex,
                gameOver: gameOver
            };
        }

        return { status: 'INVALID_PLAYER', clueIndex: this.currentClueIndex };
    }
```

- [ ] **Step 4: Run tests and verify success**

Run: `npm test tests/js/quizEngine.test.js`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add js/quizEngine.js tests/js/quizEngine.test.js
git commit -m "feat: implement submitGuess logic in QuizEngine"
```

---

### Task 3: Refactor `quiz.js` to use `QuizEngine`

**Files:**
- Modify: `js/quiz.js`

- [ ] **Step 1: Import QuizEngine and update initialization**

```javascript
import { QuizEngine } from './quizEngine.js';

// Inside initialization function:
const engine = new QuizEngine(data.answer, data.hints, data.nickname);
```

- [ ] **Step 2: Replace guess logic with engine calls**

Update the "Submit" event listener to use `engine.submitGuess(value, allPlayers)` and handle the returned status object. Remove local `normalizeText` and `calculateScore` functions from `quiz.js`.

- [ ] **Step 3: Run regression tests**

Run: `./run_tests.sh`
Expected: 100% PASS

- [ ] **Step 4: Commit**

```bash
git add js/quiz.js
git commit -m "refactor: integrate QuizEngine into quiz.js and remove redundant logic"
```
