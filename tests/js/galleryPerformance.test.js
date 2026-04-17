import { describe, it, expect, beforeEach } from 'vitest';
import { readFileSync } from 'fs';
import { resolve } from 'path';

describe('Gallery Performance Optimization', () => {
    let html;

    beforeEach(() => {
        html = readFileSync(resolve(__dirname, '../../index.html'), 'utf8');
    });

    it('should have loading="lazy" on all gallery images', () => {
        const imgTags = html.match(/<img[^>]*alt="Name that Yankee trivia card[^>]*>/g);
        
        expect(imgTags).not.toBeNull();
        imgTags.forEach(tag => {
            expect(tag).toContain('loading="lazy"');
        });
    });

    it('should have decoding="async" on all gallery images', () => {
        const imgTags = html.match(/<img[^>]*alt="Name that Yankee trivia card[^>]*>/g);
        
        expect(imgTags).not.toBeNull();
        imgTags.forEach(tag => {
            expect(tag).toContain('decoding="async"');
        });
    });
});
