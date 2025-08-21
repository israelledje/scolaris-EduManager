/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './*/templates/**/*.html',
    './static/js/**/*.js',
  ],
 
  plugins: [],
  // S'assurer que toutes les classes responsives sont générées
  safelist: [
    'lg:translate-x-0',
    'lg:ml-72',
    'mobile-sidebar',
    'sidebar-gradient',
    // Ajouter d'autres classes critiques si nécessaire
  ]
}
