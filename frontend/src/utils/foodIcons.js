export const foodIcons = {
  apfel: '/icons/Äpfel.svg',
  banane: '/icons/Bananen.svg',
  brot: '/icons/Brot.svg',
  nutella: '/icons/Nougatcreme.svg',
  milch: '/icons/Milch.svg',
  shampoo: '/icons/Shampoo.svg',
  tomate: '/icons/Tomaten.svg',
  kaese: '/icons/Käse.svg',
  käse: '/icons/Käse.svg',
  wurst: '/icons/Wurst.svg',
  fleisch: '/icons/Fleisch.svg',
  wasser: '/icons/Wasser.svg',
  cola: '/icons/Cola.svg',
  bier: '/icons/Bier.svg',
  kaffee: '/icons/Kaffee.svg',
  wein: '/icons/Rotwein.svg',
  nudel: '/icons/Nudeln.svg',
  reis: '/icons/Reis.svg',
  ei: '/icons/Eier.svg',
  butter: '/icons/Butter.svg',
  joghurt: '/icons/Joghurt.svg',
  zwiebel: '/icons/Zwiebeln.svg',
  kartoffel: '/icons/Kartoffeln.svg',
  karotte: '/icons/Karotten.svg',
  salat: '/icons/Salat.svg',
  zitrone: '/icons/Zitrone.svg',
  paprika: '/icons/Peperoni.svg',
  zahncreme: '/icons/Zahnpasta.svg',
  klopapier: '/icons/Haushaltspapier.svg',
  müllbeutel: '/icons/Abfallsäcke.svg',
  waschmittel: '/icons/Waschmittel.svg',
  honig: '/icons/Honig.svg',
  marmelade: '/icons/Konfitüre.svg',
  pizza: '/icons/Pizza.svg'
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
