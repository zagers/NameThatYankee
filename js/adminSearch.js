// ABOUTME: Pure, DOM-free search and matching helpers for the admin page.
// ABOUTME: Powers name/nickname/fuzzy searches across the puzzle catalog.

export function normalizeAdminText(text) {
    if (!text) return '';
    return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
}

export function levenshtein(a, b) {
    const m = a.length;
    const n = b.length;
    if (m === 0) return n;
    if (n === 0) return m;
    let prev = Array.from({ length: n + 1 }, (_, i) => i);
    for (let i = 1; i <= m; i++) {
        let cur = [i];
        for (let j = 1; j <= n; j++) {
            const cost = a[i - 1] === b[j - 1] ? 0 : 1;
            cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost);
        }
        prev = cur;
    }
    return prev[n];
}

function bestWordScore(token, fieldWords) {
    let best = 0;
    for (const word of fieldWords) {
        if (!word) continue;
        if (word === token) best = Math.max(best, 10);
        else if (word.startsWith(token)) best = Math.max(best, 6);
        else if (word.includes(token)) best = Math.max(best, 4);
        else if (token.length >= 4 && levenshtein(token, word) <= 1) best = Math.max(best, 2);
    }
    return best;
}

function collectFieldWords(puzzle, fields) {
    const words = [];
    for (const field of fields) {
        const value = Array.isArray(puzzle[field]) ? puzzle[field].join(' ') : String(puzzle[field] || '');
        for (const word of normalizeAdminText(value).split(/\s+/)) {
            if (word) words.push(word);
        }
    }
    return words;
}

/**
 * Precompute the normalized, tokenized field words for each puzzle so searches
 * against the same catalog don't re-normalize on every keystroke.
 * Returns entries of the shape `{ puzzle, words }`, which searchPuzzles accepts.
 *
 * @param {Array<object>} puzzles
 * @param {string[]} [fields=["name","nicknames"]]
 * @returns {Array<{puzzle: object, words: string[]}>}
 */
export function buildSearchIndex(puzzles, fields = ['name', 'nicknames']) {
    return puzzles.map(puzzle => ({ puzzle, words: collectFieldWords(puzzle, fields) }));
}

export function isSearchIndex(input) {
    if (!Array.isArray(input) || input.length === 0) return false;
    const first = input[0];
    return Boolean(first && first.puzzle && Array.isArray(first.words));
}

/**
 * Search puzzles by name/nickname using tokenized AND semantics.
 * Each token must match at least one field word. Tokens are scored:
 *   exact word hit = 10, prefix = 6, substring = 4, fuzzy (≤1 edit, len≥4) = 2.
 * Returns results sorted by score descending, best first.
 *
 * May be called with raw puzzles or a prebuilt index from buildSearchIndex().
 *
 * @param {Array<object>} puzzles
 * @param {string} query
 * @param {string[]} [fields=["name","nicknames"]]
 * @returns {Array<{puzzle: object, score: number}>}
 */
export function searchPuzzles(puzzles, query, fields = ['name', 'nicknames']) {
    const tokens = normalizeAdminText(query).split(/\s+/).filter(Boolean);
    if (tokens.length === 0) return [];

    const index = isSearchIndex(puzzles) ? puzzles : buildSearchIndex(puzzles, fields);
    const results = [];
    for (const entry of index) {
        const fieldWords = entry.words;
        let tokenScore = 0;
        let matched = true;
        for (const token of tokens) {
            const score = bestWordScore(token, fieldWords);
            if (score === 0) { matched = false; break; }
            tokenScore += score;
        }
        if (matched) results.push({ puzzle: entry.puzzle, score: tokenScore });
    }

    results.sort((a, b) => b.score - a.score);
    return results;
}
