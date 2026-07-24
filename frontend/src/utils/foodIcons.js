export const foodIcons = {
  apfel: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M14.6 4.35c.74-.93 1.25-2.25 1.12-3.61c-1.18.05-2.6.79-3.38 1.73c-.69.83-1.31 2.18-1.14 3.5c1.33.1 2.65-.67 3.4-1.62M18.7 19.3c-1.39 2.06-2.85 4.14-5.18 4.2c-2.28.05-3.03-1.33-5.63-1.33c-2.6 0-3.44 1.33-5.6 1.41C-.13 23.63-1.74 21.32 1.07 17.15c2.3-3.4 5.56-5.55 8.92-5.46c2.23.06 4.3 1.58 5.67 1.58c1.37 0 3.86-1.85 6.55-1.57c1.1.12 4.19.45 6.18 3.39c-5.16 3.16-3.8 10.3 2.14 12.51c-.88 2.15-2.3 4.67-4.22 7.37"/></svg>',
  banane: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M19.45 2.55C18 3.87 17.1 5 15.65 6.27c-3.19 2.76-7.82 4-11.83 2.75C2.63 8.65.65 7 0 5c3.27 1.83 7 2.16 10.63.79C12.92 5 13.9 3.93 14.73 2.85c.67-.88 1.25-1.78 1.95-2.61C17.5.55 18.5 1.55 19.45 2.55M23 15c-1 3.5-3.8 6.3-7 7.5c-3.7 1.4-7.8.6-11.1-1.3c-.6-.4-1.2-.8-1.7-1.3c.7.4 1.4.8 2.2 1.1c3.5 1.4 7.5.8 10.7-1C19.7 17.9 22.3 14.8 23 11c0 1.4.2 2.7 0 4M21 7.2c.4 1 .7 2.2.8 3.3c.1 1.7-.1 3.4-.6 5c-1.3 4.1-4.7 7.2-8.7 8.5c-3.1 1-6.6.7-9.5-.7c3.4 1.1 7 .9 10.2-1C16.8 20.4 20 17 21 12.5c.3-1.8.3-3.6-.2-5.3"/></svg>',
  brot: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.5 2 2 6.5 2 12c0 2.2.7 4.2 1.9 5.8l14.3-14.3C16.2 2.7 14.2 2 12 2M2.5 15.1c1.2 2 3.1 3.6 5.4 4.4L18.4 9c-.8-2.3-2.4-4.2-4.4-5.4L2.5 15.1M10 21.8c.6.1 1.3.2 2 .2c5.5 0 10-4.5 10-10c0-.7-.1-1.4-.2-2l-11.8 11.8Z"/></svg>',
  nutella: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M12 2a4 4 0 0 1 4 4v1h2.5A2.5 2.5 0 0 1 21 9.5v10a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 19.5v-10A2.5 2.5 0 0 1 5.5 7H8V6a4 4 0 0 1 4-4m0 2a2 2 0 0 0-2 2v1h4V6a2 2 0 0 0-2-2m-4.5 5A1.5 1.5 0 0 0 6 10.5v1A1.5 1.5 0 0 0 7.5 13H10v-4H7.5M14 9v4h2.5A1.5 1.5 0 0 0 18 11.5v-1A1.5 1.5 0 0 0 16.5 9H14m-1 0h-2v10h2V9Z"/></svg>',
  milch: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M9 2h6v2h-1v2.92l2.36 2.36C17.7 10.61 18 11.27 18 12v9a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2v-9c0-.73.3-1.39.64-1.72L9 6.92V4H8V2m1 5v3h4V7h-4Z"/></svg>',
  shampoo: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M12 2a4 4 0 0 1 4 4v2h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V10a2 2 0 0 1 2-2h2V6a4 4 0 0 1 4-4m0 2a2 2 0 0 0-2 2v2h4V6a2 2 0 0 0-2-2m-4 8v2h8v-2H8Z"/></svg>'
};

export function getIcon(itemName) {
  if (!itemName) return null;
  const lowerName = itemName.toLowerCase();

  for (const [key, iconSvg] of Object.entries(foodIcons)) {
    if (lowerName.includes(key)) {
      return iconSvg;
    }
  }

  return null;
}
