import { describe, it, expect } from 'vitest';
import { shouldShowGalleryItem } from '../../js/galleryFilter.js';

describe('Decade filtering reproduction', () => {
    const currentYear = 2026;
    const showUnsolvedOnly = false;
    const searchQuery = '';
    
    it('should correctly filter players from the 1980s', () => {
        // This is a player who played in the 80s (e.g., Don Mattingly)
        // search terms from index.html would have those years
        const searchTerms = "september 25 2025 nyy kcr chw 1985 1981 1988 1986 1990 1989 1979 1982 1983 1984 1987 1980 new york yankees kansas city royals chicago white sox";
        const isCompleted = false;
        const decadeParam = '1980';
        
        const match = shouldShowGalleryItem(searchTerms, isCompleted, searchQuery, decadeParam, showUnsolvedOnly, currentYear);
        expect(match).toBe(true);
    });

    it('should NOT show players who DID NOT play in the 1980s when 1980s filter is active', () => {
        // This is a modern player who only played in 2010s/2020s
        const searchTerms = "march 19 2026 stl nyy ari 2016 2017 2021 2013 2015 2018 2024 2025 2014 2022 2023 2020 2011 2019 2012 st louis cardinals new york yankees arizona diamondbacks";
        const isCompleted = false;
        const decadeParam = '1980';
        
        const match = shouldShowGalleryItem(searchTerms, isCompleted, searchQuery, decadeParam, showUnsolvedOnly, currentYear);
        expect(match).toBe(false);
    });

    it('should correctly filter players from the 1950s', () => {
        const searchTerms = "september 27 2025 nyy stl hou pha kca phi pit chc 1956 1963 1955 1954 1957 1964 1959 1953 1952 1950 1961 1958 1962 1960 1951 1949 new york yankees st louis cardinals houston astros philadelphia phillies pittsburgh pirates chicago cubs";
        const isCompleted = false;
        const decadeParam = '1940'; // Should match 1949
        
        const match = shouldShowGalleryItem(searchTerms, isCompleted, searchQuery, decadeParam, showUnsolvedOnly, currentYear);
        expect(match).toBe(true);
    });

    it('should handle decadeParam as a number (just in case)', () => {
        const searchTerms = "july 09 2025 nyy sea 1986 1982 1985 1978 1983 1980 1981 1984 1979 new york yankees seattle mariners";
        const isCompleted = false;
        const decadeParam = 1980; // Passing as number
        
        const match = shouldShowGalleryItem(searchTerms, isCompleted, searchQuery, decadeParam, showUnsolvedOnly, currentYear);
        expect(match).toBe(true);
    });

    it('should correctly filter 2020s even if currentYear is earlier than player years', () => {
        // Player played in 2025, but today is 2024.
        const searchTerms = "january 01 2026 nyy 2025 2026";
        const testCurrentYear = 2024;
        const decadeParam = '2020';
        
        const match = shouldShowGalleryItem(searchTerms, false, '', decadeParam, false, testCurrentYear);
        expect(match).toBe(true);
    });
});
