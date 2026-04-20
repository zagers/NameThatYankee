// ABOUTME: Provides interactive filtering and search logic for the puzzle archives.
// ABOUTME: Allows users to browse historical puzzles by player name, date, team, or year.

/**
 * Maps team abbreviations to full names for smarter searching.
 */
const TEAM_NAME_MAP = {
    'NYY': 'new york yankees', 'BOS': 'boston red sox', 'CAL': 'california angels',
    'CHW': 'chicago white sox', 'OAK': 'oakland athletics', 'PHI': 'philadelphia phillies',
    'SDP': 'san diego padres', 'LAD': 'los angeles dodgers', 'CHC': 'chicago cubs',
    'NYM': 'new york mets', 'CIN': 'cincinnati reds', 'ATL': 'atlanta braves',
    'CLE': 'cleveland indians guardians', 'SEA': 'seattle mariners', 'TOR': 'toronto blue jays',
    'TEX': 'texas rangers', 'KCR': 'kansas city royals', 'MIN': 'minnesota twins',
    'DET': 'detroit tigers', 'BAL': 'baltimore orioles', 'TBR': 'tampa bay rays devil',
    'HOU': 'houston astros', 'LAA': 'los angeles angels', 'SFG': 'san francisco giants',
    'ARI': 'arizona diamondbacks', 'COL': 'colorado rockies', 'MIL': 'milwaukee brewers',
    'STL': 'st louis cardinals', 'PIT': 'pittsburgh pirates', 'MIA': 'miami florida marlins',
    'WSN': 'washington nationals', 'MON': 'montreal expos'
};

const MONTH_NAMES = [
    'january', 'february', 'march', 'april', 'may', 'june',
    'july', 'august', 'september', 'october', 'november', 'december'
];

/**
 * Determines if a puzzle matches the current search tokens.
 * @param {Object} puzzle - The puzzle data from stats_summary.json
 * @param {boolean} isCompleted - Whether the user has solved this puzzle
 * @param {string[]} tokens - Lowercased search terms
 * @returns {boolean}
 */
export function checkMatch(puzzle, isCompleted, tokens) {
    if (tokens.length === 0) return true;

    // Pre-calculate date components for precise matching
    const [year, month, day] = puzzle.date.split('-');
    const monthName = MONTH_NAMES[parseInt(month, 10) - 1];
    const dayInt = parseInt(day, 10).toString(); // "09" -> "9"

    return tokens.every(token => {
        // 1. Check Date (Precise matching)
        if (token === year || token === month || token === day || token === dayInt) return true;
        if (monthName?.includes(token)) return true;
        if (puzzle.date === token) return true;
        
        // 2. Check Teams
        const teamMatch = puzzle.teams.some(abbr => {
            if (abbr.toLowerCase() === token) return true;
            const fullName = TEAM_NAME_MAP[abbr];
            return fullName && fullName.includes(token);
        });
        if (teamMatch) return true;
        
        // 3. Check Years & Decades
        if (puzzle.years.includes(token)) return true;
        if (token.endsWith('s')) {
            if (token.length === 3) { // e.g. "90s"
                const decadeDigit = token[0];
                if (puzzle.years.some(y => y.length === 4 && y[2] === decadeDigit)) return true;
            } else if (token.length === 5) { // e.g. "1990s"
                const decadePrefix = token.substring(0, 3);
                if (puzzle.years.some(y => y.startsWith(decadePrefix))) return true;
            }
        }

        // 4. Check Name/Nickname (ONLY if solved)
        if (isCompleted) {
            if (puzzle.name.toLowerCase().includes(token)) return true;
            if (puzzle.nickname && puzzle.nickname.toLowerCase().includes(token)) return true;
        }

        return false;
    });
}

/**
 * Legacy compatibility wrapper for the index.js filtering loop.
 */
export function shouldShowGalleryItem(searchTerms, isCompleted, searchQuery, decadeParam, showUnsolvedOnly, currentYear) {
    // This is no longer used by the new JSON-driven search but kept for API compatibility during transition
    const unsolvedFilterMatch = !showUnsolvedOnly || (showUnsolvedOnly && !isCompleted);
    return unsolvedFilterMatch; 
}
