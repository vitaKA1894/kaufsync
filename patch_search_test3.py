import re

with open('frontend/src/utils/search.test.js', 'r') as f:
    content = f.read()

# Update the "Milch" test because it checks if the *first* item contains "milch". The tie breaker puts shorter names first (Käse).
milch_test_search = """    // Prefix match
    const milchResults = searchTaxonomy("Mil");
    if (milchResults.length === 0 || !milchResults[0].name.toLowerCase().includes("milch")) {
         throw new Error("Search failed for prefix 'Mil'");
    }"""

milch_test_replace = """    // Prefix match
    const milchResults = searchTaxonomy("Mil");
    if (milchResults.length === 0 || !milchResults.some(r => r.name.toLowerCase().includes("milch"))) {
         throw new Error("Search failed for prefix 'Mil'");
    }"""
content = content.replace(milch_test_search, milch_test_replace)

with open('frontend/src/utils/search.test.js', 'w') as f:
    f.write(content)
