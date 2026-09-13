import re

filepath = "frontend/src/components/AddItemModal.vue"
with open(filepath, "r") as f:
    content = f.read()

# Make sure we don't accidentally intercept editItem's confirmSelection call
# When enter is pressed, and we don't have selectedItem but the query exactly matches
# an item name or alias, it's caught in taxonomyMatch.
# But if it's completely new, selectedItem is null.
# We just need to check if we are in step 1 (showScanner / tags-step not active? - well we use !selectedItem.value for step 1 logic usually)
# Actually, the logic is correct but bypassWarning is passed when clicking "Trotzdem hinzufügen", which uses proceedToDetails anyway.
# We will just verify it works properly.
