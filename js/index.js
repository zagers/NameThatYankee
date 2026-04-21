// ABOUTME: Entry point for the main landing page and archive navigation.
// ABOUTME: Initializes the archive gallery and site-wide UI behaviors.

import { checkMatch } from './galleryFilter.js';
import { initScoreDisplay } from './scoreDisplay.js';

export async function initIndex() {
    initScoreDisplay();
    const searchBar = document.getElementById('search-bar');
    const unsolvedFilter = document.getElementById('unsolved-filter');
    const galleryGrid = document.getElementById('gallery-grid');
    const noResultsMessage = document.getElementById('no-results');

    let completedPuzzles = [];
    try {
        const stored = localStorage.getItem('nameThatYankeeCompletedPuzzles');
        completedPuzzles = stored ? JSON.parse(stored) : [];
        if (!Array.isArray(completedPuzzles)) completedPuzzles = [];
    } catch (e) {
        console.warn('Malformed completion data in localStorage, resetting.', e);
        completedPuzzles = [];
    }
    let puzzleData = [];

    // Fetch the pre-generated stats summary for fast searching
    try {
        const response = await fetch(`stats_summary.json?v=${new Date().getTime()}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        puzzleData = await response.json();
    } catch (err) {
        console.error('Failed to load search data:', err);
    }

    // Populate a map for quick DOM access during filtering
    const itemMap = new Map();
    const galleryItems = galleryGrid.querySelectorAll('.gallery-container');
    galleryItems.forEach(item => {
        const href = item.querySelector('.reveal-link')?.getAttribute('href') || '';
        const date = href.match(/(\d{4}-\d{2}-\d{2})/)?.[1] || href.replace('.html', '');
        if (date) itemMap.set(date, item);
    });

    // Read URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const searchParam = urlParams.get('search');
    const decadeParam = urlParams.get('decade');

    if (decadeParam) {
        searchBar.value = decadeParam.endsWith('s') ? decadeParam : decadeParam + 's';
    } else if (searchParam) {
        searchBar.value = searchParam;
    }

    function updateCompletedUI() {
        itemMap.forEach((item, date) => {
            if (completedPuzzles.includes(date)) {
                item.classList.add('completed');
                const quizLink = item.querySelector('.quiz-link');
                if (quizLink) quizLink.classList.add('disabled');
            }
        });
    }

    function markAsCompleted(linkElement) {
        const href = linkElement.getAttribute('href');
        const date = href.match(/(\d{4}-\d{2}-\d{2})/)?.[1] || href.replace('.html', '');
        
        if (date && !completedPuzzles.includes(date)) {
            completedPuzzles.push(date);
            localStorage.setItem('nameThatYankeeCompletedPuzzles', JSON.stringify(completedPuzzles));
            updateCompletedUI();
        }
    }

    // Add click listeners to Reveal text links
    const revealLinks = document.querySelectorAll('.reveal-link');
    revealLinks.forEach(link => {
        link.addEventListener('click', () => markAsCompleted(link));
    });

    // Initial UI update
    updateCompletedUI();

    // --- High-Performance Filtering Logic ---
    function filterGallery() {
        const searchQuery = searchBar.value.toLowerCase().trim();
        const searchTokens = searchQuery.split(/\s+/).filter(t => t.length > 0);
        const showUnsolvedOnly = unsolvedFilter.checked;

        let visibleCount = 0;

        // If we failed to load JSON, fall back to showing everything (or implement DOM fallback)
        if (puzzleData.length === 0) {
            galleryItems.forEach(item => item.style.display = '');
            return;
        }

        puzzleData.forEach(puzzle => {
            const item = itemMap.get(puzzle.date);
            if (!item) return;

            const isCompleted = completedPuzzles.includes(puzzle.date);
            const unsolvedFilterMatch = !showUnsolvedOnly || !isCompleted;
            const searchMatch = checkMatch(puzzle, isCompleted, searchTokens);

            if (unsolvedFilterMatch && searchMatch) {
                item.style.display = '';
                visibleCount++;
            } else {
                item.style.display = 'none';
            }
        });

        noResultsMessage.style.display = (visibleCount === 0 && searchQuery) ? 'block' : 'none';
    }

    searchBar.addEventListener('input', filterGallery);
    unsolvedFilter.addEventListener('change', filterGallery);

    // Initial filter
    if (searchBar.value || unsolvedFilter.checked) {
        filterGallery();
    }
}

if (typeof document !== 'undefined' && !window.__TESTING__) {
    document.addEventListener('DOMContentLoaded', initIndex);
}
