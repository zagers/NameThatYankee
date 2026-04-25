/* global Chart */
// ABOUTME: Orchestrator for the interactive quiz interface.
// ABOUTME: Manages state transitions and coordinates between logic, UI, and sharing modules.

import { initializeApp } from "https://www.gstatic.com/firebasejs/12.0.0/firebase-app.js";
import { initializeAppCheck, ReCaptchaV3Provider } from "https://www.gstatic.com/firebasejs/12.0.0/firebase-app-check.js";
import { getFirestore, collection, addDoc, query, where, getDocs, serverTimestamp } from "https://www.gstatic.com/firebasejs/12.0.0/firebase-firestore.js";
import { QuizEngine, normalizeText, getAutocompleteSuggestions } from "./quizEngine.js";
import { initScoreDisplay } from "./scoreDisplay.js";
import { QuizUI } from "./quizUI.js";
import { copyShareText } from "./quizShare.js";

export function createInitialState(date) {
    return {
        status: 'loading',
        date: date,
        playerIdentity: '',
        guesses: [],
        score: 100,
        hintsRequested: 0,
        shareEvents: [],
        isComplete: false,
        finalScore: 0,
        error: null,
        feedback: '',
        feedbackClass: '',
        isProcessing: false,
        totalScore: 0,
        showChart: false
    };
}

export function reducer(state, action) {
    switch (action.type) {
        case 'INIT_DATA':
            return {
                ...state,
                status: 'active',
                playerIdentity: action.payload.playerIdentity,
            };
        case 'GUESS_RESULT': {
            const { status, score, guess, gameOver } = action.payload;
            const newGuesses = guess ? [...state.guesses, guess] : state.guesses;
            const newShareEvents = [...state.shareEvents];
            
            if (status === 'CORRECT') {
                newShareEvents.push('hit');
                return {
                    ...state,
                    status: 'complete',
                    guesses: newGuesses,
                    shareEvents: newShareEvents,
                    isComplete: true,
                    finalScore: score,
                    feedback: '',
                    error: null
                };
            } else if (status === 'INCORRECT_VALID_PLAYER' || status === 'GIVE_UP' || status === 'ALREADY_COMPLETE') {
                if (status === 'INCORRECT_VALID_PLAYER') newShareEvents.push('miss');
                
                if (gameOver) {
                    return {
                        ...state,
                        status: 'complete',
                        guesses: newGuesses,
                        shareEvents: newShareEvents,
                        isComplete: true,
                        finalScore: 0,
                        error: null
                    };
                }
                return {
                    ...state,
                    guesses: newGuesses,
                    shareEvents: newShareEvents,
                    error: null
                };
            }
            return state;
        }
        case 'REVEAL_HINT':
            return {
                ...state,
                hintsRequested: state.hintsRequested + 1,
                shareEvents: [...state.shareEvents, 'hint'],
                error: null
            };
        case 'SET_ERROR':
            return {
                ...state,
                error: action.payload,
                feedback: ''
            };
        case 'UPDATE_FEEDBACK':
            return {
                ...state,
                feedback: action.payload.message,
                feedbackClass: action.payload.className,
                error: null
            };
        case 'SET_PROCESSING':
            return {
                ...state,
                isProcessing: action.payload
            };
        case 'UPDATE_TOTAL_SCORE':
            return {
                ...state,
                totalScore: action.payload
            };
        case 'SHOW_CHART':
            return {
                ...state,
                showChart: true
            };
        default:
            return state;
    }
}

export async function initQuiz() {
    initScoreDisplay();
    const app = initializeApp(firebaseConfig);
    initializeAppCheck(app, {
        provider: new ReCaptchaV3Provider('6LdhapkrAAAAAIRnXSVdsYXLDC7XThYHEAdEp0Wf'),
        isTokenAutoRefreshEnabled: true
    });
    const db = getFirestore(app);
    const guessesCollection = collection(db, 'guesses');

    const params = new URLSearchParams(window.location.search);
    const date = params.get('date');

    if (params.get('reset') === 'true') {
        localStorage.removeItem('nameThatYankeeTotalScore');
        localStorage.removeItem('nameThatYankeeCompletedPuzzles');
        localStorage.removeItem('nameThatYankeeScoreBreakdown');
        alert('Your score and quiz history have been reset.');
        window.location.assign('/');
        return;
    }

    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    if (!date || !dateRegex.test(date)) {
        document.getElementById('quiz-area').innerHTML = '<h2>Error: A valid date was not provided.</h2>';
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

    let gameState = createInitialState(date);
    let ui = null;
    let engine;
    let allPlayers = (typeof ALL_PLAYERS !== 'undefined') ? ALL_PLAYERS : [];
    const normalizedPlayerSet = new Set(allPlayers.map(p => normalizeText(p)));
    let highlightedIndex = -1;

    let totalScore = parseInt(localStorage.getItem('nameThatYankeeTotalScore')) || 0;
    let completedPuzzles = JSON.parse(localStorage.getItem('nameThatYankeeCompletedPuzzles')) || [];

    function dispatch(action) {
        gameState = reducer(gameState, action);
        if (ui) ui.render(gameState);
    }

    dispatch({ type: 'UPDATE_TOTAL_SCORE', payload: totalScore });

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
        dispatch({ type: 'UPDATE_TOTAL_SCORE', payload: totalScore });
    }

    function markPuzzleAsComplete() {
        if (!completedPuzzles.includes(date)) {
            completedPuzzles.push(date);
            localStorage.setItem('nameThatYankeeCompletedPuzzles', JSON.stringify(completedPuzzles));
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

    async function showIncorrectGuesses() {
        dispatch({ type: 'SET_PROCESSING', payload: true });
        dispatch({ type: 'SHOW_CHART' }); // Show container early
        
        try {
            const q = query(guessesCollection, where("puzzleDate", "==", date));
            const querySnapshot = await getDocs(q);
            const guesses = querySnapshot.docs.map(doc => doc.data().guessText.toLowerCase());

            if (guesses.length === 0) {
                dispatch({ type: 'UPDATE_FEEDBACK', payload: { message: "No incorrect guesses have been submitted yet.", className: '' } });
                dispatch({ type: 'SET_PROCESSING', payload: false });
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
                entry[0].split(' ').map(n => n.charAt(0).toUpperCase() + n.slice(1)).join(' ')
            );
            const data = sortedGuesses.map(entry => entry[1]);

            if (window.Chart) {
                new Chart(ui.elements.guessesChartCanvas, {
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
                        }
                    }
                });
            }

        } catch (error) {
            console.error("Error getting guesses: ", error);
            dispatch({ type: 'SET_ERROR', payload: "Could not load guess data." });
        }
        dispatch({ type: 'SET_PROCESSING', payload: false });
    }

    async function loadQuizData() {
        if (completedPuzzles.includes(date)) {
            dispatch({ type: 'SET_ERROR', payload: "You have already completed this puzzle." });
            dispatch({ type: 'GUESS_RESULT', payload: { status: 'ALREADY_COMPLETE', score: 0, guess: '', gameOver: true } });
        }

        try {
            const response = await fetch(`${date}.html`);
            const htmlText = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(htmlText, 'text/html');

            const quizDataEl = doc.getElementById('quiz-data');
            if (quizDataEl) {
                const data = JSON.parse(quizDataEl.textContent);
                const formattedName = data.answer.split(' ').map(n => n.charAt(0).toUpperCase() + n.slice(1)).join(' ');
                dispatch({ type: 'INIT_DATA', payload: { playerIdentity: formattedName } });
                engine = new QuizEngine(data.answer, data.hints, data.nickname || '');
                ui = new QuizUI(data.hints);
                ui.render(gameState);
                setupEventListeners();
            } else {
                throw new Error('Quiz data not found on detail page.');
            }
        } catch (error) {
            console.error("Failed to load quiz data:", error);
            document.getElementById('quiz-area').innerHTML = '<h2>Error: Could not load quiz data.</h2>';
        }
    }

    function checkGuess() {
        const userGuess = ui.elements.guessInput.value;
        if (!userGuess.trim()) {
            dispatch({ type: 'UPDATE_FEEDBACK', payload: { message: "Please enter a valid guess.", className: 'incorrect' } });
            return;
        }

        const result = engine.submitGuess(userGuess, normalizedPlayerSet);

        if (result.status === 'CORRECT') {
            dispatch({ type: 'GUESS_RESULT', payload: { status: result.status, score: result.score, guess: userGuess, gameOver: result.gameOver } });
            updateTotalScore(result.score, result.clueIndex);
            markPuzzleAsComplete();
        } else if (result.status === 'INCORRECT_VALID_PLAYER') {
            saveIncorrectGuess(userGuess.trim().toLowerCase());
            if (result.gameOver) {
                endQuizAndShowAnswer();
            } else {
                dispatch({ type: 'GUESS_RESULT', payload: { status: result.status, score: result.score, guess: userGuess, gameOver: result.gameOver } });
                dispatch({ type: 'UPDATE_FEEDBACK', payload: { message: "Incorrect. Try again!", className: 'incorrect' } });
                ui.elements.guessInput.value = '';
                revealHint();
            }
        } else if (result.status === 'DUPLICATE_GUESS') {
            dispatch({ type: 'UPDATE_FEEDBACK', payload: { message: "You already guessed that player!", className: 'incorrect' } });
        } else if (result.status === 'INVALID_PLAYER') {
            dispatch({ type: 'UPDATE_FEEDBACK', payload: { message: "That is not a valid MLB player, guess again", className: 'incorrect' } });
            ui.elements.guessInput.value = '';
        }
    }

    function revealHint(isManual = false) {
        if (isManual) {
            engine.currentClueIndex++;
            dispatch({ type: 'REVEAL_HINT' });
        } else {
            gameState.hintsRequested = engine.currentClueIndex;
            ui.render(gameState);
        }
    }

    function endQuizAndShowAnswer() {
        markPuzzleAsComplete();
        const formattedAnswer = gameState.playerIdentity;
        const feedback = `Sorry, the correct answer was ${formattedAnswer}.<p> <a href="${date}.html">Click here to learn more about ${formattedAnswer}</a>`;
        dispatch({ type: 'UPDATE_FEEDBACK', payload: { message: feedback, className: '' } });
        dispatch({ type: 'GUESS_RESULT', payload: { status: 'GIVE_UP', score: 0, guess: 'Gave Up', gameOver: true } });
    }

    function setupEventListeners() {
        ui.elements.submitBtn.addEventListener('click', checkGuess);
        ui.elements.hintBtn.addEventListener('click', () => revealHint(true));
        ui.elements.giveUpBtn.addEventListener('click', endQuizAndShowAnswer);
        ui.elements.showGuessesBtn.addEventListener('click', showIncorrectGuesses);

        ui.elements.guessInput.addEventListener('input', () => {
            ui.elements.suggestionsContainer.innerHTML = '';
            const matches = getAutocompleteSuggestions(ui.elements.guessInput.value, allPlayers);
            if (matches.length > 0) {
                matches.forEach(match => {
                    const item = document.createElement('div');
                    item.textContent = match;
                    item.classList.add('suggestion-item');
                    item.addEventListener('click', () => {
                        ui.elements.guessInput.value = match;
                        ui.elements.suggestionsContainer.innerHTML = '';
                        ui.elements.suggestionsContainer.style.display = 'none';
                    });
                    ui.elements.suggestionsContainer.appendChild(item);
                });
                ui.elements.suggestionsContainer.style.display = 'block';
            } else {
                ui.elements.suggestionsContainer.style.display = 'none';
            }
        });

        ui.elements.guessInput.addEventListener('keydown', (e) => {
            const suggestions = ui.elements.suggestionsContainer.querySelectorAll('.suggestion-item');
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
                e.preventDefault();
                if (highlightedIndex > -1 && suggestions[highlightedIndex]) {
                    ui.elements.guessInput.value = suggestions[highlightedIndex].textContent;
                    ui.elements.suggestionsContainer.innerHTML = '';
                    ui.elements.suggestionsContainer.style.display = 'none';
                    checkGuess();
                } else {
                    checkGuess();
                }
            }
        });

        function updateHighlight(suggestions) {
            suggestions.forEach((item, index) => {
                if (index === highlightedIndex) {
                    item.classList.add('highlighted');
                    const container = ui.elements.suggestionsContainer;
                    if (item.offsetTop + item.offsetHeight > container.scrollTop + container.clientHeight) {
                        container.scrollTop = item.offsetTop + item.offsetHeight - container.clientHeight;
                    } else if (item.offsetTop < container.scrollTop) {
                        container.scrollTop = item.offsetTop;
                    }
                } else {
                    item.classList.remove('highlighted');
                }
            });
        }

        const formattedDate = new Date(date + 'T00:00:00').toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
        
        ui.elements.shareBtnSuccess.addEventListener('click', async () => {
            const originalText = ui.elements.shareBtnSuccess.textContent;
            await copyShareText(formattedDate, gameState);
            ui.elements.shareBtnSuccess.textContent = 'Copied! ✅';
            ui.elements.shareBtnSuccess.classList.add('copied');
            setTimeout(() => {
                ui.elements.shareBtnSuccess.textContent = originalText;
                ui.elements.shareBtnSuccess.classList.remove('copied');
            }, 2000);
        });

        ui.elements.shareBtnFail.addEventListener('click', async () => {
            const originalText = ui.elements.shareBtnFail.textContent;
            await copyShareText(formattedDate, gameState);
            ui.elements.shareBtnFail.textContent = 'Copied! ✅';
            ui.elements.shareBtnFail.classList.add('copied');
            setTimeout(() => {
                ui.elements.shareBtnFail.textContent = originalText;
                ui.elements.shareBtnFail.classList.remove('copied');
            }, 2000);
        });
    }

    await loadQuizData();
}

if (typeof document !== 'undefined' && !window.__TESTING__) {
    document.addEventListener('DOMContentLoaded', initQuiz);
}
