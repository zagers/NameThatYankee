import { shouldShowGalleryItem } from './galleryFilter.js';
import { initScoreDisplay } from './scoreDisplay.js';

export async function initIndex() {
    initScoreDisplay();
    const searchBar = document.getElementById('search-bar');
    const unsolvedFilter = document.getElementById('unsolved-filter');
    const galleryGrid = document.getElementById('gallery-grid');
    const galleryItems = galleryGrid.querySelectorAll('.gallery-container');
    const noResultsMessage = document.getElementById('no-results');

    let completedPuzzles = JSON.parse(localStorage.getItem('nameThatYankeeCompletedPuzzles')) || [];

    // Read URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const searchParam = urlParams.get('search');
    const decadeParam = urlParams.get('decade');

    // Populate search bar if search parameter is present
    // Clear search bar if decade parameter is present (decade takes precedence)
    if (decadeParam) {
        searchBar.value = '';
    } else if (searchParam) {
        searchBar.value = searchParam;
    }

    function updateCompletedUI() {
        galleryItems.forEach(item => {
            const revealLink = item.querySelector('.reveal-link');
            if (revealLink) {
                const date = revealLink.getAttribute('href').replace('.html', '');
                if (completedPuzzles.includes(date)) {
                    item.classList.add('completed');
                    const quizLink = item.querySelector('.quiz-link');
                    if (quizLink) {
                        quizLink.classList.add('disabled');
                    }
                }
            }
        });
    }

    function markAsCompleted(linkElement) {
        const date = linkElement.getAttribute('href').replace('.html', '');
        if (!completedPuzzles.includes(date)) {
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

    // Removed click listeners for gallery images - images are no longer clickable

    // Initial UI update on page load
    updateCompletedUI();

    // --- Combined Filtering Function ---
    function filterGallery() {
        // Check for decade parameter from URL (only use if search bar is empty)
        const urlParams = new URLSearchParams(window.location.search);
        const decadeParam = urlParams.get('decade');

        const searchQuery = searchBar.value.toLowerCase().trim();
        const searchTokens = searchQuery.split(' ').filter(token => token.length > 0);
        const showUnsolvedOnly = unsolvedFilter.checked;

        // Only use decade parameter if search bar is empty (user typing takes precedence)
        const useDecadeFilter = decadeParam && searchQuery.length === 0;

        const currentYear = new Date().getFullYear();
        let visibleCount = 0;

        galleryItems.forEach(item => {
            const isCompleted = item.classList.contains('completed');
            const searchTerms = item.dataset.searchTerms || '';
            const match = shouldShowGalleryItem(searchTerms, isCompleted, searchQuery, decadeParam, showUnsolvedOnly, currentYear);

            if (match) {
                item.style.display = '';
                visibleCount++;
            } else {
                item.style.display = 'none';
            }
        });

        if (visibleCount === 0 && (searchQuery || decadeParam)) {
            noResultsMessage.style.display = 'block';
        } else {
            noResultsMessage.style.display = 'none';
        }
    }

    // Add event listeners to both the search bar and the checkbox
    searchBar.addEventListener('input', filterGallery);
    unsolvedFilter.addEventListener('change', filterGallery);

    // Trigger filter on page load if URL parameters are present
    if (searchParam || decadeParam) {
        filterGallery();
    }
}

if (typeof document !== 'undefined' && !window.__TESTING__) {
    document.addEventListener('DOMContentLoaded', initIndex);
}
