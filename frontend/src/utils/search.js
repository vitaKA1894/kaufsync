// Debounce function
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Levenshtein distance algorithm
export function levenshteinDistance(a, b) {
  if (a.length === 0) return b.length;
  if (b.length === 0) return a.length;

  const matrix = [];

  for (let i = 0; i <= b.length; i++) {
    matrix[i] = [i];
  }

  for (let j = 0; j <= a.length; j++) {
    matrix[0][j] = j;
  }

  for (let i = 1; i <= b.length; i++) {
    for (let j = 1; j <= a.length; j++) {
      if (b.charAt(i - 1) == a.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1, // substitution
          matrix[i][j - 1] + 1,     // insertion
          matrix[i - 1][j] + 1      // deletion
        );
      }
    }
  }

  return matrix[b.length][a.length];
}

import taxonomy from '../assets/taxonomy.json' with { type: 'json' };
import Fuse from 'fuse.js';

const fuseOptions = {
  keys: [
    { name: 'name', weight: 0.7 },
    { name: 'aliases', weight: 0.3 }
  ],
  threshold: 0.3,
  ignoreLocation: true,
  minMatchCharLength: 2,
  includeMatches: true
};

const fuse = new Fuse(taxonomy, fuseOptions);

export function searchTaxonomy(query) {
  if (!query || query.length < 2) return [];

  const results = fuse.search(query);

  return results.slice(0, 4).map(result => {
    let matchedAlias = null;

    // Check if the match was on an alias
    if (result.matches && result.matches.length > 0) {
      // Find a match that is in the 'aliases' key
      const aliasMatch = result.matches.find(m => m.key === 'aliases');
      if (aliasMatch) {
        matchedAlias = aliasMatch.value;
      }
    }

    return { ...result.item, matchedAlias };
  });
}
