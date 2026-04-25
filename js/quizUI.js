// ABOUTME: Stateless renderer for the Name That Yankee quiz.
// ABOUTME: Synchronizes the DOM with the current QuizState.

export class QuizUI {
    /**
     * @param {string[]} clues - Array of clue strings for the current puzzle.
     */
    constructor(clues = []) {
        this.clues = clues;
        this.cacheElements();
    }

    /**
     * Caches all necessary DOM element references once during initialization.
     */
    cacheElements() {
        this.elements = {
            quizArea: document.getElementById('quiz-area'),
            successArea: document.getElementById('success-area'),
            feedbackMessage: document.getElementById('feedback-message'),
            hintsContainer: document.getElementById('hints-container'),
            hintsList: document.getElementById('hints-list'),
            guessInput: document.getElementById('guess-input'),
            submitBtn: document.getElementById('submit-guess'),
            hintBtn: document.getElementById('request-hint'),
            giveUpBtn: document.getElementById('give-up-btn'),
            totalScore: document.getElementById('total-score'),
            successHeader: document.getElementById('success-header')
        };
    }

    /**
     * Renders the current state to the DOM.
     * @param {Object} state - The current QuizState.
     */
    render(state) {
        if (!state) return;

        // 1. Set visibility of quiz-area vs success-area based on state.status
        const isSolved = state.status === 'solved';
        if (this.elements.quizArea) {
            this.elements.quizArea.style.display = isSolved ? 'none' : 'block';
        }
        if (this.elements.successArea) {
            this.elements.successArea.style.display = isSolved ? 'block' : 'none';
        }

        // 2. Update feedback-message with state.error or success messages
        if (this.elements.feedbackMessage) {
            this.elements.feedbackMessage.textContent = state.error || state.feedback || '';
        }

        // 3. Update success header
        if (this.elements.successHeader && isSolved) {
            this.elements.successHeader.textContent = state.correctAnswer || '';
        }

        // 4. Append hints to the hints-list based on state.hintsRequested
        if (this.elements.hintsList && this.elements.hintsContainer) {
            this.elements.hintsList.innerHTML = ''; // Clear existing hints
            if (state.hintsRequested > 0) {
                this.elements.hintsContainer.style.display = 'block';
                for (let i = 0; i < state.hintsRequested; i++) {
                    if (this.clues[i]) {
                        const li = document.createElement('li');
                        li.textContent = this.clues[i];
                        this.elements.hintsList.appendChild(li);
                    }
                }
            } else {
                this.elements.hintsContainer.style.display = 'none';
            }
        }

        // 5. Disable/Enable inputs and buttons
        const shouldDisable = !!(state.isProcessing || state.isComplete);
        if (this.elements.guessInput) this.elements.guessInput.disabled = shouldDisable;
        if (this.elements.submitBtn) this.elements.submitBtn.disabled = shouldDisable;
        if (this.elements.hintBtn) this.elements.hintBtn.disabled = shouldDisable;
        if (this.elements.giveUpBtn) this.elements.giveUpBtn.disabled = shouldDisable;

        // 6. Update total-score display
        if (this.elements.totalScore) {
            this.elements.totalScore.textContent = state.totalScore !== undefined ? state.totalScore : '0';
        }
    }
}
