// ABOUTME: Stateless renderer for the Name That Yankee quiz.
// ABOUTME: Synchronizes the DOM with the current QuizState.

export class QuizUI {
    /**
     * @param {string[]} clues - Array of clue strings for the current puzzle.
     * @param {Object} callbacks - Map of callback functions for UI interactions.
     */
    constructor(clues = [], callbacks = {}) {
        this.clues = clues;
        this.callbacks = callbacks;
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
            quizTitle: document.getElementById('quiz-title'),
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
            this.elements.feedbackMessage.textContent = ''; // Clear
            if (state.error) {
                this.elements.feedbackMessage.textContent = state.error;
                this.elements.feedbackMessage.className = 'incorrect';
                this.elements.feedbackMessage.style.display = 'block';
            } else if (state.feedback) {
                this.elements.feedbackMessage.textContent = state.feedback;
                if (state.feedbackLink) {
                    const p = document.createElement('p');
                    const link = document.createElement('a');
                    link.href = state.feedbackLink.url;
                    link.textContent = state.feedbackLink.text;
                    p.appendChild(link);
                    this.elements.feedbackMessage.appendChild(p);
                }
                this.elements.feedbackMessage.className = state.feedbackClass || '';
                this.elements.feedbackMessage.style.display = 'block';
            } else {
                this.elements.feedbackMessage.className = '';
                // Keep visible but empty if game is active
                this.elements.feedbackMessage.style.display = state.status === 'active' ? 'block' : 'none';
            }
        }

        // Autocomplete suggestions
        if (this.elements.suggestionsContainer) {
            this.elements.suggestionsContainer.innerHTML = '';
            if (state.suggestions && state.suggestions.length > 0) {
                state.suggestions.forEach((match, index) => {
                    const item = document.createElement('div');
                    item.textContent = match;
                    item.classList.add('suggestion-item');
                    if (index === state.highlightedIndex) {
                        item.classList.add('highlighted');
                    }
                    item.addEventListener('click', () => {
                        if (this.callbacks.onSuggestionClick) {
                            this.callbacks.onSuggestionClick(match);
                        }
                    });
                    this.elements.suggestionsContainer.appendChild(item);
                });
                this.elements.suggestionsContainer.style.display = 'block';
                
                // Ensure highlighted item is visible
                const highlighted = this.elements.suggestionsContainer.children[state.highlightedIndex];
                if (highlighted) {
                    const container = this.elements.suggestionsContainer;
                    if (highlighted.offsetTop + highlighted.offsetHeight > container.scrollTop + container.clientHeight) {
                        container.scrollTop = highlighted.offsetTop + highlighted.offsetHeight - container.clientHeight;
                    } else if (highlighted.offsetTop < container.scrollTop) {
                        container.scrollTop = highlighted.offsetTop;
                    }
                }
            } else {
                this.elements.suggestionsContainer.style.display = 'none';
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
            const cluesToUse = state.clues && state.clues.length > 0 ? state.clues : this.clues;
            if (state.hintsRequested > 0) {
                this.elements.hintsContainer.style.display = 'block';
                for (let i = 0; i < state.hintsRequested; i++) {
                    if (cluesToUse[i]) {
                        const li = document.createElement('li');
                        li.textContent = cluesToUse[i];
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

        if (this.elements.hintBtn && state.hintsRequested >= (state.clues ? state.clues.length : this.clues.length)) {
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
        const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
        const safeDate = (typeof state.date === 'string' && dateRegex.test(state.date)) ? state.date : null;

        if (this.elements.clueImage && safeDate) {
            const newSrc = `images/clue-${safeDate}.webp`;
            if (this.elements.clueImage.getAttribute('src') !== newSrc) {
                this.elements.clueImage.src = newSrc;
            }
        }
        if (this.elements.answerImage && safeDate && isWin) {
            const newSrc = `images/answer-${safeDate}.webp`;
            if (this.elements.answerImage.getAttribute('src') !== newSrc) {
                this.elements.answerImage.src = newSrc;
            }
        }
        if (this.elements.viewAnswerLink && safeDate) {
            const newHref = `${safeDate}.html`;
            if (this.elements.viewAnswerLink.getAttribute('href') !== newHref) {
                this.elements.viewAnswerLink.href = newHref;
            }
        }
    }
}
