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
}
