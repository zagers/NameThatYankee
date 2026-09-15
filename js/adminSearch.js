// ABOUTME: Provides fuzzy search over admin_data.json puzzle records.
// ABOUTME: Exports normalizeAdminText, levenshtein, and searchPuzzles for the admin search page.

/**
 * Normalize text for comparison: lowercase, strip diacritics, trim.
 * @param {string|null|undefined} text
 * @returns {string}
 */
export function normalizeAdminText(text) {
    if (text == null) return '';
    return text
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
        .trim();
}

/**
 * Standard Levenshtein distance between two strings.
 * @param {string} a
 * @param {string} b
 * @returns {number}
 */
export function levenshtein(a, b) {
    const lenA = a.length;
    const lenB = b.length;
    const dp = Array.from({ length: lenA + 1 }, () => new Array(lenB + 1).fill(0));
    for (let i = 0; i <= lenA; i++) dp[i][0] = i;
    for (let j = 0; j <= lenB; j++) dp[0][j] = j;
    for (let i = 1; i <= lenA; i++) {
        for (let j = 1; j <= lenB; j++) {
            const cost = a[i - 1] === b[j - 1] ? 0 : 1;
            dp[i][j] = Math.min(
                dp[i - 1][j] + 1,       // deletion
                dp[i][j - 1] + 1,       // insertion
                dp[i - 1][j - 1] + cost // substitution
            );
        }
    }
    return dp[lenA][lenB];
}

/**
 * Search puzzles by name/nickname/career_totals using Levenshtein fuzzy matching.
 * Returns results sorted by score (0 = exact match), filtered to those within threshold.
 *
 * @param {Array<{name: string, nicknames: string[], career_totals: Record<string, string>}>} puzzles
 * @param {string} query
 * @param {number} [threshold=3] - max edit distance to consider a match
 * @returns {Array<{puzzle: object, score: number}>}
 */
export function searchPuzzles(puzzles, query, threshold = 3) {
    if (!query) return [];
    const q = normalizeAdminText(query);
    if (!q) return [];

    const results = [];

    for (const puzzle of puzzles) {
        let best = Infinity;

        // Check name
        const name = normalizeAdminText(puzzle.name || '');
        if (name === q) { best = 0; }
        else {
            const d = levenshtein(q, name);
            if (d < best) best = d;
        }

        // Check nicknames
        if (puzzle.nicknames) {
            for (const nick of puzzle.nicknames) {
                const n = normalizeAdminText(nick);
                if (n === q) { best = 0; break; }
                const d = levenshtein(q, n);
                if (d < best) best = d;
            }
        }

        // Check career_totals values (e.g. "62.0")
        if (puzzle.career_totals) {
            for (const val of Object.values(puzzle.career_totals)) {
                const v = normalizeAdminText(String(val));
                if (v === q) { best = 0; break; }
                const d = levenshtein(q, v);
                if (d < best) best = d;
            }
        }

        if (best <= threshold) {
            results.push({ puzzle, score: best });
        }
    }

    results.sort((a, b) => a.score - b.score);
    return results;
}
