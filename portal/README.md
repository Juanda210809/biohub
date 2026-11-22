# Portal Web

**Dueña:** Luna · React + Vite + Leaflet (mapas con OpenStreetMap)

- Todas las llamadas a los servicios pasan por Kong: usa `pedir()` de `src/api.js`.
- Cada pantalla vive en `src/paginas/<parte>/`. Por ahora `src/App.jsx` muestra la consulta pública (`src/paginas/consulta/`, HU-05/06): listado de hallazgos y ficha, sin coordenadas.
- La consulta usa el backend real por Kong. Para verla con datos ficticios: `VITE_MODO_DEMO=true npm run dev` (muestra un aviso de que no son registros reales).
- Para desarrollar más rápido fuera de Docker: `npm install` y luego `npm run dev` (abre http://localhost:5173).
