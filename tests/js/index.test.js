import { describe, it, expect, vi, beforeEach } from 'vitest';
import { JSDOM } from 'jsdom';

// Mock the gallery filter function
vi.mock('../../js/galleryFilter.js', () => ({
    checkMatch: vi.fn((puzzle, isCompleted, tokens) => {
        if (tokens.length === 0) return true;
        const searchStr = tokens.join(' ');
        if (puzzle.name.toLowerCase().includes(searchStr)) return true;
        if (puzzle.teams.some(t => t.toLowerCase().includes(searchStr))) return true;
        return false;
    })
}));

import { initIndex } from '../../js/index.js';

describe('Index DOM tests', () => {
    const sampleStats = [
        { date: "2025-05-15", name: "Derek Jeter", teams: ["NYY"], years: ["1995"] },
        { date: "2025-06-01", name: "Aaron Judge", teams: ["NYY"], years: ["2016"] },
        { date: "2026-04-12", name: "Gerrit Cole", teams: ["NYY"], years: ["2020"] }
    ];

    beforeEach(() => {
        // Mock global fetch
        global.fetch = vi.fn().mockImplementation(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve(sampleStats),
            })
        );

        document.body.innerHTML = `
            <div id="score-display">
                Your Score: <span id="total-score">0</span>
                <div id="score-breakdown-container" style="display: none;">
                    <table>
                        <tbody id="breakdown-body"></tbody>
                    </table>
                </div>
            </div>
            <input id="search-bar" type="text" />
            <input type="checkbox" id="unsolved-filter" />
            
            <div id="gallery-grid">
                <div class="gallery-container">
                    <a class="reveal-link" href="2025-05-15.html">Reveal</a>
                    <a class="quiz-link" href="quiz.html?date=2025-05-15">Quiz</a>
                </div>
                <div class="gallery-container">
                    <a class="reveal-link" href="2025-06-01.html">Reveal</a>
                    <a class="quiz-link" href="quiz.html?date=2025-06-01">Quiz</a>
                </div>
                <div class="gallery-container">
                    <a class="reveal-link" href="2026-04-12">Reveal</a>
                    <a class="quiz-link" href="quiz.html?date=2026-04-12">Quiz</a>
                </div>
            </div>
            <div id="no-results" style="display: none;">No Results Found</div>
        `;

        global.localStorage.clear();
        delete window.location;
        window.location = new URL('http://localhost/index.html');
    });

    it('should initialize and display total score from localStorage', async () => {
        global.localStorage.setItem('nameThatYankeeTotalScore', '45');

        await initIndex();

        expect(document.getElementById('total-score').textContent).toBe('45');
    });

    it('should mark completed puzzles visually', async () => {
        global.localStorage.setItem('nameThatYankeeCompletedPuzzles', JSON.stringify(['2025-05-15']));

        await initIndex();

        const containers = document.querySelectorAll('.gallery-container');
        expect(containers[0].classList.contains('completed')).toBe(true);
        expect(containers[0].querySelector('.quiz-link').classList.contains('disabled')).toBe(true);

        // The second one shouldn't be completed
        expect(containers[1].classList.contains('completed')).toBe(false);
    });

    it('should correctly mark completed puzzles with extensionless URLs', async () => {
        global.localStorage.setItem('nameThatYankeeCompletedPuzzles', JSON.stringify(['2026-04-12', '2025-05-15']));

        await initIndex();

        const containers = document.querySelectorAll('.gallery-container');
        // Traditional link (2025-05-15.html) should be marked completed
        expect(containers[0].classList.contains('completed')).toBe(true);
        // Extensionless link (2026-04-12) should be marked completed
        expect(containers[2].classList.contains('completed')).toBe(true);
    });

    it('should filter items when search bar is typed into', async () => {
        await initIndex();
        // Wait for fetch to complete
        await new Promise(resolve => setTimeout(resolve, 0));

        const searchBar = document.getElementById('search-bar');
        searchBar.value = 'judge';

        // Dispatch input event to trigger filterGallery()
        searchBar.dispatchEvent(new Event('input'));

        const containers = document.querySelectorAll('.gallery-container');
        expect(containers[0].style.display).toBe('none'); // Jeter 
        expect(containers[1].style.display).toBe(''); // Judge

        expect(document.getElementById('no-results').style.display).toBe('none');
    });

    it('should show no results message when search matches nothing', async () => {
        await initIndex();
        await new Promise(resolve => setTimeout(resolve, 0));

        const searchBar = document.getElementById('search-bar');
        searchBar.value = 'nomatch';
        searchBar.dispatchEvent(new Event('input'));

        const containers = document.querySelectorAll('.gallery-container');
        expect(containers[0].style.display).toBe('none');
        expect(containers[1].style.display).toBe('none');

        expect(document.getElementById('no-results').style.display).toBe('block');
    });

    it('should filter out completed items when unsolved-filter checkbox is checked', async () => {
        global.localStorage.setItem('nameThatYankeeCompletedPuzzles', JSON.stringify(['2025-05-15']));
        await initIndex();
        await new Promise(resolve => setTimeout(resolve, 0));

        const unsolvedFilter = document.getElementById('unsolved-filter');
        unsolvedFilter.checked = true;
        unsolvedFilter.dispatchEvent(new Event('change'));

        const containers = document.querySelectorAll('.gallery-container');
        expect(containers[0].style.display).toBe('none'); // Jeter (completed)
        expect(containers[1].style.display).toBe(''); // Judge (not completed)
    });
});
