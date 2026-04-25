# Quiz Refactor (Part 2) Design Spec

> **About this document:** This spec defines the transition of the quiz interface from a monolithic architecture to a modular, state-driven system.

**Goal:** Refactor `js/quiz.js` into focused modules (`Orchestrator`, `UI`, and `Share`) to improve maintainability, testability, and security.

**Architecture:** 
- **Modular Design:** Separation of concerns between high-level game flow, DOM rendering, and social sharing.
- **State-Driven UI:** The user interface becomes a pure function of a central `QuizState` object.

**Tech Stack:** Vanilla JavaScript (ES Modules)

---

## 1. Core Modules

### 1.1 `js/quiz.js` (The Orchestrator)
The entry point that manages the "Source of Truth" for the game.
- **Initialization:** Sets up Firebase, Firestore, and ReCaptcha.
- **State Management:** Maintains a central `state` object.
- **Input Handling:** Listens for user actions (guesses, resets) and delegates logic to `QuizEngine`.
- **Database Coordination:** Handles all `addDoc` and `getDoc` calls to Firestore.
- **Security:** Isolates the database object (`db`) from other modules.

### 1.2 `js/quizUI.js` (The Renderer)
A pure UI layer that updates the DOM based on the current state.
- **DOM Caching:** Efficiently caches element references once at startup.
- **Stateless Rendering:** A main `render(state)` function that ensures the DOM matches the `QuizState`.
- **Interactivity:** Manages focus states, button disabled states, and visual feedback (error messages, loading spinners).
- **Security (XSS):** Uses `textContent` for all player-derived strings.

### 1.3 `js/quizShare.js` (The Social Engine)
Handles result formatting and clipboard/sharing API interactions.
- **Text Generation:** Formats the emoji-grid and score summary for sharing.
- **API Integration:** Manages `navigator.share` (mobile) and `navigator.clipboard` (desktop) logic.
- **Reuse:** Decoupled so sharing logic can be invoked from other pages if needed.

---

## 2. Data Structures

### 2.1 The `QuizState` Object
```javascript
{
    status: 'loading' | 'active' | 'solved' | 'failed',
    date: 'YYYY-MM-DD',
    playerIdentity: string, // Correct answer name
    guesses: string[],
    score: number,
    hintsRevealed: number,
    timerSeconds: number,
    isProcessing: boolean, // For loading states
    error: string | null
}
```

---

## 3. Security Requirements

- **Authority Isolation:** Only `quiz.js` is permitted to perform Firestore writes.
- **Input Sanitization:** All user-provided or data-derived text must be rendered using `textContent` to prevent XSS.
- **Credential Protection:** Firebase config remains in `firebase-config.js` and is imported only by the Orchestrator.

---

## 4. Success Criteria

1. **Modular Code:** `quiz.js` is reduced from ~500 lines to a clean orchestrator script.
2. **Behavioral Parity:** The quiz remains fully functional with no regression in scoring or gameplay.
3. **Green Tests:** All existing `Vitest` and `Playwright` tests pass with the new architecture.
4. **State Integrity:** UI correctly reflects state changes (e.g., sharing button only appears when the game is over).

---

## 5. Testing Strategy

- **Unit Tests:** Add new tests for `quizShare.js` result formatting.
- **Component Tests:** Verify `quizUI.render` correctly toggles visibility of key elements (modals, buttons).
- **Integration Tests:** Existing E2E suite (`test_yankee_site.py`) must pass to confirm end-to-end game flow.
