import { levenshteinDistance, searchTaxonomy, debounce } from './search.js';

// Setup mock for taxonomy.json since we use it directly in search.js
// We don't actually need to mock it if we are using ES modules in test, but
// we will just run this with basic node testing or vitest.

function runTests() {
    console.log("Running Levenshtein distance tests...");

    const assertEqual = (actual, expected, msg) => {
        if (actual !== expected) {
            throw new Error(`Test failed: ${msg}. Expected ${expected}, got ${actual}`);
        }
    }

    // Exact matches
    assertEqual(levenshteinDistance("test", "test"), 0, "Exact match");
    assertEqual(levenshteinDistance("", ""), 0, "Empty strings");

    // Substitutions
    assertEqual(levenshteinDistance("tomate", "tomta"), 2, "Substitution");
    assertEqual(levenshteinDistance("milch", "milhc"), 2, "Transposition");

    // Additions/Deletions
    assertEqual(levenshteinDistance("apfel", "apfe"), 1, "Deletion");
    assertEqual(levenshteinDistance("brot", "brott"), 1, "Addition");

    console.log("Levenshtein tests passed!");

    console.log("Running search algorithm tests...");

    // Threshold check (must be >= 3 chars)
    assertEqual(searchTaxonomy("ap").length, 0, "Query length < 3 should return 0 results");

    // Prefix match
    const milchResults = searchTaxonomy("Mil");
    if (milchResults.length === 0 || !milchResults[0].name.toLowerCase().includes("milch")) {
         throw new Error("Search failed for prefix 'Mil'");
    }

    // Fuzzy match
    const tomateResults = searchTaxonomy("tomta");
    if (tomateResults.length === 0 || !tomateResults[0].name.toLowerCase().includes("tomat")) {
        throw new Error("Fuzzy search failed for 'tomta'");
    }

    console.log("Search tests passed!");

    // Basic debounce test (synchronous check is hard without proper test runner,
    // but we just verify it returns a function)
    const dbFunc = debounce(() => {}, 250);
    assertEqual(typeof dbFunc, "function", "Debounce should return a function");

    console.log("All tests passed!");
}

runTests();
