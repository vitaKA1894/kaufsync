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

export function searchTaxonomy(query) {
  if (!query || query.length < 1) return [];

  const lowerQuery = query.toLowerCase();

  // Scoring function (Strict matching only):
  // - Exact match in primary name or aliases: 0
  // - Prefix match (e.g. "Mil" in "Milch"): 1
  // - Contains substring match: 3

  const results = taxonomy.map(item => {
    let nameScore = Infinity;
    const lowerName = item.name.toLowerCase();

    // Check primary name
    if (lowerName === lowerQuery) {
        nameScore = Math.min(nameScore, 0);
    } else if (lowerName.startsWith(lowerQuery)) {
        nameScore = Math.min(nameScore, 1);
    } else if (lowerName.includes(lowerQuery)) {
        nameScore = Math.min(nameScore, 3);
    }

    let bestAliasScore = Infinity;
    let bestAlias = null;

    // Check aliases
    for (const alias of item.aliases) {
        const lowerAlias = alias.toLowerCase();
        let aliasScore = Infinity;

        if (lowerAlias === lowerQuery) {
            aliasScore = 0;
        } else if (lowerAlias.startsWith(lowerQuery)) {
            aliasScore = 1;
        } else if (lowerAlias.includes(lowerQuery)) {
            aliasScore = 3;
        }

        if (aliasScore < bestAliasScore) {
            bestAliasScore = aliasScore;
            bestAlias = alias;
        }
    }

    let finalScore = Math.min(nameScore, bestAliasScore);
    let matchedAlias = (bestAliasScore < nameScore && bestAlias) ? bestAlias : null;

    return { item: { ...item, matchedAlias }, score: finalScore };
  })
  .filter(result => result.score !== Infinity)
  .sort((a, b) => {
    if (a.score !== b.score) return a.score - b.score;
    // Tie-breaker: Shorter names first
    return a.item.name.length - b.item.name.length;
  })
  .map(result => result.item)
  .slice(0, 4);

  return results;
}
