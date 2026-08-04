# Stage 1: Build der Vue-Anwendung
# Wir nutzen das Standard-Node-Image statt Alpine, um Kompilierungsfehler zu vermeiden.
# Die Größe spielt hier keine Rolle, da diese Stage später weggeworfen wird.
FROM node:20 AS build

# Wir setzen das Arbeitsverzeichnis
WORKDIR /app

# WICHTIG: Wir greifen explizit auf deinen "frontend" Ordner zu!
COPY frontend/package*.json ./

# Wir nutzen npm ci für saubere CI/CD Builds (setzt eine package-lock.json voraus)
# Falls du keine package-lock.json hast, ändere dies wieder zu: RUN npm install
RUN npm ci

# Jetzt kopieren wir den Rest deines Vue-Codes aus dem frontend-Ordner
COPY frontend/ .

# Vue-App bauen
RUN npm run build

# Stage 2: Ausliefern mit Nginx (Hier bleibt alles schön klein und schlank)
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]