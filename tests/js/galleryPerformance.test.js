import { describe, it, expect, beforeEach } from 'vitest';
import { readFileSync } from 'fs';
import { resolve } from 'path';

describe('Gallery Performance Optimization', () => {
    let html;

    beforeEach(() => {
        html = readFileSync(resolve(__dirname, '../../index.html'), 'utf8');
    });

    it('should have loading="lazy" on items below the fold (index > 5)', () => {
        const imgTags = html.match(/<img[^>]*alt="Name that Yankee trivia card[^>]*>/g);
        
        expect(imgTags).not.toBeNull();
        expect(imgTags.length).toBeGreaterThan(6);

        // First 6 should NOT have loading="lazy"
        for (let i = 0; i < 6; i++) {
            expect(imgTags[i]).not.toContain('loading="lazy"');
        }

        // Everything else SHOULD have loading="lazy"
        for (let i = 6; i < imgTags.length; i++) {
            expect(imgTags[i]).toContain('loading="lazy"');
        }
    });

    it('should have decoding="async" on all gallery images', () => {
        const imgTags = html.match(/<img[^>]*alt="Name that Yankee trivia card[^>]*>/g);
        
        expect(imgTags).not.toBeNull();
        imgTags.forEach(tag => {
            expect(tag).toContain('decoding="async"');
        });
    });
});
