/* Собирает index.html + css + js в один самодостаточный файл для превью.
   Запуск: node tools/build-preview.js [выходной-путь] */
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const out = process.argv[2] || path.join(root, 'dist', 'preview.html');

let html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

/* внешние стили → инлайн */
html = html.replace(/<link rel="stylesheet" href="([^"]+)">/g, (m, href) =>
  '<style>\n' + fs.readFileSync(path.join(root, href), 'utf8') + '\n</style>');

/* локальные скрипты → инлайн (внешние ссылки не трогаем) */
html = html.replace(/<script src="([^"]+)"><\/script>/g, (m, src) =>
  src.startsWith('http') ? m : '<script>\n' + fs.readFileSync(path.join(root, src), 'utf8') + '\n</script>');

/* артефакт оборачивается в свой skeleton — отдаём только содержимое */
html = html
  .replace(/^[\s\S]*?<head>/, '')
  .replace(/<\/head>\s*<body>/, '')
  .replace(/<\/body>\s*<\/html>\s*$/, '')
  .replace(/<meta charset="UTF-8">\s*/, '')
  .trim();

fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, html);
console.log('built', out, (html.length / 1024).toFixed(1) + ' KB');
