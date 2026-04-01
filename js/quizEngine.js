/**
 * Normalizes text by removing diacritics and converting to lowercase.
 */
export function normalizeText(text) {
    if (!text) return '';
    return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

/**
 * Validates a user's guess against the correct answer and a list of normalized player names.
 * Returns an object indicating the result.
 */
export function validateGuess(userGuess, correctAnswer, normalizedPlayers, nickname = "") {
    const normalizedGuess = normalizeText(userGuess).trim();
    const normalizedAnswer = normalizeText(correctAnswer).trim();
    const normalizedNickname = normalizeText(nickname).trim();

    if (normalizedGuess === normalizedAnswer || (normalizedNickname && normalizedGuess === normalizedNickname)) {
        return { status: 'CORRECT' };
    }

    const isPlayerInList = normalizedPlayers.includes(normalizedGuess);

    if (isPlayerInList) {
        return { status: 'INCORRECT_VALID_PLAYER' };
    }

    return { status: 'INVALID_PLAYER' };
}

/**
 * Calculates the score based on how many hints were used.
 */
export function calculateScore(hintsRevealed, pointsArray) {
    return pointsArray[hintsRevealed] !== undefined ? pointsArray[hintsRevealed] : 0;
}

/**
 * Gets a list of autocomplete suggestions based on the user's input.
 */
export function getAutocompleteSuggestions(inputText, allPlayers, maxSuggestions = 7) {
    const normalizedInput = normalizeText(inputText);

    if (normalizedInput.length < 2) {
        return [];
    }

    return allPlayers.filter(player => {
        if (typeof player !== 'string') return false;
        return normalizeText(player).startsWith(normalizedInput);
    }).slice(0, maxSuggestions);
}
