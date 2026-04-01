import { initializeApp } from "https://www.gstatic.com/firebasejs/12.0.0/firebase-app.js";
import { initializeAppCheck, ReCaptchaV3Provider } from "https://www.gstatic.com/firebasejs/12.0.0/firebase-app-check.js";
import { getFirestore, collection, addDoc, query, where, getDocs, serverTimestamp, doc, getDoc, setDoc } from "https://www.gstatic.com/firebasejs/12.0.0/firebase-firestore.js";
import { normalizeText, validateGuess, calculateScore, getAutocompleteSuggestions } from "./quizEngine.js";
import { initScoreDisplay } from "./scoreDisplay.js";

export async function initQuiz() {
    initScoreDisplay();
    const app = initializeApp(firebaseConfig);
    const appCheck = initializeAppCheck(app, {
        provider: new ReCaptchaV3Provider('6LdhapkrAAAAAIRnXSVdsYXLDC7XThYHEAdEp0Wf'),
        isTokenAutoRefreshEnabled: true
    });
    const db = getFirestore(app);
    const guessesCollection = collection(db, 'guesses')

    const params = new URLSearchParams(window.location.search);

    if (params.get('reset') === 'true') {
        localStorage.removeItem('nameThatYankeeTotalScore');
        localStorage.removeItem('nameThatYankeeCompletedPuzzles');
        localStorage.removeItem('nameThatYankeeScoreBreakdown');
        alert('Your score and quiz history have been reset.');
        window.location.assign('index.html');
        return;
    }

    const date = params.get('date');
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    if (!date || !dateRegex.test(date)) {
        document.getElementById('quiz-area').innerHTML = '<h2>Error: A valid date was not provided.</h2>';
        return; // Stop execution if the date is invalid
    }

    if (!date) {
        document.getElementById('quiz-area').innerHTML = '<h2>Error: No date provided for the quiz.</h2>';
        return;
    }

    const quizTitle = document.getElementById('quiz-title');
    try {
        const dateObj = new Date(date + 'T00:00:00');
        const formattedDate = dateObj.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
        quizTitle.textContent = `Quiz for ${formattedDate}`;
    } catch (e) {
        quizTitle.textContent = 'Name That Yankee Quiz';
    }

    const clueImageEl = document.getElementById('clue-image');
    const guessInputEl = document.getElementById('guess-input');
    const submitBtn = document.getElementById('submit-guess');
    const hintBtn = document.getElementById('request-hint');
    const giveUpBtn = document.getElementById('give-up-btn'); // New button
    const feedbackMsg = document.getElementById('feedback-message');
    const hintsContainer = document.getElementById('hints-container');
    const hintsList = document.getElementById('hints-list');
    const quizArea = document.getElementById('quiz-area');
    const successArea = document.getElementById('success-area');
    const answerImageEl = document.getElementById('answer-image');
    const successHeader = document.getElementById('success-header');
    const successPoints = document.getElementById('success-points');
    const viewAnswerLink = document.getElementById('view-answer-link'); // New link reference
    const totalScoreEl = document.getElementById('total-score');
    const showGuessesBtn = document.getElementById('show-guesses-btn');
    const guessesChartContainer = document.getElementById('guesses-chart-container');
    const guessesChartCanvas = document.getElementById('guessesChart');
    const suggestionsContainer = document.getElementById('suggestions-container');
    const shareBtnSuccess = document.getElementById('share-btn-success');
    const shareBtnFail = document.getElementById('share-btn-fail');
    const shareFailContainer = document.getElementById('share-fail-container');

    // Consolidated Game State
    const gameState = {
        correctAnswer: '',
        nickname: '',
        hints: [],
        hintsRevealed: 0,
        hintsRequested: 0,
        shareEvents: [], // 'hint', 'miss', 'hit'
        isComplete: false,
        points: [10, 7, 4, 1, 0]
    };

    //let allPlayers = [];
    //Initialize the local variable with the global one from all_players.js
    let allPlayers = (typeof ALL_PLAYERS !== 'undefined') ? ALL_PLAYERS : [];
    let highlightedIndex = -1; // For keyboard navigation

    let totalScore = parseInt(localStorage.getItem('nameThatYankeeTotalScore')) || 0;
    let completedPuzzles = JSON.parse(localStorage.getItem('nameThatYankeeCompletedPuzzles')) || [];
    totalScoreEl.textContent = totalScore;

    function updateTotalScore(pointsToAdd, hintsRevealed) {
        totalScore += pointsToAdd;
        localStorage.setItem('nameThatYankeeTotalScore', totalScore);

        if (pointsToAdd > 0) {
            let breakdown;
            try {
                breakdown = JSON.parse(localStorage.getItem('nameThatYankeeScoreBreakdown')) || { "0": 0, "1": 0, "2": 0, "3": 0 };
            } catch (e) {
                breakdown = { "0": 0, "1": 0, "2": 0, "3": 0 };
            }
            const bucket = hintsRevealed.toString();
            if (breakdown.hasOwnProperty(bucket)) {
                breakdown[bucket] = (breakdown[bucket] || 0) + 1;
                localStorage.setItem('nameThatYankeeScoreBreakdown', JSON.stringify(breakdown));
            }
        }

        totalScoreEl.textContent = totalScore;
    }

    function markPuzzleAsComplete() {
        if (!completedPuzzles.includes(date)) {
            completedPuzzles.push(date);
            localStorage.setItem('nameThatYankeeCompletedPuzzles', JSON.stringify(completedPuzzles));
        }
    }

    async function loadQuizData() {
        clueImageEl.src = `images/clue-${date}.webp`;

        if (completedPuzzles.includes(date)) {
            feedbackMsg.textContent = "You have already completed this puzzle.";
            submitBtn.disabled = true;
            hintBtn.disabled = true;
            giveUpBtn.disabled = true;
            guessInputEl.disabled = true;
            shareBtnSuccess.style.display = 'none';
            if (shareFailContainer) shareFailContainer.style.display = 'none';
            gameState.isComplete = true;
        }

        try {
            //     const playerListResponse = await fetch('all_players.json');
            //     allPlayers = (await playerListResponse.json()).map(p => p.toLowerCase());

            const response = await fetch(`${date}.html`);
            const htmlText = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(htmlText, 'text/html');

            const quizDataEl = doc.getElementById('quiz-data');
            if (quizDataEl) {
                const data = JSON.parse(quizDataEl.textContent);
                gameState.correctAnswer = data.answer.toLowerCase();
                gameState.nickname = data.nickname ? data.nickname.toLowerCase() : '';
                gameState.hints = data.hints;
            } else {
                throw new Error('Quiz data not found on detail page.');
            }
        } catch (error) {
            console.error("Failed to load quiz data:", error);
            quizArea.innerHTML = '<h2>Error: Could not load quiz data.</h2>';
        }
    }

    async function saveIncorrectGuess(guess) {
        try {
            await addDoc(guessesCollection, {
                puzzleDate: date,
                guessText: guess,
                timestamp: serverTimestamp()
            });
        } catch (error) {
            console.error("Error writing document: ", error);
        }
    }

    function sanitizeHTML(text) {
        const temp = document.createElement('div');
        if (text) { // Ensure text is not null or undefined
            temp.textContent = text;
        }
        return temp.innerHTML;
    }

    async function showIncorrectGuesses() {
        showGuessesBtn.disabled = true;
        showGuessesBtn.textContent = "Loading...";

        try {
            const q = query(guessesCollection, where("puzzleDate", "==", date));
            const querySnapshot = await getDocs(q);
            const guesses = querySnapshot.docs.map(doc => doc.data().guessText.toLowerCase());

            showGuessesBtn.textContent = "See Common Incorrect Guesses";

            if (guesses.length === 0) {
                guessesChartContainer.innerHTML = '<p>No incorrect guesses have been submitted yet.</p>';
                guessesChartContainer.style.display = 'block';
                return;
            }

            const guessCounts = guesses.reduce((acc, guess) => {
                acc[guess] = (acc[guess] || 0) + 1;
                return acc;
            }, {});

            const sortedGuesses = Object.entries(guessCounts)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 5);

            const labels = sortedGuesses.map(entry =>
                sanitizeHTML(entry[0].split(' ').map(n => n.charAt(0).toUpperCase() + n.slice(1)).join(' '))
            );
            const data = sortedGuesses.map(entry => entry[1]);

            guessesChartContainer.style.display = 'block';

            new Chart(guessesChartCanvas, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Number of Guesses',
                        data: data,
                        backgroundColor: 'rgba(12, 35, 64, 0.8)',
                    }]
                },
                options: {
                    indexAxis: 'y',
                    plugins: {
                        legend: { display: false },
                        title: {
                            display: true,
                            text: 'Most Common Incorrect Guesses'
                        }
                    },
                    scales: {
                        x: {
                            ticks: { beginAtZero: true, stepSize: 1 }
                        }
                    },
                    layout: {
                        padding: {
                            left: 25
                        }
                    }
                }
            });

        } catch (error) {
            console.error("Error getting guesses: ", error);
            guessesChartContainer.innerHTML = '<p>Could not load guess data.</p>';
            guessesChartContainer.style.display = 'block';
        }
    }

    function checkGuess() {
        const userGuess = guessInputEl.value;
        if (!userGuess.trim()) {
            feedbackMsg.textContent = "Please enter a valid guess.";
            feedbackMsg.className = 'incorrect';
            return;
        }

        const validation = validateGuess(userGuess, gameState.correctAnswer, allPlayers, gameState.nickname);

        if (validation.status === 'CORRECT') {
            gameState.shareEvents.push('hit');
            gameState.isComplete = true;
            const pointsEarned = calculateScore(gameState.hintsRevealed, gameState.points);
            answerImageEl.src = `images/answer-${date}.webp`;
            successHeader.textContent = `Correct! The answer is ${gameState.correctAnswer.split(' ').map(n => n.charAt(0).toUpperCase() + n.slice(1)).join(' ')}.`;
            successPoints.textContent = `You earned ${pointsEarned} points!`;
            viewAnswerLink.href = `${date}.html`; // Set the link
            updateTotalScore(pointsEarned, gameState.hintsRevealed);
            markPuzzleAsComplete();
            quizArea.style.display = 'none';
            successArea.style.display = 'block';
        } else {
            if (validation.status === 'INCORRECT_VALID_PLAYER') {
                gameState.shareEvents.push('miss');
                saveIncorrectGuess(userGuess.trim().toLowerCase());
                if (gameState.hintsRevealed >= gameState.hints.length) {
                    endQuizAndShowAnswer();
                } else {
                    feedbackMsg.textContent = "Incorrect. Try again!";
                    feedbackMsg.className = 'incorrect';
                    guessInputEl.value = '';
                    revealHint();
                }
            } else {
                feedbackMsg.textContent = "That is not a valid MLB player, guess again";
                feedbackMsg.className = 'incorrect';
                guessInputEl.value = '';
            }
        }
    }

    function revealHint(isManual = false) {
        if (gameState.hintsRevealed < gameState.hints.length) {
            hintsContainer.style.display = 'block';
            const newHint = document.createElement('li');
            newHint.textContent = gameState.hints[gameState.hintsRevealed];
            hintsList.appendChild(newHint);
            gameState.hintsRevealed++;
            if (isManual) {
                gameState.hintsRequested++;
                gameState.shareEvents.push('hint');
            }
        }

        if (gameState.hintsRevealed >= gameState.hints.length) {
            hintBtn.disabled = true;
            if (!submitBtn.disabled) {
                feedbackMsg.textContent = 'All hints revealed! One guess remaining.';
                feedbackMsg.className = '';
            }
        }
    }

    // NEW: Function to end the quiz and show the answer
    function endQuizAndShowAnswer() {
        gameState.isComplete = true;
        const formattedAnswer = gameState.correctAnswer.split(' ').map(n => n.charAt(0).toUpperCase() + n.slice(1)).join(' ');
        feedbackMsg.innerHTML = `Sorry, the correct answer was ${formattedAnswer}.<p> <a href="${date}.html">Click here to learn more about ${formattedAnswer}</a>`;
        submitBtn.disabled = true;
        hintBtn.disabled = true;
        giveUpBtn.disabled = true;
        guessInputEl.disabled = true;
        if (shareFailContainer) shareFailContainer.style.display = 'block';
        markPuzzleAsComplete();
    }

    // --- Autocomplete Logic ---
    guessInputEl.addEventListener('input', () => {
        suggestionsContainer.innerHTML = '';

        const matches = getAutocompleteSuggestions(guessInputEl.value, allPlayers);

        if (matches.length > 0) {
            matches.forEach(match => {
                const suggestionItem = document.createElement('div');
                suggestionItem.textContent = match;
                suggestionItem.classList.add('suggestion-item');
                suggestionItem.addEventListener('click', () => {
                    guessInputEl.value = match;
                    suggestionsContainer.innerHTML = '';
                    suggestionsContainer.style.display = 'none';
                });
                suggestionsContainer.appendChild(suggestionItem);
            });
            suggestionsContainer.style.display = 'block';
        } else {
            suggestionsContainer.style.display = 'none';
        }
    });

    // --- UPDATED: Keyboard Navigation Logic ---
    guessInputEl.addEventListener('keydown', (e) => {
        const suggestions = suggestionsContainer.querySelectorAll('.suggestion-item');

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (suggestions.length > 0) {
                highlightedIndex = (highlightedIndex + 1) % suggestions.length;
                updateHighlight(suggestions);
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (suggestions.length > 0) {
                highlightedIndex = (highlightedIndex - 1 + suggestions.length) % suggestions.length;
                updateHighlight(suggestions);
            }
        } else if (e.key === 'Enter') {
            e.preventDefault(); // Always prevent default on Enter
            if (highlightedIndex > -1 && suggestions[highlightedIndex]) {
                // A suggestion is highlighted, so select it and submit
                guessInputEl.value = suggestions[highlightedIndex].textContent;
                suggestionsContainer.innerHTML = '';
                suggestionsContainer.style.display = 'none';
                checkGuess(); // Submit the guess
            } else {
                // No suggestion is highlighted, just submit the current text
                checkGuess();
            }
        }
    });

    function updateHighlight(suggestions) {
        suggestions.forEach((item, index) => {
            if (index === highlightedIndex) {
                item.classList.add('highlighted');
                // THE FIX: Manually control the container's scroll position
                const container = suggestionsContainer;
                const itemTop = item.offsetTop;
                const itemBottom = itemTop + item.offsetHeight;
                const containerTop = container.scrollTop;
                const containerBottom = containerTop + container.clientHeight;

                if (itemBottom > containerBottom) {
                    container.scrollTop = itemBottom - container.clientHeight;
                } else if (itemTop < containerTop) {
                    container.scrollTop = itemTop;
                }
            } else {
                item.classList.remove('highlighted');
            }
        });
    }

    function generateShareText(dateStr, state) {
        const isWin = state.shareEvents.includes('hit');
        const pointsEarned = isWin ? calculateScore(state.hintsRevealed, state.points) : 0;
        
        // Map events to emojis: hint=📘, miss=🟥, hit=🟩
        const emojiMap = {
            'hint': '📘',
            'miss': '🟥',
            'hit': '🟩'
        };
        const emojiGrid = state.shareEvents.map(event => emojiMap[event]).join('');

        const shareText = `Name That Yankee - ${dateStr}\n` +
            `⚾ Score: ${pointsEarned} pts\n` +
            `💡 Hints used: ${state.hintsRequested}\n` +
            `${emojiGrid}\n\n` +
            `${window.location.href}`;
        
        return shareText;
    }

    async function copyShareText(btn, dateStr, state) {
        const text = generateShareText(dateStr, state);
        
        if (navigator.share) {
            try {
                // On iOS Safari, providing a 'title' or 'url' alongside 'text' that contains a URL 
                // often causes the browser to ignore the 'text' field entirely.
                // Omitting 'title' and 'url' ensures the full "Wordle-style" text block is shared.
                await navigator.share({
                    text: text
                });
                return; // Successfully shared using native dialog
            } catch (err) {
                // If user cancels the share dialog, it throws an AbortError.
                // We shouldn't alert on cancellation, just silently return.
                if (err.name === 'AbortError') return;
                console.error('Native share failed, falling back to clipboard: ', err);
                // Fall through to clipboard approach
            }
        }

        try {
            await navigator.clipboard.writeText(text);
            const originalText = btn.textContent;
            btn.textContent = 'Copied! ✅';
            btn.classList.add('copied');
            setTimeout(() => {
                btn.textContent = originalText;
                btn.classList.remove('copied');
            }, 2000);
        } catch (err) {
            console.error('Failed to copy: ', err);
            alert('Could not copy to clipboard. Please try again.');
        }
    }

    submitBtn.addEventListener('click', checkGuess);
    hintBtn.addEventListener('click', () => revealHint(true));
    giveUpBtn.addEventListener('click', endQuizAndShowAnswer); // New event listener
    showGuessesBtn.addEventListener('click', showIncorrectGuesses);
    
    // Get formatted date once for sharing
    let formattedDate = '';
    try {
        const dateObj = new Date(date + 'T00:00:00');
        formattedDate = dateObj.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    } catch (e) {
        formattedDate = date;
    }

    shareBtnSuccess.addEventListener('click', () => copyShareText(shareBtnSuccess, formattedDate, gameState));
    shareBtnFail.addEventListener('click', () => copyShareText(shareBtnFail, formattedDate, gameState));


    await loadQuizData();
}

if (typeof document !== 'undefined' && !window.__TESTING__) {
    document.addEventListener('DOMContentLoaded', initQuiz);
}
