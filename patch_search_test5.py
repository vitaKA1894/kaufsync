import re

with open('frontend/src/utils/search.test.js', 'r') as f:
    content = f.read()

# Since searchTaxonomy explicitly supports 1-character length now `if (query.length < 1)` instead of 3, the assertions for 1-character and 2-character queries returning 0 results are incorrect. I should remove them.
content = content.replace('assertEqual(searchTaxonomy("a").length, 0, "1-character query should return 0 results");', '')
content = content.replace('assertEqual(searchTaxonomy("ab").length, 0, "2-character query should return 0 results");', '')

# Also fixing upperCaseResults since it uses the same buggy logic of checking only index 0 for "milch".
upper_test_search = """    // Case insensitivity
    const upperCaseResults = searchTaxonomy("MILCH");
    if (upperCaseResults.length === 0 || !upperCaseResults[0].name.toLowerCase().includes("milch")) {
         throw new Error("Search failed for uppercase 'MILCH'");
    }"""
upper_test_replace = """    // Case insensitivity
    const upperCaseResults = searchTaxonomy("MILCH");
    if (upperCaseResults.length === 0 || !upperCaseResults.some(r => r.name.toLowerCase().includes("milch"))) {
         throw new Error("Search failed for uppercase 'MILCH'");
    }"""
content = content.replace(upper_test_search, upper_test_replace)

with open('frontend/src/utils/search.test.js', 'w') as f:
    f.write(content)
