import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';
import { JSDOM } from 'jsdom';

// ABOUTME: Verifies that quiz.html has the correct social sharing meta tags.

describe('quiz.html Meta Tags', () => {
    const html = fs.readFileSync(path.resolve(__dirname, '../../quiz.html'), 'utf8');
    const dom = new JSDOM(html);
    const document = dom.window.document;

    it('should have the correct og:title', () => {
        const tag = document.querySelector('meta[property="og:title"]');
        expect(tag?.getAttribute('content')).toBe('Name That Yankee Quiz');
    });

    it('should have the correct og:description', () => {
        const tag = document.querySelector('meta[property="og:description"]');
        expect(tag?.getAttribute('content')).toBe('Check out this Name That Yankee puzzle! Can you name this player based on their career stats?');
    });

    it('should have the correct og:image', () => {
        const tag = document.querySelector('meta[property="og:image"]');
        expect(tag?.getAttribute('content')).toBe('https://namethatyankeequiz.com/images/social-card.webp');
    });

    it('should have the correct twitter:card', () => {
        const tag = document.querySelector('meta[name="twitter:card"]');
        expect(tag?.getAttribute('content')).toBe('summary_large_image');
    });

    it('should have the correct twitter:title', () => {
        const tag = document.querySelector('meta[name="twitter:title"]');
        expect(tag?.getAttribute('content')).toBe('Name That Yankee Quiz');
    });

    it('should have the correct twitter:description', () => {
        const tag = document.querySelector('meta[name="twitter:description"]');
        expect(tag?.getAttribute('content')).toBe('Check out this Name That Yankee puzzle! Can you name this player based on their career stats?');
    });

    it('should have the correct twitter:image', () => {
        const tag = document.querySelector('meta[name="twitter:image"]');
        expect(tag?.getAttribute('content')).toBe('https://namethatyankeequiz.com/images/social-card.webp');
    });
});
