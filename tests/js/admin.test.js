import { describe, it, expect } from 'vitest';
import { escapeHtml, puzzleDetailsHtml } from '../../js/admin.js';

describe('escapeHtml', () => {
    it('escapes HTML special characters', () => {
        expect(escapeHtml('<b>&"\'')).toBe('&lt;b&gt;&amp;&quot;&#39;');
    });

    it('handles non-string input', () => {
        expect(escapeHtml(42)).toBe('42');
    });
});

describe('puzzleDetailsHtml', () => {
    const puzzle = {
        date: '2026-09-14',
        name: 'Billy Martin',
        nicknames: ['Billy'],
        hints: ['fiery infielder'],
        followup_qa: [{ question: 'Q?', answer: 'A!' }],
        career_totals: { WAR: '2.9' },
        war_arc: [{ year: '1950', war: 0.0, team: 'NYY' }],
        flags: ['no_nickname'],
    };

    it('renders nicknames, stats, war arc, and flags', () => {
        const html = puzzleDetailsHtml(puzzle);
        expect(html).toContain('Nicknames: Billy');
        expect(html).toContain('WAR</b> 2.9');
        expect(html).toContain('1950 0');
        expect(html).toContain('no_nickname');
        expect(html).toContain('2026-09-14.html');
        expect(html).toContain('class="stat"');
    });

    it('handles sparse records gracefully', () => {
        const bare = { ...puzzle, nicknames: [], hints: [], followup_qa: [], war_arc: [], flags: [], career_totals: {} };
        expect(puzzleDetailsHtml(bare)).not.toContain('Nicknames');
        expect(puzzleDetailsHtml(bare)).toContain('—');
    });

    it('escapes war arc values', () => {
        const hostile = { ...puzzle, war_arc: [{ year: '<img>', war: '<b>0.5</b>', team: 'NYY' }] };
        const html = puzzleDetailsHtml(hostile);
        expect(html).toContain('&lt;img&gt; &lt;b&gt;0.5&lt;/b&gt;');
        expect(html).not.toContain('<img>');
        expect(html).not.toContain('<b>0.5</b>');
    });
});