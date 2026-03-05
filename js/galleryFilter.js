/**
 * Determines if a gallery item should be visible based on search and filter criteria.
 */
export function shouldShowGalleryItem(searchTerms, isCompleted, searchQuery, decadeParam, showUnsolvedOnly, currentYear) {
    const searchTokens = searchQuery.trim().toLowerCase().split(' ').filter(token => token.length > 0);
    const useDecadeFilter = decadeParam && searchTokens.length === 0;

    const unsolvedFilterMatch = !showUnsolvedOnly || (showUnsolvedOnly && !isCompleted);

    let dataTokens = searchTerms.toLowerCase().replace(/,/g, '').split(/\s+/).filter(t => t.length > 0);
    const augmentedTokens = [];
    dataTokens.forEach(token => {
        if (!isNaN(token) && token.startsWith('0') && token.length > 1) {
            augmentedTokens.push(parseInt(token, 10).toString());
        }
    });
    dataTokens = dataTokens.concat(augmentedTokens);

    let textSearchMatch = false;

    if (useDecadeFilter) {
        const decadeStart = parseInt(decadeParam);
        if (!isNaN(decadeStart)) {
            const decadeEnd = Math.min(decadeStart + 9, currentYear);
            const decadeYears = [];
            for (let year = decadeStart; year <= decadeEnd; year++) {
                decadeYears.push(year.toString());
            }

            const yearTokens = dataTokens.filter(token => {
                const yearNum = parseInt(token, 10);
                return !isNaN(yearNum) && yearNum >= 1900 && yearNum <= 2100 && token.length === 4;
            });

            const puzzleDateYear = currentYear.toString();
            let playerYears = yearTokens;
            if (yearTokens.length > 0 && yearTokens[0] === puzzleDateYear) {
                playerYears = yearTokens.slice(1);
            }

            textSearchMatch = decadeYears.length > 0 && decadeYears.some(year => playerYears.includes(year));
        }
    } else {
        textSearchMatch = searchTokens.length === 0 || searchTokens.every(token => dataTokens.includes(token));
    }

    return unsolvedFilterMatch && textSearchMatch;
}
