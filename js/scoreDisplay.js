export function initScoreDisplay() {
    const totalScoreEl = document.getElementById('total-score');
    const scoreDisplay = document.getElementById('score-display');
    const breakdownContainer = document.getElementById('score-breakdown-container');
    const breakdownBody = document.getElementById('breakdown-body');

    if (!totalScoreEl || !scoreDisplay || !breakdownContainer || !breakdownBody) {
        return;
    }

    let totalScore = parseInt(localStorage.getItem('nameThatYankeeTotalScore')) || 0;
    totalScoreEl.textContent = totalScore;

    function populateBreakdown() {
        const breakdown = JSON.parse(localStorage.getItem('nameThatYankeeScoreBreakdown')) || { "0": 0, "1": 0, "2": 0, "3": 0 };
        const pointValues = { "0": 10, "1": 7, "2": 4, "3": 1 };
        const clueLabels = { "0": "1st Clue", "1": "2nd Clue", "2": "3rd Clue", "3": "Last Clue" };

        breakdownBody.innerHTML = '';
        Object.keys(clueLabels).forEach(bucket => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${clueLabels[bucket]}</td>
                <td>${pointValues[bucket]}</td>
                <td>${breakdown[bucket] || 0}</td>
            `;
            breakdownBody.appendChild(row);
        });
    }

    scoreDisplay.addEventListener('click', (e) => {
        if (e.target.closest('table')) return;

        const isHidden = breakdownContainer.style.display === 'none';
        if (isHidden) {
            populateBreakdown();
            breakdownContainer.style.display = 'block';
        } else {
            breakdownContainer.style.display = 'none';
        }
    });

    document.addEventListener('click', (e) => {
        if (!scoreDisplay.contains(e.target) && breakdownContainer.style.display === 'block') {
            breakdownContainer.style.display = 'none';
        }
    });
}
