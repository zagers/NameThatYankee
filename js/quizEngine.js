// ABOUTME: Pure logic engine for the Name That Yankee quiz.
// ABOUTME: Handles scoring, normalization, and game state without DOM dependencies.

/**
 * Normalizes text for comparison by removing accents, converting to lowercase, and trimming.
 * @param {string} text - The text to normalize.
 * @returns {string} The normalized text.
 */
export function normalizeText(text) {
    if (!text) return '';
    return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
}

/**
 * Provides autocomplete suggestions based on player names.
 * @param {string} inputText - The user input to match.
 * @param {string[]} allPlayers - The full list of player names.
 * @param {number} maxSuggestions - Maximum number of suggestions to return.
 * @returns {string[]} Filtered list of player names.
 */
export function getAutocompleteSuggestions(inputText, allPlayers, maxSuggestions = 7) {
    const normalizedInput = normalizeText(inputText);
    if (normalizedInput.length < 2) return [];
    return allPlayers.filter(player => {
        if (typeof player !== 'string') return false;
        return normalizeText(player).startsWith(normalizedInput);
    }).slice(0, maxSuggestions);
}

/**
 * Calculates the score based on how many hints were revealed.
 * @param {number} index - The current hint index (0-based).
 * @returns {number} The score earned.
 */
export function calculateScore(index) {
    const points = [10, 7, 4, 1, 0];
    return points[index] !== undefined ? points[index] : 0;
}

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
        return normalizeText(text);
    }

    calculateScore(index) {
        return calculateScore(index);
    }

    /**
     * Validates a guess and updates the internal state.
     * @param {string} guess - The user's guess.
     * @param {Set<string>} normalizedPlayerSet - A pre-normalized Set of valid player names for O(1) lookups.
     * @returns {Object} The result of the guess.
     */
    submitGuess(guess, normalizedPlayerSet) {
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

        if (normalizedPlayerSet.has(normalizedGuess)) {
            this.previousGuesses.add(normalizedGuess);
            this.currentClueIndex++;
            const gameOver = this.currentClueIndex > this.clues.length;
            if (gameOver) this.isComplete = true;
            
            return {
                status: 'INCORRECT_VALID_PLAYER',
                clueIndex: this.currentClueIndex,
                gameOver: gameOver
            };
        }

        return { status: 'INVALID_PLAYER', clueIndex: this.currentClueIndex };
    }
}
