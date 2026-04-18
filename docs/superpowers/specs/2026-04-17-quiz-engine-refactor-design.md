# Design Spec: Quiz Engine Refactor (The "Pragmatic Brain")

**Date:** 2026-04-17  
**Topic:** Refactoring `js/quiz.js` into a testable `QuizEngine` module.

## 1. Goal
Improve the testability and maintainability of the Name That Yankee trivia game by decoupling the core game logic (the "Brain") from the DOM and UI (the "Body").

## 2. Architecture: The "Brain" and the "Body"

We will split the current `js/quiz.js` into two focused modules:

### 2.1 `js/quizEngine.js` (The Brain)
- **Role:** Pure game logic, scoring, and normalization.
- **Responsibility:**
    - Initialize with a hidden `#answer` and `#nickname`.
    - Track `currentClueIndex` and `isComplete` status.
    - Process guesses via `submitGuess(guess, allPlayers)`.
    - Calculate scores based on the current clue index.
    - Normalize player names (case-insensitive, diacritic-insensitive).
- **Security:** Use Private Class Fields (`#answer`) to prevent easy console-peeking.
- **Testability:** 100% testable in a headless Node.js environment with mock data.

### 2.2 `js/quiz.js` (The Body)
- **Role:** DOM driver and entry point.
- **Responsibility:**
    - Scrape the answer and clues from the puzzle's HTML.
    - Instantiate and manage a `QuizEngine` instance.
    - Handle DOM events (clicks on "Guess", "Hint", "I Give Up").
    - Update the UI based on the `Result` objects returned by the engine.
    - Persist game state and final scores to `localStorage`.

## 3. The `QuizEngine` Interface

The engine acts as a "Calculator." It does not update the screen or reach into the DOM.

### `submitGuess(guess, allPlayers)`
**Returns a Result Object:**
```javascript
{ 
  status: 'CORRECT' | 'INCORRECT_VALID_PLAYER' | 'INVALID_PLAYER' | 'DUPLICATE_GUESS',
  score: number, 
  clueIndex: number,
  gameOver: boolean,
  message: string (optional tooltip text)
}
```

## 4. Security & Error Handling
- **Locked State:** Once `isComplete` is true (Win or Give Up), the engine rejects further guesses.
- **Input Validation:** All inputs are strictly cast to strings to prevent prototype pollution.
- **Robustness:** Explicitly throws errors if initialized without a valid answer or clues list.

## 5. Testing Strategy (TDD)
- **Unit Tests:** `tests/js/quizEngine.test.js` will cover:
    - Normalization: `A-Rod` vs `Alex Rodriguez`.
    - Scoring: 100 points on clue 0, 80 on clue 1, etc.
    - Game Flow: Correct guess, incorrect guess (clue increment), too many wrong guesses (GameOver).
    - Edge Cases: Duplicate guesses, empty inputs, "I Give Up" locking.

## 6. Implementation Steps
1. Create `js/quizEngine.js` with basic class structure.
2. Write failing unit tests for normalization and scoring.
3. Implement `normalize()` and `calculateScore()` in the engine.
4. Write failing tests for `submitGuess()` game flow.
5. Implement `submitGuess()` logic.
6. Refactor `js/quiz.js` to use the new `QuizEngine`.
7. Verify 100% pass rate on all regression tests (`./run_tests.sh`).
