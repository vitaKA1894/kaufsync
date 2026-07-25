<script setup>
import { computed } from 'vue';
import {
  Apple, Banana, Croissant, Beer, Wine, Trash2, Sparkles, Bath, ShoppingBag,
  Wheat, Milk, Coffee, Beef, Fish, Droplets, Egg, Carrot, Grape, Pizza, Store,
  Drumstick, Leaf, Candy, IceCream, Utensils
} from '@lucide/vue';

const props = defineProps({
  name: {
    type: String,
    default: ''
  },
  category: {
    type: String,
    default: ''
  },
  size: {
    type: [Number, String],
    default: 24
  },
  strokeWidth: {
    type: [Number, String],
    default: 2
  },
  color: {
    type: String,
    default: 'currentColor'
  }
});

const itemIconMap = {
  'apfel': Apple,
  'banane': Banana,
  'brot': Wheat,
  'brötchen': Wheat,
  'croissant': Croissant,
  'milch': Milk,
  'kaffee': Coffee,
  'fleisch': Beef,
  'wurst': Beef,
  'fisch': Fish,
  'wasser': Droplets,
  'cola': Beer,
  'bier': Beer,
  'wein': Wine,
  'ei': Egg,
  'eier': Egg,
  'möhre': Carrot,
  'karotte': Carrot,
  'traube': Grape,
  'pizza': Pizza,
  'müllbeutel': Trash2,
  'waschmittel': Sparkles,
  'shampoo': Bath,
  'zahncreme': Bath,
  'seife': Bath,
  'klopapier': Bath,
  'hähnchen': Drumstick,
  'salat': Leaf,
  'schokolade': Candy,
  'eis': IceCream
};

const categoryIconMap = {
  'obst & gemüse': Carrot,
  'kühlregal': Milk,
  'backwaren': Wheat,
  'fleisch & fisch': Beef,
  'getränke': Beer,
  'drogerie': Bath,
  'allgemein': ShoppingBag
};

const iconComponent = computed(() => {
  const lowerName = props.name.toLowerCase();

  // Plural-Handling (simple)
  const searchName = lowerName.endsWith('en') ? lowerName.slice(0, -2) : (lowerName.endsWith('n') ? lowerName.slice(0, -1) : lowerName);
  const searchName2 = lowerName.endsWith('s') ? lowerName.slice(0, -1) : lowerName;
  const searchName3 = lowerName.endsWith('er') ? lowerName.slice(0, -2) : lowerName;
  const searchName4 = lowerName.replace('ä', 'a').replace('ö', 'o').replace('ü', 'u');

  const searchNames = [lowerName, searchName, searchName2, searchName3, searchName4];

  // Check item names first (sort by length descending to match more specific words first, e.g. "eier" before "ei", and avoid "ei" matching "bier")
  const sortedItemKeys = Object.keys(itemIconMap).sort((a, b) => b.length - a.length);
  for (const key of sortedItemKeys) {
    for (const name of searchNames) {
      if (name.includes(key)) {
        return itemIconMap[key];
      }
    }
  }

  // Check categories next
  if (props.category) {
    const lowerCategory = props.category.toLowerCase();
    const sortedCategoryKeys = Object.keys(categoryIconMap).sort((a, b) => b.length - a.length);
    for (const key of sortedCategoryKeys) {
      if (lowerCategory.includes(key)) {
        return categoryIconMap[key];
      }
    }
  }

  // Fallback
  return ShoppingBag;
});

</script>

<template>
  <component
    :is="iconComponent"
    :size="size"
    :stroke-width="strokeWidth"
    :color="color"
    class="lucide-icon"
  />
</template>

<style scoped>
.lucide-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>