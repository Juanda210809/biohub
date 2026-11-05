# Portal Web

**Dueña:** Luna · React + Vite + Leaflet (mapas con OpenStreetMap)

- Todas las llamadas a los servicios pasan por Kong: usa `pedir()` de `src/api.js`.
- La página actual (`src/App.jsx`) solo comprueba que los 5 servicios responden. Se reemplaza por las pantallas reales.
- Para desarrollar más rápido fuera de Docker: `npm install` y luego `npm run dev` (abre http://localhost:5173).
