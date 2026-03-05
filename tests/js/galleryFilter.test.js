import { describe, it, expect } from 'vitest';
import { shouldShowGalleryItem } from '../../js/galleryFilter.js';

describe('galleryFilter', () => {
    describe('shouldShowGalleryItem', () => {
        const currentYear = 2025;

        it('should show all when no filters applied', () => {
            expect(shouldShowGalleryItem('NYY, 2015', false, '', null, false, currentYear)).toBe(true);
        });

        it('should filter by completion status', () => {
            const searchTerms = 'NYY, 2015';
            expect(shouldShowGalleryItem(searchTerms, true, '', null, true, currentYear)).toBe(false);
            expect(shouldShowGalleryItem(searchTerms, false, '', null, true, currentYear)).toBe(true);
        });

        it('should filter by search query (single word)', () => {
            const searchTerms = 'Jeter NYY 1995 2014';
            expect(shouldShowGalleryItem(searchTerms, false, 'jeter', null, false, currentYear)).toBe(true);
            expect(shouldShowGalleryItem(searchTerms, false, 'aaron', null, false, currentYear)).toBe(false);
        });

        it('should require all tokens in search query (AND logic)', () => {
            const searchTerms = 'Jeter NYY 1995 2014';
            expect(shouldShowGalleryItem(searchTerms, false, 'jeter nyy', null, false, currentYear)).toBe(true);
            expect(shouldShowGalleryItem(searchTerms, false, 'jeter judge', null, false, currentYear)).toBe(false);
        });

        it('should filter by decade param', () => {
            const searchTerms = '2022-05-15 Jeter NYY 1995 2014'; // Note puzzle date is first year
            expect(shouldShowGalleryItem(searchTerms, false, '', '1990', false, currentYear)).toBe(true); // Matches 1995
            expect(shouldShowGalleryItem(searchTerms, false, '', '2010', false, currentYear)).toBe(true); // Matches 2014
            expect(shouldShowGalleryItem(searchTerms, false, '', '1980', false, currentYear)).toBe(false); // No match
        });

        it('should handle zero padded strings correctly', () => {
            const searchTerms = 'NYY 05 06';
            // 05 should augment to 5
            expect(shouldShowGalleryItem(searchTerms, false, '5', null, false, currentYear)).toBe(true);
            expect(shouldShowGalleryItem(searchTerms, false, '05', null, false, currentYear)).toBe(true);
        });
    });
});
