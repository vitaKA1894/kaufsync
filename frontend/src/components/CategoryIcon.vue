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
    default: 45
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
  'obst & gemüse': 'Obst.svg',
  'brot & backwaren': 'Brot.svg',
  'fleisch & fisch': 'fleisch_allgemein.svg',
  'milchprodukte & tiefkühlkost': 'Milch.svg',
  'vorratskammer': 'Nudeln.svg',
  'getränke & genussmittel': 'Getraenke_allgemein.svg',
  'drogerie, haushalt & tierbedarf': 'Putzmittel.svg',
  'sonstiges': 'Allgemein.svg'
};

const errorLevel = ref(0);
const showSvg = ref(false);

const resetState = () => {
  errorLevel.value = 0;
  showSvg.value = false;
};

watch(() => props.name, resetState);
watch(() => props.category, resetState);


const categoryClass = computed(() => {
  if (!props.category) return '';
  const lowerCat = props.category.toLowerCase();
  if (lowerCat.includes('obst & gemüse')) return 'cat-obst-gemuese';
  if (lowerCat.includes('brot & backwaren')) return 'cat-brot-backwaren';
  if (lowerCat.includes('fleisch & fisch')) return 'cat-fleisch-fisch';
  if (lowerCat.includes('milchprodukte & tiefkühlkost')) return 'cat-milch-tiefkuehl';
  if (lowerCat.includes('vorratskammer')) return 'cat-vorratskammer';
  if (lowerCat.includes('getränke & genussmittel')) return 'cat-getraenke-genuss';
  if (lowerCat.includes('drogerie, haushalt & tierbedarf')) return 'cat-drogerie-haushalt';
  return 'cat-sonstiges';
});

const currentImageSrc = computed(() => {
  if (errorLevel.value === 0) {
    return `/icons/${props.name}.svg`;
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
    showSvg.value = true;
    return '';
  }
  if (errorLevel.value === 2) {
    showSvg.value = true;
    return '';
  }
  return '';
});

const onImageError = (event) => {
  if (errorLevel.value === 0) {
    errorLevel.value = 1;
  } else if (errorLevel.value === 1) {
    errorLevel.value = 2;
    showSvg.value = true;
  } else {
    showSvg.value = true;
  }
};

</script>

<template>
  <div class="icon-wrapper flex items-center justify-center shrink-0">
    <div
      v-if="showSvg && name"
      class="fallback-initial-icon"
      :class="categoryClass"
      :style="{
        backgroundColor: color === 'currentColor' ? 'var(--ks-surface-4)' : color,
        color: 'white',
        width: !isNaN(size) ? `${size}px` : size,
        height: !isNaN(size) ? `${size}px` : size,
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: !isNaN(size) ? `${size * 0.55}px` : '1em',
        fontWeight: 'bold',
        opacity: 0.8
      }"
      :title="name"
    >
      {{ name.charAt(0).toUpperCase() }}
    </div>
    <component
      v-else-if="!name"
      :is="iconComponent"
      :size="size"
      :stroke-width="strokeWidth"
      :color="color"
      class="lucide-icon"
      :class="categoryClass"
    />
    <div
      v-else
      class="item-icon-svg"
      :class="categoryClass"
      :style="{
        '--icon-src': `url(${currentImageSrc})`,
        'background-color': color && color !== 'currentColor' ? color : 'var(--ks-text)',
        width: !isNaN(size) ? `${size}px` : size,
        height: !isNaN(size) ? `${size}px` : size
      }"
      :title="name"
    >
      <img
        :src="currentImageSrc"
        @error="onImageError"
        style="display: none;"
        :alt="name"
      />
    </div>
  </div>
</template>

<style scoped>
.lucide-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.item-icon-svg {
  display: inline-block;
  mask-image: var(--icon-src);
  -webkit-mask-image: var(--icon-src);
  mask-size: contain;
  -webkit-mask-size: contain;
  mask-repeat: no-repeat;
  -webkit-mask-repeat: no-repeat;
  mask-position: center;
  -webkit-mask-position: center;
}

/* Fallback Classes in case color prop isn't passed down - they align with ListView colors */
.cat-obst-gemuese { color: #1B5E20; }
.cat-brot-backwaren { color: #F57F17; }
.cat-fleisch-fisch { color: #B71C1C; }
.cat-milch-tiefkuehl { color: #01579B; }
.cat-vorratskammer { color: #E65100; }
.cat-getraenke-genuss { color: #1A237E; }
.cat-drogerie-haushalt { color: #006064; }
.cat-sonstiges { color: #4A148C; }
</style>
