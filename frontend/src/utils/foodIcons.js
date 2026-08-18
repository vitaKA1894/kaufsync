export const foodIcons = {
  apfel: '/icons/apfel.png',
  banane: '/icons/banane.png',
  brot: '/icons/brot.png',
  nutella: '/icons/nutella.png',
  milch: '/icons/milch.png',
  shampoo: '/icons/shampoo.png',
  tomate: '/icons/tomate.png',
  kaese: '/icons/kaese.png',
  käse: '/icons/käse.png',
  wurst: '/icons/wurst.png',
  fleisch: '/icons/fleisch.png',
  wasser: '/icons/wasser.png',
  cola: '/icons/cola.png',
  bier: '/icons/bier.png',
  kaffee: '/icons/kaffee.png',
  wein: '/icons/wein.png',
  nudel: '/icons/nudel.png',
  reis: '/icons/reis.png',
  ei: '/icons/ei.png',
  butter: '/icons/butter.png',
  joghurt: '/icons/joghurt.png',
  zwiebel: '/icons/zwiebel.png',
  kartoffel: '/icons/kartoffel.png',
  karotte: '/icons/karotte.png',
  salat: '/icons/salat.png',
  zitrone: '/icons/zitrone.png',
  paprika: '/icons/paprika.png',
  zahncreme: '/icons/zahncreme.png',
  klopapier: '/icons/klopapier.png',
  müllbeutel: '/icons/müllbeutel.png',
  waschmittel: '/icons/waschmittel.png',
  honig: '/icons/honig.png',
  marmelade: '/icons/marmelade.png',
  pizza: '/icons/pizza.png'
};

export function getIcon(itemName) {
  if (!itemName) return null;
  const lowerName = itemName.toLowerCase();

  // Plural-Handling für deutsche Begriffe
  const searchName = lowerName.endsWith('en') ? lowerName.slice(0, -2) : (lowerName.endsWith('n') ? lowerName.slice(0, -1) : lowerName);
  const searchName2 = lowerName.endsWith('s') ? lowerName.slice(0, -1) : lowerName;
  const searchName3 = lowerName.endsWith('er') ? lowerName.slice(0, -2) : lowerName;
  const searchName4 = lowerName.replace('ä', 'a').replace('ö', 'o').replace('ü', 'u'); // Apfel <-> Äpfel

  const searchNames = [lowerName, searchName, searchName2, searchName3, searchName4];

  for (const [key, iconSvg] of Object.entries(foodIcons)) {
    for (const name of searchNames) {
      if (name.includes(key)) {
        return iconSvg;
      }
    }
  }

  return null;
}
