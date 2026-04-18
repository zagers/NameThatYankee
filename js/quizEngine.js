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
