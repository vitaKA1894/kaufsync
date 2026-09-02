import re

with open('frontend/src/components/AddItemModal.vue', 'r') as f:
    content = f.read()

# Update tags step
# Find the tags-step div
start_idx = content.find('<div v-else class="tags-step">')

# Modify header inside tags-step
header_search = """           <div class="modal-header" style="justify-content: flex-start; gap: 12px; margin-top: 0; padding-bottom: 16px;">
              <button class="ks-icon-btn" @click="selectedItem = null">
                 <svg viewBox="0 0 24 24"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
              </button>
              <h3 style="margin:0; font-size: 18px;">Details zu {{ selectedItem.name }}</h3>
           </div>"""

header_replace = """           <div class="ks-sheet__handle" style="margin: 8px auto 16px auto; width: 40px; height: 4px; background: var(--ks-border); border-radius: 2px;"></div>
           <div class="modal-header" style="justify-content: space-between; align-items: center; margin-top: 0; padding-bottom: 16px;">
              <div style="display: flex; align-items: center; gap: 12px;">
                 <!-- Empty placeholder for alignment if we don't need back button, or back button if needed, wait, the design doesn't show a back button, but has 'Eis' prominently on the left. Ah, actually in the new design we don't have a back button. But let's keep selectedItem = null functionality. I'll make the title itself clickable or just remove it if not needed? Actually, the request says 'Eis' as h2 and 'Fertig' on the right. -->
                 <h2 style="margin:0; font-size: 24px; font-weight: bold;">{{ selectedItem.name }}</h2>
              </div>
              <button class="ks-btn-text" @click="confirmSelection(false)" style="font-size: 16px; font-weight: 600; padding: 0;">Fertig</button>
           </div>"""

content = content.replace(header_search, header_replace)

# Modify the Tags Content
tags_content_search = """               <div class="manual-amount-input mb-3" style="display: flex; gap: 8px; align-items: center;">
                   <input
                       type="text"
                       v-model="manualQuantity"
                       placeholder="Menge, Beschreibung..."
                       class="modal-input"
                       style="background: var(--ks-surface-3); font-size: 16px; padding: 10px 14px; flex: 1; min-width: 0;"
                       @keyup.enter="confirmSelection(false)"
                   />
               </div>"""

tags_content_replace = """               <div class="manual-amount-input mb-3" style="display: flex; gap: 8px; align-items: center;">
                   <input
                       type="text"
                       v-model="manualQuantity"
                       placeholder="Menge, Beschreibung..."
                       class="modal-input"
                       style="background: var(--ks-surface-3); font-size: 16px; padding: 14px 16px; flex: 1; min-width: 0; border-radius: 8px;"
                       @keyup.enter="confirmSelection(false)"
                   />
               </div>

               <p class="history-label" style="margin-top: 16px; font-size: 16px;">Details zu {{ selectedItem.name }}</p>"""

content = content.replace(tags_content_search, tags_content_replace)

# Remove separators and add icons
separator_search = """                   <!-- Separator for Constellations & Meta Tags -->
                   <div v-if="selectedItem.tags.constellations?.length || selectedItem.tags.global_meta?.filter(t => !['Dringend', 'Angebot', 'Wenn\\'s passt'].includes(t)).length" style="flex-basis: 100%; height: 0;"></div>
                   <hr v-if="selectedItem.tags.constellations?.length || selectedItem.tags.global_meta?.filter(t => !['Dringend', 'Angebot', 'Wenn\\'s passt'].includes(t)).length" class="border-t border-gray-200 dark:border-gray-700 opacity-60 w-full my-2" style="border-top: 1px solid var(--ks-border); opacity: 0.6; width: 100%; margin: 8px 0;" />"""

content = content.replace(separator_search, "")

separator2_search = """                   <!-- Separator for Dringlichkeit -->
                   <div style="flex-basis: 100%; height: 0;"></div>
                   <hr class="border-t border-gray-200 dark:border-gray-700 opacity-60 w-full my-2" style="border-top: 1px solid var(--ks-border); opacity: 0.6; width: 100%; margin: 8px 0;" />"""

content = content.replace(separator2_search, """                   <!-- Separator for Dringlichkeit -->
                   <div style="flex-basis: 100%; height: 0;"></div>""")


urgency_search = """                   <button
                       v-for="tag in ['Dringend', 'Angebot', 'Wenn\\'s passt']" :key="'u-'+tag"
                       class="ks-chip tag-chip tag-meta urgency-tag"
                       :class="{ active: activeTags.includes(tag) }"
                       @click="toggleTag(tag)"
                   >
                       {{ tag }}
                   </button>"""

urgency_replace = """                   <button
                       v-for="tag in ['Dringend', 'Angebot', 'Wenn\\'s passt']" :key="'u-'+tag"
                       class="ks-chip tag-chip tag-meta urgency-tag"
                       :class="{ active: activeTags.includes(tag) }"
                       @click="toggleTag(tag)"
                       style="display: flex; align-items: center; gap: 6px;"
                   >
                       <svg v-if="tag === 'Dringend'" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M13.5 5.5c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zM9.8 8.9L7 23h2.1l1.8-8 2.1 2v6h2v-7.5l-2.1-2 .6-3C14.8 12 16.8 13 19 13v-2c-1.9 0-3.5-1-4.3-2.4l-1-1.6c-.4-.6-1-1-1.7-1-.3 0-.5.1-.8.1L6 8.3V13h2V9.6l1.8-.7"/></svg>
                       <svg v-if="tag === 'Angebot'" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M21.41 11.58l-9-9C12.05 2.22 11.55 2 11 2H4c-1.1 0-2 .9-2 2v7c0 .55.22 1.05.59 1.42l9 9c.36.36.86.58 1.41.58.55 0 1.05-.22 1.41-.59l7-7c.37-.36.59-.86.59-1.41 0-.55-.23-1.06-.59-1.42zM5.5 7C4.67 7 4 6.33 4 5.5S4.67 4 5.5 4 7 4.67 7 5.5 6.33 7 5.5 7z"/></svg>
                       <svg v-if="tag === 'Wenn\\'s passt'" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 9h-2V7h-2v5H6v2h2v5h2v-5h2v-2zm4 5h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
                       {{ tag }}
                   </button>"""

content = content.replace(urgency_search, urgency_replace)


# Remove the settings button/footer since it's not requested in this particular design but we might need to keep it? The design in the image doesn't show "Einstellungen" or the footer button. Actually, wait. It shows the tags up to "Wenn's passt". I should keep "Einstellungen" if it exists below, but I'll remove the footer.

footer_search = """           <div class="modal-footer">
               <button class="ks-btn-filled full-width" @click="confirmSelection(false)">
                   {{ editItem ? 'Speichern' : 'Zur Liste hinzufügen' }}
               </button>
           </div>"""

content = content.replace(footer_search, "")

with open('frontend/src/components/AddItemModal.vue', 'w') as f:
    f.write(content)
