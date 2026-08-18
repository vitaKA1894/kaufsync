<script setup>
import { computed, ref, watch } from 'vue';
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
  'brot & backwaren': Wheat,
  'fleisch & fisch': Beef,
  'milchprodukte & tiefkühlkost': Milk,
  'vorratskammer': ShoppingBag,
  'getränke & genussmittel': Beer,
  'drogerie, haushalt & tierbedarf': Bath,
  'sonstiges': Sparkles
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

const categoryImageMap = {
  'obst & gemüse': 'apfel.png',
  'brot & backwaren': 'brot.png',
  'fleisch & fisch': 'fleisch_allgemein.png',
  'milchprodukte & tiefkühlkost': 'milch.png',
  'vorratskammer': 'nudeln.png',
  'getränke & genussmittel': 'getraenke.png',
  'drogerie, haushalt & tierbedarf': 'putzmittel.png',
  'sonstiges': 'sonstiges.png'
};

const errorLevel = ref(0);
const showSvg = ref(false);

const resetState = () => {
  errorLevel.value = 0;
  showSvg.value = false;
};

watch(() => props.name, resetState);
watch(() => props.category, resetState);

const currentImageSrc = computed(() => {
  if (errorLevel.value === 0) {
    return `/icons/${props.name}.png`;
  }
  if (errorLevel.value === 1) {
    if (props.category) {
      const lowerCategory = props.category.toLowerCase();
      // Find the exact match or substring match for category
      const sortedCategoryKeys = Object.keys(categoryImageMap).sort((a, b) => b.length - a.length);
      for (const key of sortedCategoryKeys) {
        if (lowerCategory.includes(key)) {
          return `/icons/${categoryImageMap[key]}`;
        }
      }
    }
    // If no category match, force the next error level by returning a path we know will trigger an error or directly advance
    // Returning `sonstiges.png` here handles it natively.
    return '/icons/sonstiges.png';
  }
  if (errorLevel.value === 2) {
    return '/icons/sonstiges.png';
  }
  return '';
});

const onImageError = (event) => {
  if (errorLevel.value === 0) {
    errorLevel.value = 1;
  } else if (errorLevel.value === 1) {
    errorLevel.value = 2;
  } else {
    showSvg.value = true;
  }
};

</script>

<template>
  <component
    v-if="showSvg || !name"
    :is="iconComponent"
    :size="size"
    :stroke-width="strokeWidth"
    :color="color"
    class="lucide-icon"
  />
  <img
    v-else
    :src="currentImageSrc"
    @error="onImageError"
    class="item-icon-img"
    :style="{ width: typeof size === 'number' ? `${size}px` : size, height: typeof size === 'number' ? `${size}px` : size }"
    :alt="name"
  />
</template>

<style scoped>
.lucide-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.item-icon-img {
  object-fit: contain;
  display: inline-block;
}
</style>
