// ABOUTME: Admin UI - search, inspect, and analyze puzzles from admin_data.json.
// ABOUTME: Gated by a client-side passphrase; spoiler content, not for end users.
import { searchPuzzles } from './adminSearch.js';

const ADMIN_PASS_HASH = '1026c2d269101ddb639aee31ad310f42ec0fae00189ed328741b0091256c32ec';
const UNLOCK_KEY = 'nta_admin_unlocked';

let adminPuzzles = [];

async function sha256(text) {
    const data = new TextEncoder().encode(text);
    const digest = await crypto.subtle.digest('SHA-256', data);
    return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, '0')).join('');
}

function isUnlocked() {
    return sessionStorage.getItem(UNLOCK_KEY) === '1';
}

function requireUnlocked() {
    if (isUnlocked()) return;
    document.getElementById('app').hidden = true;
    document.getElementById('gate').hidden = false;
}

function showUnlocked() {
    document.getElementById('gate').hidden = true;
    document.getElementById('app').hidden = false;
}

async function loadAdminData() {
    let adminData;
    try {
        adminData = await (await fetch('admin_data.json?v=' + Date.now())).json();
    } catch (e) {
        document.getElementById('gate-error').textContent = 'Failed to load admin_data.json. Is the generator run?';
        return;
    }
    adminPuzzles = adminData.puzzles;
    renderStats(adminData);
    renderPool(adminData.pool);
    renderAll(adminPuzzles);
}

async function init() {
    document.getElementById('gate').querySelector('form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = document.getElementById('passphrase').value;
        if ((await sha256(input)) === ADMIN_PASS_HASH) {
            sessionStorage.setItem(UNLOCK_KEY, '1');
            showUnlocked();
            await loadAdminData();
        } else {
            document.getElementById('gate-error').textContent = 'Incorrect passphrase.';
        }
    });

    requireUnlocked();
    if (isUnlocked()) {
        showUnlocked();
        await loadAdminData();
    }

    document.getElementById('search-bar').addEventListener('input', (e) => {
        renderSearchResults(adminPuzzles, e.target.value);
    });
}

function renderAll(puzzles) { renderSearchResults(puzzles, ''); }

export function renderSearchResults(puzzles, query) {
    const grid = document.getElementById('results');
    const results = query
        ? searchPuzzles(puzzles, query)
        : [...puzzles].sort((a, b) => b.date.localeCompare(a.date)).map(p => ({ puzzle: p, score: null }));
    if (results.length === 0) { grid.innerHTML = '<p class="empty">No puzzle found for this search.</p>'; return; }
    grid.innerHTML = results.map(({ puzzle, score }) => `
        <div class="card" data-date="${puzzle.date}">
            <div class="card-head"><strong>${escapeHtml(puzzle.name)}</strong> <span class="date">${puzzle.date}</span></div>
            <div class="meta">${escapeHtml(puzzle.teams.join(', ')) || '—'} · ${puzzle.years.length} seasons${score === null ? '' : ` · score ${score}`}</div>
            <details><summary>Details</summary>${puzzleDetailsHtml(puzzle)}</details>
        </div>`).join('');
}

export function puzzleDetailsHtml(puzzle) {
    const nicknames = puzzle.nicknames.length ? `<li>Nicknames: ${escapeHtml(puzzle.nicknames.join(', '))}</li>` : '';
    const hints = (puzzle.hints || []).map(h => `<li>Hint: ${escapeHtml(h)}</li>`).join('');
    const qa = (puzzle.followup_qa || []).map(p => `<li><b>Q:</b> ${escapeHtml(p.question)}<br><b>A:</b> ${escapeHtml(p.answer)}</li>`).join('');
    const stats = Object.entries(puzzle.career_totals || {}).map(([k, v]) => `<span class="stat"><b>${k}</b> ${escapeHtml(v)}</span>`).join(' ');
    const warArc = (puzzle.war_arc || []).map(y => `${escapeHtml(y.year)} ${escapeHtml(y.war)}`).join(' · ');
    const flags = (puzzle.flags || []).map(f => `<span class="flag">${f}</span>`).join(' ');
    return `<ul>
        ${nicknames}
        ${hints}
        ${qa ? '<li><b>Follow-ups:</b></li>' + qa : ''}
        <li><b>Career totals:</b> ${stats || '—'}</li>
        <li><b>WAR arc:</b> ${warArc || '—'}</li>
        <li><a href="${puzzle.date}.html" target="_blank">Answer page</a> · <a href="quiz?date=${puzzle.date}" target="_blank">Quiz</a></li>
        ${flags ? '<li>' + flags + '</li>' : ''}
    </ul>`;
}

export function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

export function renderStats(adminData) {
    const puzzles = adminData.puzzles;
    const byYear = {};
    puzzles.forEach(p => { const y = p.date.slice(0, 4); byYear[y] = (byYear[y] || 0) + 1; });
    const noNick = puzzles.filter(p => p.flags.includes('no_nickname')).length;
    const missingAssets = puzzles.filter(p => p.flags.some(f => f.startsWith('missing_'))).length;
    document.getElementById('stats').innerHTML = `
        <p>Total puzzles: <b>${puzzles.length}</b></p>
        <p>By year: ${Object.entries(byYear).sort().map(([y, c]) => `${y} (${c})`).join(', ')}</p>
        <p>Missing nicknames: <b>${noNick}</b></p>
        <p>Missing assets: <b>${missingAssets}</b></p>
        <p>Duplicates: <b>${adminData.pool.duplicates.length}</b></p>`;
}

export function renderPool(pool) {
    const list = pool.duplicates.map(d => `<li>${escapeHtml(d[0])}: ${d[1].join(', ')}</li>`).join('');
    document.getElementById('pool').innerHTML = `
        <p>Used players: <b>${pool.used.length}</b></p>
        <p>Available: <b>${pool.available_count}</b></p>
        <details><summary>Available players (first 100)</summary><ul>${pool.available.slice(0, 100).map(a => `<li>${escapeHtml(a)}</li>`).join('')}</ul></details>
        <details><summary>Duplicates</summary><ul>${list || '<li>None</li>'}</ul></details>`;
}

if (!window.__TESTING__) {
    document.addEventListener('DOMContentLoaded', init);
}