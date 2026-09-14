<script setup>
import { computed, ref, watch } from 'vue';
import taxonomy from '../assets/taxonomy.json' with { type: 'json' };

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
    default: 2.5
  },
  color: {
    type: String,
    default: 'currentColor'
  }
});

// Build taxonomy lookup map for faster resolution
const taxonomyLookup = new Map();
taxonomy.forEach(entry => {
  if (entry.name) {
    taxonomyLookup.set(entry.name.toLowerCase(), entry);
  }
  if (entry.aliases && Array.isArray(entry.aliases)) {
    entry.aliases.forEach(alias => {
      taxonomyLookup.set(alias.toLowerCase(), entry);
    });
  }
});

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

const getLetterPath = (name) => {
  if (!name) return '';
  let firstLetter = name.charAt(0).toLowerCase();
  const umlautMap = { 'ä': 'a', 'ö': 'o', 'ü': 'u' };
  if (umlautMap[firstLetter]) {
    firstLetter = umlautMap[firstLetter];
  }
  if (/^[a-z]$/.test(firstLetter)) {
    return `/icons/letters/${firstLetter}.svg`;
  }
  return '';
};

const iconSources = computed(() => {
  if (!props.name) return [];

  const lowerName = props.name.toLowerCase();
  const sources = [];

  // Priority 1: Direct name match
  sources.push(`/icons/${props.name}.svg`);

  // Lookup taxonomy entry by alias or exact name match
  const taxEntry = taxonomyLookup.get(lowerName);
  if (taxEntry) {
    // Priority 2: Taxonomy Main Name
    if (taxEntry.name && taxEntry.name !== props.name) {
      sources.push(`/icons/${taxEntry.name}.svg`);
    }
    // Priority 3: Explicit icon field
    if (taxEntry.icon && taxEntry.icon !== props.name && taxEntry.icon !== taxEntry.name) {
      sources.push(`/icons/${taxEntry.icon}.svg`);
    }
  }

  // Priority 4: Global Letter Fallback
  const letterPath = getLetterPath(props.name);
  if (letterPath) {
    sources.push(letterPath);
  }

  return sources;
});

const currentImageSrc = computed(() => {
  if (errorLevel.value < iconSources.value.length) {
    return iconSources.value[errorLevel.value];
  }
  showSvg.value = true;
  return '';
});

const onImageError = (event) => {
  if (errorLevel.value < iconSources.value.length - 1) {
    errorLevel.value += 1;
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
    <div
      v-else-if="name"
      class="item-icon-svg"
      :class="categoryClass"
      :style="{
        '--icon-src': `url(${currentImageSrc})`,
        'background-color': color && color !== 'currentColor' ? color : 'currentColor',
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
  filter: drop-shadow(0 0 1px currentColor);
}

/* Fallback Classes in case color prop isn't passed down - they align with ListView colors */
.cat-obst-gemuese { color: #86efac; }
.cat-brot-backwaren { color: #fef08a; }
.cat-fleisch-fisch { color: #fca5a5; }
.cat-milch-tiefkuehl { color: #93c5fd; }
.cat-vorratskammer { color: #fdba74; }
.cat-getraenke-genuss { color: #a5b4fc; }
.cat-drogerie-haushalt { color: #5eead4; }
.cat-sonstiges { color: #d8b4fe; }
</style>
