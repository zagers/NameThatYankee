// ABOUTME: Manages the logic for the site-wide analytics and performance dashboard.
// ABOUTME: Handles data visualization and summary statistics for trivia puzzles.

import { initializeApp } from "https://www.gstatic.com/firebasejs/12.0.0/firebase-app.js";
import { initializeAppCheck, ReCaptchaV3Provider } from "https://www.gstatic.com/firebasejs/12.0.0/firebase-app-check.js";
import { getFirestore, collection, getDocs } from "https://www.gstatic.com/firebasejs/12.0.0/firebase-firestore.js";
import { processTeamData, processDecadeData, processGuessesData, processToughestPuzzlesData } from "./analyticsData.js";
import { initScoreDisplay } from "./scoreDisplay.js";

export async function initAnalytics() {
    initScoreDisplay();
    // --- Initialize Firebase and App Check with modern API ---
    console.log("Initializing Firebase with modern API...");
    const app = initializeApp(firebaseConfig);
    const appCheck = initializeAppCheck(app, {
        provider: new ReCaptchaV3Provider('6LdhapkrAAAAAIRnXSVdsYXLDC7XThYHEAdEp0Wf'),
        isTokenAutoRefreshEnabled: true
    });
    const db = getFirestore(app);
    console.log("Firebase initialized successfully with modern API");

    const loadingMessage = document.getElementById('loading-message');
    const analyticsContent = document.getElementById('analytics-content');

    try {
        console.log("Fetching player data and guess statistics...");
        const [statsResponse, guessesSnapshot] = await Promise.all([
            fetch(`stats_summary.json?v=${new Date().getTime()}`),
            getDocs(collection(db, 'guesses'))
        ]);

        if (!statsResponse.ok) {
            throw new Error(`Failed to fetch stats_summary.json: ${statsResponse.statusText}`);
        }
        
        const allPlayerData = await statsResponse.json();
        console.log(`Successfully loaded ${allPlayerData.length} players from summary.`);

        const allGuesses = guessesSnapshot.docs.map(doc => doc.data());
        console.log("Guess data processed.");

        generateTeamChart(allPlayerData);
        generateDecadeChart(allPlayerData);
        generateGuessesChart(allGuesses);
        generateToughestPuzzlesChart(allGuesses);

        loadingMessage.style.display = 'none';
        analyticsContent.classList.remove('hidden');

    } catch (error) {
        console.error("Error loading analytics:", error);
        loadingMessage.innerHTML = '<p class="text-xl font-semibold text-red-600">Could not load analytics data.</p>';
    }
}

if (typeof document !== 'undefined' && !window.__TESTING__) {
    document.addEventListener('DOMContentLoaded', initAnalytics);
}

// --- Chart Generation Functions ---
function generateTeamChart(playerData) {
    const { labels, data } = processTeamData(playerData);

    new Chart(document.getElementById('teamChart'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Players',
                data: data,
                backgroundColor: 'rgba(20, 44, 86, 0.7)',
                borderColor: 'rgba(20, 44, 86, 1)',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        footer: function () {
                            return 'Click to filter puzzles by this team';
                        }
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const clickedIndex = elements[0].index;
                    const teamAbbreviation = labels[clickedIndex];
                    window.location.href = `/?search=${teamAbbreviation}`;
                }
            }
        }
    });
}

function generateDecadeChart(playerData) {
    const { labels, data, originalDecades } = processDecadeData(playerData);

    new Chart(document.getElementById('decadeChart'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Players',
                data: data,
                backgroundColor: 'rgba(196, 30, 58, 0.7)',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        footer: function () {
                            return 'Click to filter puzzles from this decade';
                        }
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const clickedIndex = elements[0].index;
                    const decade = originalDecades[clickedIndex]; // e.g., 1980
                    window.location.href = `/?decade=${decade}`;
                }
            }
        }
    });
}

function generateGuessesChart(guessData) {
    const { labels, data } = processGuessesData(guessData);

    new Chart(document.getElementById('guessesChart'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Guesses',
                data: data,
                backgroundColor: 'rgba(12, 35, 64, 0.7)',
                borderColor: 'rgba(12, 35, 64, 1)',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: function (context) {
                            return context[0].label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Incorrect Guesses'
                    }
                }
            }
        }
    });
}

function generateToughestPuzzlesChart(guessData) {
    const { labels, data, originalDates } = processToughestPuzzlesData(guessData);

    new Chart(document.getElementById('toughestPuzzlesChart'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Total Incorrect Guesses',
                data: data,
                backgroundColor: 'rgba(0, 90, 156, 0.7)',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        footer: function () {
                            return 'Click to view this puzzle';
                        }
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const clickedIndex = elements[0].index;
                    const date = originalDates[clickedIndex]; // YYYY-MM-DD format
                    window.location.href = `${date}.html`;
                }
            }
        }
    });
}
