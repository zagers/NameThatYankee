# Quiz Refactor (Part 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the quiz interface into a modular, state-driven architecture for better maintainability and security.

**Architecture:** A central Orchestrator (`quiz.js`) manages a `QuizState` object. It uses the `QuizEngine` to calculate state transitions, a specialized Renderer (`quizUI.js`) for DOM updates, and `quizShare.js` for social logic.

**Tech Stack:** Vanilla JavaScript (ES Modules), Vitest (Unit/Component testing), Playwright (E2E testing)

---

### Task 1: Implement State Transition Logic & Tests

**Goal:** Ensure the "brain" of the state management is robust before touching the UI.

**Files:**
- Create: `tests/js/quizState.test.js`
- Modify: `js/quiz.js` (Define the core state transition function)

- [ ] **Step 1: Write state transition tests**
Verify that user actions (guess, hint) produce the correct state changes.

```javascript
import { describe, it, expect, vi } from 'vitest';
// We'll mock the QuizEngine to focus purely on state management
vi.mock('../../js/quizEngine.js');

describe('Quiz State Transitions', () => {
    it('initializes with a default state', () => {
        const state = createInitialState('2026-04-20');
        expect(state.status).toBe('loading');
        expect(state.guesses).toEqual([]);
    });

    it('transitions to solved when a correct guess is processed', () => {
        const initialState = { status: 'active', guesses: [], score: 100 };
        const result = { status: 'CORRECT', score: 100 };
        const nextState = reducer(initialState, { type: 'GUESS_RESULT', result });
        expect(nextState.status).toBe('solved');
        expect(nextState.score).toBe(100);
    });
});
```

- [ ] **Step 2: Implement the `reducer` pattern in `js/quiz.js`**
Even in vanilla JS, a reducer-like function will make state changes predictable and testable.

- [ ] **Step 3: Commit**
```bash
git add js/quiz.js tests/js/quizState.test.js
git commit -m "test: add state transition logic and tests"
```

---

### Task 2: Implement the Sharing Module

**Files:**
- Create: `js/quizShare.js`
- Test: `tests/js/quizShare.test.js`

- [ ] **Step 1: Write unit tests for emoji grid and text generation**
- [ ] **Step 2: Implement `js/quizShare.js`**
- [ ] **Step 3: Commit**
```bash
git add js/quizShare.js tests/js/quizShare.test.js
git commit -m "feat: add isolated sharing module"
```

---

### Task 3: Implement the UI Renderer

**Files:**
- Create: `js/quizUI.js`
- Test: `tests/js/quizUI.test.js`

- [ ] **Step 1: Write component tests for the renderer**
Mock the DOM using JSDOM and verify that `render(state)` toggles the correct visibility and text.

- [ ] **Step 2: Implement `js/quizUI.js`**
Focus on `textContent` for security and caching DOM elements for performance.

- [ ] **Step 3: Commit**
```bash
git add js/quizUI.js tests/js/quizUI.test.js
git commit -m "feat: add state-driven UI renderer"
```

---

### Task 4: Orchestration & Final Integration

**Files:**
- Modify: `js/quiz.js`
- Test: `run_tests.sh`

- [ ] **Step 1: Connect all modules in `initQuiz`**
- [ ] **Step 2: Remove legacy monolithic code**
- [ ] **Step 3: Run full regression suite (Python E2E + Vitest)**
- [ ] **Step 4: Commit**
```bash
git add js/quiz.js
git commit -m "refactor: complete modular quiz refactor"
```
