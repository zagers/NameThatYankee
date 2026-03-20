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

        it('should filter by decade param with format from index.html', () => {
            const searchTerms = "march 19 2026 stl nyy ari 2016 2017 2021 2013 2015 2018 2024 2025 2014 2022 2023 2020 2011 2019 2012 st louis cardinals new york yankees arizona diamondbacks";
            const currentYear = 2026;
            
            // Should match 2010s
            expect(shouldShowGalleryItem(searchTerms, false, '', '2010', false, currentYear)).toBe(true);
            
            // Should match 2020s
            expect(shouldShowGalleryItem(searchTerms, false, '', '2020', false, currentYear)).toBe(true);
            
            // Should NOT match 1980s
            expect(shouldShowGalleryItem(searchTerms, false, '', '1980', false, currentYear)).toBe(false);
        });
    });
});
