<script setup>
import { computed } from 'vue';
import {
  Apple, Banana, Croissant, Beer, Wine, Trash2, Sparkles, Bath, ShoppingBag,
  Wheat, Milk, Coffee, Beef, Fish, Droplets, Egg, Carrot, Grape, Pizza,
  Drumstick, Leaf, Candy, IceCream, Utensils, EggFried, Cherry, Cookie, Cake,
  Soup, CupSoda, GlassWater, SprayCan, Toilet, Paperclip
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
  // Obst & Gemüse
  'apfel': Apple,
  'äpfel': Apple,
  'banane': Banana,
  'bananen': Banana,
  'möhre': Carrot,
  'karotte': Carrot,
  'traube': Grape,
  'kirsche': Cherry,
  'salat': Leaf,
  'gemüse': Leaf,
  'obst': Apple,
  'zitrone': Apple, // fallback
  'kartoffel': Leaf,
  'zwiebel': Leaf,
  'tomate': Carrot,
  'paprika': Carrot,

  // Backwaren
  'brot': Wheat,
  'brötchen': Wheat,
  'croissant': Croissant,
  'brezel': Croissant, // fallback
  'kuchen': Cake,
  'torte': Cake,
  'keks': Cookie,

  // Kühlregal
  'milch': Milk,
  'käse': EggFried, // fallback
  'joghurt': Milk,
  'butter': Milk,
  'ei': Egg,
  'eier': Egg,
  'sahne': Milk,

  // Fleisch & Fisch
  'fleisch': Beef,
  'wurst': Beef,
  'salami': Beef,
  'hähnchen': Drumstick,
  'fisch': Fish,
  'lachs': Fish,

  // Getränke
  'wasser': GlassWater,
  'cola': CupSoda,
  'bier': Beer,
  'wein': Wine,
  'kaffee': Coffee,
  'tee': Coffee,
  'saft': GlassWater,

  // Süßigkeiten & Snacks
  'schokolade': Candy,
  'eis': IceCream,
  'chips': Candy,
  'nuss': Cookie,
  'pizza': Pizza,

  // Vorrat & Fertig
  'suppe': Soup,
  'nudel': Wheat,
  'reis': Wheat,

  // Drogerie & Haushalt
  'müllbeutel': Trash2,
  'waschmittel': Sparkles,
  'putzmittel': SprayCan,
  'shampoo': Bath,
  'duschgel': Bath,
  'zahncreme': Bath,
  'zahnpasta': Bath,
  'seife': Bath,
  'klopapier': Toilet,
  'toilettenpapier': Toilet,
  'tampon': Bath,
  'windel': Bath
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

  const searchNames = [lowerName, searchName, searchName2, searchName3];

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
