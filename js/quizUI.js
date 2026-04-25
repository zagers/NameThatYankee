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
            successHeader: document.getElementById('success-header'),
            successPoints: document.getElementById('success-points'),
            clueImage: document.getElementById('clue-image'),
            answerImage: document.getElementById('answer-image'),
            viewAnswerLink: document.getElementById('view-answer-link'),
            showGuessesBtn: document.getElementById('show-guesses-btn'),
            guessesChartContainer: document.getElementById('guesses-chart-container'),
            guessesChartCanvas: document.getElementById('guessesChart'),
            suggestionsContainer: document.getElementById('suggestions-container'),
            shareFailContainer: document.getElementById('share-fail-container'),
            shareBtnSuccess: document.getElementById('share-btn-success'),
            shareBtnFail: document.getElementById('share-btn-fail')
        };
    }

    /**
     * Renders the current state to the DOM.
     * @param {Object} state - The current QuizState.
     */
    render(state) {
        if (!state) return;

        // Visibility toggles
        const isWin = state.isComplete && state.finalScore > 0;
        const isLoss = state.isComplete && state.finalScore === 0;

        if (this.elements.quizArea) {
            // Hide quiz area ONLY on win. Keep it on loss to show correct answer feedback.
            this.elements.quizArea.style.display = isWin ? 'none' : 'block';
        }
        if (this.elements.successArea) {
            this.elements.successArea.style.display = isWin ? 'block' : 'none';
        }
        if (this.elements.shareFailContainer) {
            this.elements.shareFailContainer.style.display = isLoss ? 'block' : 'none';
        }
        if (this.elements.guessesChartContainer) {
            this.elements.guessesChartContainer.style.display = state.showChart ? 'block' : 'none';
        }

        // Feedback messaging
        if (this.elements.feedbackMessage) {
            if (state.error) {
                this.elements.feedbackMessage.textContent = state.error;
                this.elements.feedbackMessage.className = 'incorrect';
                this.elements.feedbackMessage.style.display = 'block';
            } else if (state.feedback) {
                this.elements.feedbackMessage.innerHTML = state.feedback; // Allow HTML for answer link
                this.elements.feedbackMessage.className = state.feedbackClass || '';
                this.elements.feedbackMessage.style.display = 'block';
            } else {
                this.elements.feedbackMessage.textContent = '';
                this.elements.feedbackMessage.className = '';
                // Keep visible but empty if game is active
                this.elements.feedbackMessage.style.display = state.status === 'active' ? 'block' : 'none';
            }
        }

        // Success Header & Points
        if (this.elements.successHeader && isWin) {
            this.elements.successHeader.textContent = `Correct! The answer is ${state.playerIdentity}.`;
        }
        if (this.elements.successPoints && isWin) {
            this.elements.successPoints.textContent = `You earned ${state.finalScore} points!`;
        }

        // Hints
        if (this.elements.hintsList && this.elements.hintsContainer) {
            this.elements.hintsList.innerHTML = '';
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

        // Input & Button states
        const shouldDisable = !!(state.isProcessing || state.isComplete);
        if (this.elements.guessInput) this.elements.guessInput.disabled = shouldDisable;
        if (this.elements.submitBtn) this.elements.submitBtn.disabled = shouldDisable;
        if (this.elements.hintBtn) this.elements.hintBtn.disabled = shouldDisable;
        if (this.elements.giveUpBtn) this.elements.giveUpBtn.disabled = shouldDisable;

        if (this.elements.hintBtn && state.hintsRequested >= this.clues.length) {
            this.elements.hintBtn.disabled = true;
            if (!shouldDisable && !state.feedback && state.status !== 'complete') {
                if (this.elements.feedbackMessage) {
                    this.elements.feedbackMessage.textContent = 'All hints revealed! One guess remaining.';
                    this.elements.feedbackMessage.className = '';
                    this.elements.feedbackMessage.style.display = 'block';
                }
            }
        }

        // Total Score
        if (this.elements.totalScore) {
            this.elements.totalScore.textContent = state.totalScore !== undefined ? state.totalScore : '0';
        }

        // Images & Links
        if (this.elements.clueImage && state.date) {
            this.elements.clueImage.src = `images/clue-${state.date}.webp`;
        }
        if (this.elements.answerImage && state.date && isWin) {
            this.elements.answerImage.src = `images/answer-${state.date}.webp`;
        }
        if (this.elements.viewAnswerLink && state.date) {
            this.elements.viewAnswerLink.href = `${state.date}.html`;
        }
    }
}
