import { initializeApp } from "https://www.gstatic.com/firebasejs/12.0.0/firebase-app.js";
import { initializeAppCheck, ReCaptchaV3Provider } from "https://www.gstatic.com/firebasejs/12.0.0/firebase-app-check.js";
import { getFirestore, collection, getDocs } from "https://www.gstatic.com/firebasejs/12.0.0/firebase-firestore.js";
import { processTeamData, processDecadeData, processGuessesData, processToughestPuzzlesData } from "./analyticsData.js";

export async function initAnalytics() {
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
    const totalScoreEl = document.getElementById('total-score');

    let totalScore = parseInt(localStorage.getItem('nameThatYankeeTotalScore')) || 0;
    totalScoreEl.textContent = totalScore;

    try {
        console.log("Fetching player data...");
        const indexResponse = await fetch('index.html');
        const indexHtml = await indexResponse.text();
        const parser = new DOMParser();
        const indexDoc = parser.parseFromString(indexHtml, 'text/html');

        const detailPageLinks = Array.from(indexDoc.querySelectorAll('.gallery-item')).map(a => a.getAttribute('href'));

        const allPlayerData = [];
        for (const link of detailPageLinks) {
            const detailResponse = await fetch(link);
            const detailHtml = await detailResponse.text();
            const detailDoc = parser.parseFromString(detailHtml, 'text/html');
            const searchDataEl = detailDoc.getElementById('search-data');
            if (searchDataEl) {
                allPlayerData.push(JSON.parse(searchDataEl.textContent));
            }
        }
        console.log("Player data processed.");

        console.log("Fetching guess data...");
        const guessesSnapshot = await getDocs(collection(db, 'guesses'));
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
                    window.location.href = `index.html?search=${teamAbbreviation}`;
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
                    window.location.href = `index.html?decade=${decade}`;
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
