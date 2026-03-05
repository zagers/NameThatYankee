/**
 * Processes player data to get team counts.
 * Returns an object with 'labels' and 'data'.
 */
export function processTeamData(playerData) {
    const teamCounts = {};
    playerData.forEach(player => {
        player.teams.forEach(team => {
            if (team !== 'NYY' && !team.endsWith('TM')) {
                teamCounts[team] = (teamCounts[team] || 0) + 1;
            }
        });
    });

    const sortedTeams = Object.entries(teamCounts).sort((a, b) => b[1] - a[1]).slice(0, 10);
    return {
        labels: sortedTeams.map(entry => entry[0]),
        data: sortedTeams.map(entry => entry[1])
    };
}

/**
 * Processes player data to get decade counts.
 */
export function processDecadeData(playerData) {
    const decadeCounts = {};
    playerData.forEach(player => {
        const years = player.years.map(y => {
            const yearNum = typeof y === 'string' ? parseInt(y, 10) : y;
            return isNaN(yearNum) ? null : yearNum;
        }).filter(y => y !== null);

        if (years.length > 0) {
            const uniqueDecades = new Set();
            years.forEach(year => {
                const decade = Math.floor(year / 10) * 10;
                uniqueDecades.add(decade);
            });
            uniqueDecades.forEach(decade => {
                decadeCounts[decade] = (decadeCounts[decade] || 0) + 1;
            });
        }
    });

    const sortedDecades = Object.entries(decadeCounts).sort((a, b) => a[0] - b[0]);
    return {
        labels: sortedDecades.map(entry => `${entry[0]}s`),
        data: sortedDecades.map(entry => entry[1]),
        originalDecades: sortedDecades.map(entry => entry[0])
    };
}

/**
 * Processes incorrect guess data.
 */
export function processGuessesData(guessData) {
    const guessCounts = guessData.reduce((acc, guess) => {
        const name = guess.guessText.toLowerCase();
        acc[name] = (acc[name] || 0) + 1;
        return acc;
    }, {});

    const sortedGuesses = Object.entries(guessCounts).sort((a, b) => b[1] - a[1]).slice(0, 15);
    return {
        labels: sortedGuesses.map(([name, count]) => {
            return name.split(' ').map(n => n.charAt(0).toUpperCase() + n.slice(1)).join(' ');
        }),
        data: sortedGuesses.map(([name, count]) => count)
    };
}

/**
 * Processes toughest puzzle data based on incorrect guesses.
 */
export function processToughestPuzzlesData(guessData) {
    const puzzleCounts = guessData.reduce((acc, guess) => {
        acc[guess.puzzleDate] = (acc[guess.puzzleDate] || 0) + 1;
        return acc;
    }, {});

    const sortedPuzzles = Object.entries(puzzleCounts).sort((a, b) => b[1] - a[1]).slice(0, 5);
    return {
        labels: sortedPuzzles.map(entry => {
            try {
                const dateObj = new Date(entry[0] + 'T00:00:00');
                if (isNaN(dateObj.getTime())) {
                    return entry[0];
                }
                return dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
            } catch (e) {
                return entry[0];
            }
        }),
        data: sortedPuzzles.map(entry => entry[1]),
        originalDates: sortedPuzzles.map(entry => entry[0])
    };
}
