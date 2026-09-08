import re

with open('frontend/src/views/ListView.vue', 'r') as f:
    content = f.read()

# Update completed style
completed_search = """.grid-card.completed {
  background: transparent;
  border-color: rgba(255,255,255,0.04);
}
.grid-card.completed .card-icon-area {
  background: transparent;
}
.grid-card.completed .item-name {
  text-decoration: line-through; color: var(--ks-text-muted); font-weight: 500;
}"""

completed_replace = """.grid-card.completed {
  background: rgba(34, 197, 94, 0.15); /* Transparent green */
  border-color: rgba(34, 197, 94, 0.3);
}
.grid-card.completed .card-icon-area {
  background: transparent !important;
  color: #4ade80 !important; /* Vivid green for icon */
}
.grid-card.completed .item-name {
  text-decoration: line-through; color: #4ade80; font-weight: 500;
}"""

content = content.replace(completed_search, completed_replace)

# Also ensure transitions are there
transition_search = """      <div class="ks-grid" :class="{'compact-mode': isCompactView}">
        <div
          v-for="item in group.items" """

transition_replace = """      <transition-group name="list" tag="div" class="ks-grid" :class="{'compact-mode': isCompactView}">
        <div
          v-for="item in group.items" """

content = content.replace(transition_search, transition_replace)

close_transition_search = """        </div>
      </div>
    </div>"""

close_transition_replace = """        </div>
      </transition-group>
    </div>"""

content = content.replace(close_transition_search, close_transition_replace)


transition_css = """
.list-move,
.list-enter-active,
.list-leave-active {
  transition: all 0.5s ease;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

.list-leave-active {
  position: absolute;
}
"""

if ".list-move" not in content:
    content = content + transition_css

with open('frontend/src/views/ListView.vue', 'w') as f:
    f.write(content)
