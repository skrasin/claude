/* ============================================================
   assets.js — векторная библиотека: материалы, мебель, дома.
   Вся геометрия авторится в сантиметрах (1 SVG-юнит = 1 см),
   поэтому предметы соотносятся друг с другом как в жизни.
   ============================================================ */
window.ASSETS = (function () {
  'use strict';

  /* ---------------------------------------------------------- utils */

  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }

  function hexToRgb(h) {
    h = String(h).replace('#', '');
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }

  function rgbToHex(r, g, b) {
    return '#' + [r, g, b].map(function (v) {
      return clamp(Math.round(v), 0, 255).toString(16).padStart(2, '0');
    }).join('');
  }

  /** Осветлить (amt > 0) или затемнить (amt < 0) цвет. amt: -1..1 */
  function sh(hex, amt) {
    var c = hexToRgb(hex);
    if (amt >= 0) {
      return rgbToHex(c[0] + (255 - c[0]) * amt, c[1] + (255 - c[1]) * amt, c[2] + (255 - c[2]) * amt);
    }
    var k = 1 + amt;
    return rgbToHex(c[0] * k, c[1] * k, c[2] * k);
  }

  /** Воспринимаемая светлота 0..1 — чтобы подбирать контрастную обводку. */
  function lum(hex) {
    var c = hexToRgb(hex);
    return (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) / 255;
  }

  /* ---------------------------------------------------------- иконки */

  var ICONS = {
    back: '<path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
    plus: '<path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    trash: '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
    flip: '<path d="M12 4v16M8 8L4 12l4 4M16 8l4 4-4 4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
    grow: '<path d="M4 10V4h6M20 14v6h-6M4 4l7 7M20 20l-7-7" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
    shrink: '<path d="M10 4v6H4M14 20v-6h6M4 10l6-6M20 14l-6 6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
    front: '<path d="M12 3l8 5-8 5-8-5 8-5z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="M4 13l8 5 8-5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>',
    copy: '<rect x="8" y="8" width="12" height="12" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
    check: '<path d="M5 13l4 4 10-10" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',
    eye: '<path d="M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12z" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="12" r="2.8" fill="none" stroke="currentColor" stroke-width="1.8"/>',
    edit: '<path d="M4 20h4L20 8l-4-4L4 16v4z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>',
    sun: '<circle cx="12" cy="12" r="4.2" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 2v2.4M12 19.6V22M2 12h2.4M19.6 12H22M4.9 4.9l1.7 1.7M17.4 17.4l1.7 1.7M19.1 4.9l-1.7 1.7M6.6 17.4l-1.7 1.7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
    moon: '<path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>',
    home: '<path d="M3.5 11L12 4l8.5 7" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/><path d="M5.5 10v9h13v-9" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"/>',
    arrowRight: '<path d="M5 12h13M13 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
  };

  function icon(name, size) {
    return '<svg class="ic" viewBox="0 0 24 24" width="' + (size || 20) + '" height="' + (size || 20) +
      '" aria-hidden="true">' + (ICONS[name] || '') + '</svg>';
  }

  /* ==========================================================
     МАТЕРИАЛЫ СТЕН (плоскость обращена к зрителю — без перспективы)
     ========================================================== */

  var WALL_MATERIALS = [
    { id: 'chalk',    label: 'Извёстка',    kind: 'paint', color: '#EFEDE7' },
    { id: 'greige',   label: 'Грейж',       kind: 'paint', color: '#D5D0C6' },
    { id: 'sage',     label: 'Шалфей',      kind: 'paint', color: '#9EAE9B' },
    { id: 'clay',     label: 'Глина',       kind: 'paint', color: '#C08A70' },
    { id: 'navy',     label: 'Ночной синий',kind: 'paint', color: '#2E4A66' },
    { id: 'graphite', label: 'Графит',      kind: 'paint', color: '#3B3F44' },
    { id: 'blush',    label: 'Пудра',       kind: 'paint', color: '#DEC3BC' },
    { id: 'olive',    label: 'Олива',       kind: 'paint', color: '#7C845E' },
    { id: 'brick',    label: 'Кирпич',      kind: 'brick', color: '#B2705C' },
    { id: 'panel',    label: 'Рейки',       kind: 'panel', color: '#C09468' },
    { id: 'concrete', label: 'Бетон',       kind: 'concrete', color: '#C6C4BE' }
  ];

  /** Рисует стену: x,y,w,h в юнитах вьюбокса комнаты. */
  function renderWall(mat, x, y, w, h, p) {
    var c = mat.color, out = '';
    out += '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" fill="' + c + '"/>';

    if (mat.kind === 'brick') {
      var bh = 14, bw = 34, row = 0, yy, xx, off;
      out += '<g stroke="' + sh(c, -0.16) + '" stroke-width="1.6" opacity=".85">';
      for (yy = y; yy < y + h; yy += bh, row++) {
        out += '<line x1="' + x + '" y1="' + yy.toFixed(1) + '" x2="' + (x + w) + '" y2="' + yy.toFixed(1) + '"/>';
        off = (row % 2) ? bw / 2 : 0;
        for (xx = x + off; xx < x + w; xx += bw) {
          out += '<line x1="' + xx.toFixed(1) + '" y1="' + yy.toFixed(1) +
            '" x2="' + xx.toFixed(1) + '" y2="' + Math.min(yy + bh, y + h).toFixed(1) + '"/>';
        }
      }
      out += '</g>';
      /* лёгкая неровность кладки */
      out += '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h +
        '" fill="url(#' + p + 'wgrain)" opacity=".35"/>';
    } else if (mat.kind === 'panel') {
      var pw = 13;
      out += '<g>';
      for (var px = x; px < x + w; px += pw) {
        out += '<rect x="' + px.toFixed(1) + '" y="' + y + '" width="' + (pw - 3).toFixed(1) +
          '" height="' + h + '" fill="' + sh(c, 0.07) + '"/>';
        out += '<rect x="' + (px + pw - 3).toFixed(1) + '" y="' + y + '" width="3" height="' + h +
          '" fill="' + sh(c, -0.3) + '"/>';
      }
      out += '</g>';
    } else if (mat.kind === 'concrete') {
      out += '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h +
        '" fill="url(#' + p + 'wgrain)" opacity=".55"/>';
      /* следы опалубки */
      out += '<g fill="' + sh(c, -0.12) + '" opacity=".5">';
      for (var cx = x + 60; cx < x + w; cx += 120) {
        out += '<circle cx="' + cx.toFixed(1) + '" cy="' + (y + h * 0.3).toFixed(1) + '" r="3"/>';
        out += '<circle cx="' + cx.toFixed(1) + '" cy="' + (y + h * 0.72).toFixed(1) + '" r="3"/>';
      }
      out += '</g>';
    }

    /* мягкое затенение по углам — воздух в комнате */
    out += '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h +
      '" fill="url(#' + p + 'wvign)"/>';
    return out;
  }

  /* ==========================================================
     МАТЕРИАЛЫ ПОЛА (рисуются в перспективе, с сходящимися швами)
     ========================================================== */

  var FLOOR_MATERIALS = [
    { id: 'oakLight', label: 'Дуб светлый', kind: 'plank', color: '#D6B183' },
    { id: 'oakMid',   label: 'Дуб',         kind: 'plank', color: '#BE9160' },
    { id: 'walnut',   label: 'Орех',        kind: 'plank', color: '#7E5638' },
    { id: 'ash',      label: 'Ясень белый', kind: 'plank', color: '#E4DCCD' },
    { id: 'herring',  label: 'Ёлочка',      kind: 'herring', color: '#C79A63' },
    { id: 'concreteF',label: 'Бетон',       kind: 'slab',  color: '#BDBBB5' },
    { id: 'marble',   label: 'Мрамор',      kind: 'marble',color: '#E8E7E3' },
    { id: 'checker',  label: 'Шахматы',     kind: 'checker', color: '#DAD7D0' },
    { id: 'carpetGr', label: 'Ковролин',    kind: 'carpet', color: '#9A9A94' },
    { id: 'carpetSa', label: 'Ковролин беж',kind: 'carpet', color: '#C4B49B' }
  ];

  /**
   * geo — геометрия комнаты из app.js:
   *   { W, H, wallY, backHalf, frontHalf, xAt(cm, fy), yAt(fy) }
   */
  function renderFloor(mat, geo, p) {
    var c = mat.color, out = '';
    var W = geo.W, H = geo.H, wallY = geo.wallY;

    /* сама плоскость пола — трапеция */
    var quad = [
      [geo.xAt(-250, 0), wallY],
      [geo.xAt(250, 0), wallY],
      [geo.xAt(250, 1), H],
      [geo.xAt(-250, 1), H]
    ];
    var poly = quad.map(function (q) { return q[0].toFixed(1) + ',' + q[1].toFixed(1); }).join(' ');
    out += '<clipPath id="' + p + 'floorClip"><polygon points="' + poly + '"/></clipPath>';
    out += '<g clip-path="url(#' + p + 'floorClip)">';
    out += '<polygon points="' + poly + '" fill="' + c + '"/>';

    /* поперечные швы: шаг растёт к зрителю — так работает перспектива */
    var rows = [0.07, 0.17, 0.29, 0.43, 0.59, 0.78, 1.0];
    var seamCol = sh(c, mat.kind === 'carpet' ? -0.08 : -0.22);

    function longitudinal(stepCm, width, op) {
      var s = '<g stroke="' + seamCol + '" stroke-width="' + width + '" opacity="' + op + '">';
      for (var xc = -250; xc <= 250; xc += stepCm) {
        s += '<line x1="' + geo.xAt(xc, 0).toFixed(1) + '" y1="' + wallY.toFixed(1) +
          '" x2="' + geo.xAt(xc, 1).toFixed(1) + '" y2="' + H.toFixed(1) + '"/>';
      }
      return s + '</g>';
    }

    function transverse(list, width, op) {
      var s = '<g stroke="' + seamCol + '" stroke-width="' + width + '" opacity="' + op + '">';
      list.forEach(function (fy) {
        var yy = geo.yAt(fy);
        s += '<line x1="' + geo.xAt(-250, fy).toFixed(1) + '" y1="' + yy.toFixed(1) +
          '" x2="' + geo.xAt(250, fy).toFixed(1) + '" y2="' + yy.toFixed(1) + '"/>';
      });
      return s + '</g>';
    }

    if (mat.kind === 'plank') {
      /* доски разной ширины — чтобы не читалось как таблица */
      out += '<g>';
      var xc = -250, i = 0;
      while (xc < 250) {
        var wcm = [18, 22, 20, 25, 19][i % 5];
        var tone = [0.05, -0.04, 0.02, -0.07, 0.0][i % 5];
        out += '<polygon fill="' + sh(c, tone) + '" points="' +
          geo.xAt(xc, 0).toFixed(1) + ',' + wallY.toFixed(1) + ' ' +
          geo.xAt(Math.min(xc + wcm, 250), 0).toFixed(1) + ',' + wallY.toFixed(1) + ' ' +
          geo.xAt(Math.min(xc + wcm, 250), 1).toFixed(1) + ',' + H.toFixed(1) + ' ' +
          geo.xAt(xc, 1).toFixed(1) + ',' + H.toFixed(1) + '"/>';
        xc += wcm; i++;
      }
      out += '</g>';
      out += longitudinal(20, 1.4, 0.5);
      out += transverse(rows, 1.2, 0.35);
    } else if (mat.kind === 'herring') {
      /* ёлочка: короткие планки под 45°, кладём рядами по глубине */
      out += '<g opacity=".9">';
      for (var r = 0; r < rows.length; r++) {
        var f0 = r === 0 ? 0 : rows[r - 1], f1 = rows[r];
        var fm = (f0 + f1) / 2;
        var step = 34;
        for (var hx = -250; hx < 250; hx += step) {
          var dir = ((hx / step) | 0) % 2 === 0 ? 1 : -1;
          var tone2 = dir > 0 ? 0.06 : -0.08;
          out += '<polygon fill="' + sh(c, tone2) + '" stroke="' + sh(c, -0.25) +
            '" stroke-width="1" points="' +
            geo.xAt(hx, f0).toFixed(1) + ',' + geo.yAt(f0).toFixed(1) + ' ' +
            geo.xAt(hx + step, fm).toFixed(1) + ',' + geo.yAt(fm).toFixed(1) + ' ' +
            geo.xAt(hx + step, f1).toFixed(1) + ',' + geo.yAt(f1).toFixed(1) + ' ' +
            geo.xAt(hx, fm).toFixed(1) + ',' + geo.yAt(fm).toFixed(1) + '"/>';
        }
      }
      out += '</g>';
    } else if (mat.kind === 'checker') {
      var cols = 10, dark = '#3C3B39';
      for (var rr = 0; rr < rows.length; rr++) {
        var a = rr === 0 ? 0 : rows[rr - 1], b = rows[rr];
        for (var cc = 0; cc < cols; cc++) {
          if ((rr + cc) % 2) continue;
          var x0 = -250 + cc * (500 / cols), x1 = x0 + 500 / cols;
          out += '<polygon fill="' + dark + '" points="' +
            geo.xAt(x0, a).toFixed(1) + ',' + geo.yAt(a).toFixed(1) + ' ' +
            geo.xAt(x1, a).toFixed(1) + ',' + geo.yAt(a).toFixed(1) + ' ' +
            geo.xAt(x1, b).toFixed(1) + ',' + geo.yAt(b).toFixed(1) + ' ' +
            geo.xAt(x0, b).toFixed(1) + ',' + geo.yAt(b).toFixed(1) + '"/>';
        }
      }
      out += longitudinal(50, 1.6, 0.4);
      out += transverse(rows, 1.6, 0.4);
    } else if (mat.kind === 'slab') {
      out += longitudinal(125, 2, 0.35);
      out += transverse([0.29, 0.59, 1.0], 2, 0.35);
      out += '<rect x="0" y="' + wallY + '" width="' + W + '" height="' + (H - wallY) +
        '" fill="url(#' + p + 'wgrain)" opacity=".5"/>';
    } else if (mat.kind === 'marble') {
      out += longitudinal(125, 1.8, 0.3);
      out += transverse([0.29, 0.59, 1.0], 1.8, 0.3);
      out += '<g stroke="' + sh(c, -0.42) + '" fill="none" opacity=".45" stroke-linecap="round">';
      out += '<path d="M' + geo.xAt(-210, 0) + ',' + geo.yAt(0.02) + ' C' + geo.xAt(-90, 0.3) + ',' +
        geo.yAt(0.25) + ' ' + geo.xAt(-170, 0.6) + ',' + geo.yAt(0.6) + ' ' + geo.xAt(-40, 1) + ',' + geo.yAt(1) +
        '" stroke-width="2.2"/>';
      out += '<path d="M' + geo.xAt(60, 0) + ',' + geo.yAt(0.02) + ' C' + geo.xAt(150, 0.35) + ',' +
        geo.yAt(0.3) + ' ' + geo.xAt(70, 0.7) + ',' + geo.yAt(0.7) + ' ' + geo.xAt(190, 1) + ',' + geo.yAt(1) +
        '" stroke-width="1.6"/>';
      out += '</g>';
    } else if (mat.kind === 'carpet') {
      out += '<rect x="0" y="' + wallY + '" width="' + W + '" height="' + (H - wallY) +
        '" fill="url(#' + p + 'wgrain)" opacity=".7"/>';
      out += longitudinal(8, 0.8, 0.16);
    }

    /* свет от окна и затемнение к дальней стене — придаёт объём */
    out += '<rect x="0" y="' + wallY + '" width="' + W + '" height="' + (H - wallY) +
      '" fill="url(#' + p + 'fshade)"/>';
    out += '</g>';
    return out;
  }

  /* ==========================================================
     МЕБЕЛЬ. Все размеры — сантиметры. Origin — левый верхний угол,
     низ объекта = линия пола.
     ========================================================== */

  var WOOD = '#B98A57', WOOD_D = '#8A6440', METAL = '#4A4E52', DARK = '#2F3336';

  var FURNITURE = {

    /* ---------------------------------------------- мягкая мебель */
    sofa3: {
      label: 'Диван', cat: 'floor', w: 224, h: 86, tint: '#7C8A93',
      draw: function (c) {
        var d = sh(c, -0.2), l = sh(c, 0.13);
        return '' +
          '<rect x="20" y="72" width="11" height="14" rx="3" fill="' + WOOD_D + '"/>' +
          '<rect x="193" y="72" width="11" height="14" rx="3" fill="' + WOOD_D + '"/>' +
          '<rect x="10" y="6" width="204" height="50" rx="11" fill="' + d + '"/>' +
          '<rect x="21" y="11" width="90" height="42" rx="9" fill="' + c + '"/>' +
          '<rect x="113" y="11" width="90" height="42" rx="9" fill="' + c + '"/>' +
          '<rect x="10" y="45" width="204" height="31" rx="10" fill="' + l + '"/>' +
          '<line x1="112" y1="50" x2="112" y2="72" stroke="' + d + '" stroke-width="1.6" opacity=".55"/>' +
          '<rect x="0" y="16" width="27" height="62" rx="12" fill="' + c + '"/>' +
          '<rect x="197" y="16" width="27" height="62" rx="12" fill="' + c + '"/>' +
          '<rect x="3" y="19" width="21" height="9" rx="4.5" fill="' + l + '" opacity=".8"/>' +
          '<rect x="200" y="19" width="21" height="9" rx="4.5" fill="' + l + '" opacity=".8"/>';
      }
    },

    armchair: {
      label: 'Кресло', cat: 'floor', w: 92, h: 84, tint: '#B08968',
      draw: function (c) {
        var d = sh(c, -0.2), l = sh(c, 0.13);
        return '' +
          '<rect x="16" y="70" width="9" height="14" rx="3" fill="' + WOOD_D + '"/>' +
          '<rect x="67" y="70" width="9" height="14" rx="3" fill="' + WOOD_D + '"/>' +
          '<rect x="8" y="4" width="76" height="50" rx="12" fill="' + d + '"/>' +
          '<rect x="18" y="9" width="56" height="42" rx="10" fill="' + c + '"/>' +
          '<rect x="8" y="44" width="76" height="30" rx="10" fill="' + l + '"/>' +
          '<rect x="0" y="16" width="24" height="58" rx="11" fill="' + c + '"/>' +
          '<rect x="68" y="16" width="24" height="58" rx="11" fill="' + c + '"/>';
      }
    },

    pouf: {
      label: 'Пуф', cat: 'floor', w: 60, h: 42, tint: '#C8A24A',
      draw: function (c) {
        var d = sh(c, -0.18), l = sh(c, 0.12);
        return '' +
          '<rect x="10" y="34" width="6" height="8" rx="2" fill="' + WOOD_D + '"/>' +
          '<rect x="44" y="34" width="6" height="8" rx="2" fill="' + WOOD_D + '"/>' +
          '<rect x="2" y="6" width="56" height="30" rx="13" fill="' + c + '"/>' +
          '<ellipse cx="30" cy="12" rx="24" ry="6" fill="' + l + '"/>' +
          '<path d="M2 24 h56" stroke="' + d + '" stroke-width="1.4" opacity=".5"/>';
      }
    },

    beanbag: {
      label: 'Кресло-мешок', cat: 'floor', w: 96, h: 78, tint: '#5F7A8C',
      draw: function (c) {
        var d = sh(c, -0.2), l = sh(c, 0.14);
        return '' +
          '<path d="M6 78 C0 46 14 22 40 14 C64 6 92 20 92 44 C92 64 78 78 60 78 Z" fill="' + c + '"/>' +
          '<path d="M40 14 C60 10 84 22 88 42 C80 30 62 22 40 24 Z" fill="' + l + '"/>' +
          '<path d="M10 66 C30 76 62 78 88 62 C82 74 66 78 52 78 L14 78 Z" fill="' + d + '" opacity=".55"/>' +
          '<path d="M22 30 C34 22 52 22 66 30" stroke="' + d + '" stroke-width="1.6" fill="none" opacity=".5"/>';
      }
    },

    /* ---------------------------------------------- столы и хранение */
    coffeeTable: {
      label: 'Журнальный стол', cat: 'floor', w: 112, h: 42,
      draw: function () {
        return '' +
          '<rect x="12" y="16" width="8" height="26" rx="2.5" fill="' + WOOD_D + '" transform="rotate(5 16 30)"/>' +
          '<rect x="92" y="16" width="8" height="26" rx="2.5" fill="' + WOOD_D + '" transform="rotate(-5 96 30)"/>' +
          '<rect x="18" y="26" width="76" height="5" rx="2" fill="' + sh(WOOD, -0.12) + '"/>' +
          '<rect x="0" y="8" width="112" height="10" rx="4" fill="' + WOOD + '"/>' +
          '<rect x="0" y="16" width="112" height="4" rx="2" fill="' + WOOD_D + '"/>' +
          '<rect x="6" y="9.5" width="100" height="3" rx="1.5" fill="' + sh(WOOD, 0.18) + '" opacity=".7"/>';
      }
    },

    sideTable: {
      label: 'Столик', cat: 'floor', w: 44, h: 55,
      draw: function () {
        return '' +
          '<rect x="19" y="12" width="6" height="43" fill="' + METAL + '"/>' +
          '<ellipse cx="22" cy="53" rx="16" ry="4" fill="' + sh(METAL, -0.1) + '"/>' +
          '<rect x="0" y="6" width="44" height="8" rx="4" fill="' + sh(WOOD, 0.06) + '"/>' +
          '<rect x="0" y="12" width="44" height="3" rx="1.5" fill="' + WOOD_D + '"/>';
      }
    },

    mediaConsole: {
      against: true, label: 'Тумба под ТВ', cat: 'floor', w: 168, h: 50,
      draw: function () {
        var f = sh(WOOD, 0.04), d = sh(WOOD, -0.24);
        return '' +
          '<rect x="0" y="4" width="168" height="38" rx="4" fill="' + f + '"/>' +
          '<rect x="0" y="4" width="168" height="5" rx="2.5" fill="' + sh(WOOD, 0.16) + '"/>' +
          '<rect x="6" y="13" width="76" height="24" rx="2.5" fill="' + d + '" opacity=".55"/>' +
          '<rect x="86" y="13" width="76" height="24" rx="2.5" fill="' + d + '" opacity=".55"/>' +
          '<rect x="30" y="23" width="28" height="3" rx="1.5" fill="' + sh(WOOD, 0.3) + '"/>' +
          '<rect x="110" y="23" width="28" height="3" rx="1.5" fill="' + sh(WOOD, 0.3) + '"/>' +
          '<rect x="10" y="42" width="7" height="8" fill="' + METAL + '"/>' +
          '<rect x="151" y="42" width="7" height="8" fill="' + METAL + '"/>';
      }
    },

    bookshelf: {
      against: true, label: 'Стеллаж', cat: 'floor', w: 94, h: 196,
      draw: function () {
        var f = sh(WOOD, 0.02), d = sh(WOOD, -0.3), out = '';
        out += '<rect x="0" y="0" width="94" height="196" rx="3" fill="' + f + '"/>';
        out += '<rect x="5" y="5" width="84" height="186" fill="' + d + '" opacity=".5"/>';
        var shelfY = [5, 43, 81, 119, 157];
        shelfY.forEach(function (y) {
          out += '<rect x="5" y="' + (y + 33) + '" width="84" height="5" fill="' + f + '"/>';
        });
        /* книги и мелочи */
        /* корешки книг — стоят на каждой полке */
        shelfY.forEach(function (y, i) {
          var bx = 9 + (i % 2) * 34, n = 5 + (i % 3);
          for (var k = 0; k < n; k++) {
            var bh = 22 + ((i + k) % 4) * 3;
            var col = ['#8C5A4A', '#3F5D6B', '#C7A05A', '#5E6B4E', '#7C6B8C', '#B08968'][(i + k) % 6];
            out += '<rect x="' + (bx + k * 6.5) + '" y="' + (y + 33 - bh) + '" width="5.4" height="' + bh +
              '" rx="1" fill="' + col + '"/>';
          }
          if (i === 1 || i === 3) {
            out += '<rect x="' + (bx + 44) + '" y="' + (y + 16) + '" width="18" height="17" rx="2" fill="' + sh(WOOD, 0.25) + '"/>';
          }
        });
        return out;
      }
    },

    wardrobe: {
      against: true, label: 'Шкаф', cat: 'floor', w: 128, h: 212,
      draw: function () {
        var f = sh(WOOD, 0.06), d = sh(WOOD, -0.26);
        return '' +
          '<rect x="0" y="0" width="128" height="212" rx="4" fill="' + f + '"/>' +
          '<rect x="4" y="4" width="58" height="200" rx="2" fill="' + sh(WOOD, 0.14) + '"/>' +
          '<rect x="66" y="4" width="58" height="200" rx="2" fill="' + sh(WOOD, 0.1) + '"/>' +
          '<line x1="64" y1="4" x2="64" y2="204" stroke="' + d + '" stroke-width="2"/>' +
          '<rect x="55" y="96" width="4" height="30" rx="2" fill="' + METAL + '"/>' +
          '<rect x="69" y="96" width="4" height="30" rx="2" fill="' + METAL + '"/>' +
          '<rect x="6" y="204" width="10" height="8" fill="' + d + '"/>' +
          '<rect x="112" y="204" width="10" height="8" fill="' + d + '"/>';
      }
    },

    dresser: {
      against: true, label: 'Комод', cat: 'floor', w: 104, h: 88,
      draw: function () {
        var f = sh(WOOD, 0.05), d = sh(WOOD, -0.26), out = '';
        out += '<rect x="0" y="0" width="104" height="76" rx="4" fill="' + f + '"/>';
        for (var i = 0; i < 3; i++) {
          out += '<rect x="6" y="' + (6 + i * 22) + '" width="92" height="18" rx="2.5" fill="' + sh(WOOD, 0.13) + '"/>';
          out += '<rect x="42" y="' + (13 + i * 22) + '" width="20" height="3.5" rx="1.75" fill="' + METAL + '"/>';
        }
        out += '<rect x="8" y="76" width="8" height="12" rx="2" fill="' + d + '"/>';
        out += '<rect x="88" y="76" width="8" height="12" rx="2" fill="' + d + '"/>';
        return out;
      }
    },

    nightstand: {
      label: 'Тумбочка', cat: 'floor', w: 46, h: 56,
      draw: function () {
        var f = sh(WOOD, 0.05), d = sh(WOOD, -0.26);
        return '' +
          '<rect x="0" y="0" width="46" height="44" rx="3" fill="' + f + '"/>' +
          '<rect x="4" y="5" width="38" height="15" rx="2" fill="' + sh(WOOD, 0.14) + '"/>' +
          '<rect x="4" y="23" width="38" height="15" rx="2" fill="' + sh(WOOD, 0.14) + '"/>' +
          '<rect x="17" y="11" width="12" height="3" rx="1.5" fill="' + METAL + '"/>' +
          '<rect x="17" y="29" width="12" height="3" rx="1.5" fill="' + METAL + '"/>' +
          '<rect x="4" y="44" width="5" height="12" fill="' + d + '"/>' +
          '<rect x="37" y="44" width="5" height="12" fill="' + d + '"/>';
      }
    },

    /* ---------------------------------------------- кровати */
    bedDouble: {
      against: true, label: 'Двуспальная кровать', cat: 'floor', w: 172, h: 96, tint: '#DAD3C6',
      draw: function (c) {
        var d = sh(c, -0.16), l = sh(c, 0.1);
        return '' +
          '<rect x="0" y="0" width="16" height="96" rx="4" fill="' + sh(WOOD, 0.02) + '"/>' +
          '<rect x="2" y="4" width="12" height="88" rx="3" fill="' + sh(WOOD, 0.14) + '"/>' +
          '<rect x="14" y="34" width="158" height="46" rx="6" fill="' + c + '"/>' +
          '<rect x="14" y="34" width="158" height="9" rx="4" fill="' + l + '"/>' +
          '<path d="M14 60 h158" stroke="' + d + '" stroke-width="1.4" opacity=".45"/>' +
          '<rect x="20" y="14" width="52" height="24" rx="7" fill="' + l + '"/>' +
          '<rect x="76" y="14" width="52" height="24" rx="7" fill="' + l + '"/>' +
          '<rect x="20" y="14" width="52" height="24" rx="7" fill="none" stroke="' + d + '" stroke-width="1" opacity=".4"/>' +
          '<rect x="76" y="14" width="52" height="24" rx="7" fill="none" stroke="' + d + '" stroke-width="1" opacity=".4"/>' +
          '<rect x="132" y="40" width="40" height="34" rx="5" fill="' + sh(c, -0.28) + '"/>' +
          '<rect x="150" y="80" width="10" height="16" fill="' + WOOD_D + '"/>' +
          '<rect x="18" y="80" width="10" height="16" fill="' + WOOD_D + '"/>';
      }
    },

    bedSingle: {
      against: true, label: 'Кровать', cat: 'floor', w: 112, h: 92, tint: '#9BAEB5',
      draw: function (c) {
        var d = sh(c, -0.16), l = sh(c, 0.1);
        return '' +
          '<rect x="0" y="0" width="14" height="92" rx="4" fill="' + sh(WOOD, 0.02) + '"/>' +
          '<rect x="2" y="4" width="10" height="84" rx="3" fill="' + sh(WOOD, 0.14) + '"/>' +
          '<rect x="12" y="36" width="100" height="42" rx="6" fill="' + c + '"/>' +
          '<rect x="12" y="36" width="100" height="8" rx="4" fill="' + l + '"/>' +
          '<rect x="18" y="18" width="46" height="22" rx="7" fill="' + l + '"/>' +
          '<rect x="18" y="18" width="46" height="22" rx="7" fill="none" stroke="' + d + '" stroke-width="1" opacity=".4"/>' +
          '<rect x="80" y="42" width="32" height="30" rx="5" fill="' + sh(c, -0.28) + '"/>' +
          '<rect x="16" y="78" width="9" height="14" fill="' + WOOD_D + '"/>' +
          '<rect x="94" y="78" width="9" height="14" fill="' + WOOD_D + '"/>';
      }
    },

    /* ---------------------------------------------- рабочее место */
    deskSetup: {
      against: true, label: 'Рабочий стол', cat: 'floor', w: 148, h: 118, tint: '#3C4045',
      draw: function (c) {
        var scr = '#1A1D21';
        return '' +
          /* стул */
          '<rect x="52" y="66" width="44" height="8" rx="4" fill="' + c + '"/>' +
          '<rect x="70" y="74" width="7" height="26" fill="' + METAL + '"/>' +
          '<path d="M58 100 h32 M74 100 v6" stroke="' + METAL + '" stroke-width="4" stroke-linecap="round"/>' +
          /* столешница */
          '<rect x="0" y="56" width="148" height="9" rx="3" fill="' + sh(WOOD, 0.08) + '"/>' +
          '<rect x="0" y="63" width="148" height="4" rx="2" fill="' + WOOD_D + '"/>' +
          '<rect x="8" y="67" width="6" height="51" fill="' + METAL + '"/>' +
          '<rect x="134" y="67" width="6" height="51" fill="' + METAL + '"/>' +
          /* монитор */
          '<rect x="40" y="10" width="70" height="40" rx="3" fill="' + scr + '"/>' +
          '<rect x="44" y="14" width="62" height="32" rx="2" fill="#2C4F63"/>' +
          '<rect x="44" y="14" width="62" height="32" rx="2" fill="url(#screenGlow)" opacity=".55"/>' +
          '<rect x="70" y="50" width="10" height="6" fill="' + METAL + '"/>' +
          '<rect x="58" y="54" width="34" height="4" rx="2" fill="' + METAL + '"/>' +
          /* клавиатура и мышь */
          '<rect x="52" y="52" width="0" height="0"/>' +
          '<rect x="18" y="53" width="34" height="4" rx="2" fill="' + sh(c, 0.25) + '"/>' +
          '<ellipse cx="122" cy="55" rx="5" ry="3.4" fill="' + sh(c, 0.25) + '"/>' +
          /* лампа */
          '<path d="M124 56 v-16 l10 -10" stroke="' + METAL + '" stroke-width="3" fill="none" stroke-linecap="round"/>' +
          '<path d="M129 32 l12 -6 l4 8 l-12 6 z" fill="' + sh(c, 0.15) + '"/>';
      },
      glow: { x: 75, y: 30, r: 60 }
    },

    deskChair: {
      label: 'Кресло', cat: 'floor', w: 62, h: 108, tint: '#3C4045',
      draw: function (c) {
        var l = sh(c, 0.16);
        return '' +
          '<rect x="14" y="0" width="34" height="52" rx="10" fill="' + c + '"/>' +
          '<rect x="19" y="6" width="24" height="40" rx="7" fill="' + l + '"/>' +
          '<rect x="8" y="52" width="46" height="12" rx="5" fill="' + c + '"/>' +
          '<rect x="4" y="42" width="7" height="14" rx="3" fill="' + sh(c, -0.2) + '"/>' +
          '<rect x="51" y="42" width="7" height="14" rx="3" fill="' + sh(c, -0.2) + '"/>' +
          '<rect x="27" y="64" width="8" height="30" fill="' + METAL + '"/>' +
          '<path d="M12 96 h38 M31 94 v8" stroke="' + METAL + '" stroke-width="5" stroke-linecap="round"/>' +
          '<circle cx="12" cy="102" r="5" fill="' + DARK + '"/>' +
          '<circle cx="50" cy="102" r="5" fill="' + DARK + '"/>';
      }
    },

    /* ---------------------------------------------- кухня */
    counterRun: {
      against: true, label: 'Кухонный гарнитур', cat: 'floor', w: 196, h: 92, tint: '#4F5A56',
      draw: function (c) {
        var d = sh(c, -0.18), l = sh(c, 0.1), out = '';
        out += '<rect x="0" y="8" width="196" height="80" rx="3" fill="' + c + '"/>';
        out += '<rect x="0" y="0" width="196" height="10" rx="3" fill="#DEDCD6"/>';
        out += '<rect x="0" y="8" width="196" height="3" fill="#B9B6AE"/>';
        for (var i = 0; i < 4; i++) {
          out += '<rect x="' + (5 + i * 48) + '" y="15" width="42" height="68" rx="2.5" fill="' + l + '"/>';
          out += '<rect x="' + (12 + i * 48) + '" y="21" width="28" height="3.4" rx="1.7" fill="' + METAL + '"/>';
        }
        out += '<rect x="0" y="88" width="196" height="4" fill="' + d + '"/>';
        /* мойка со смесителем */
        out += '<rect x="112" y="1" width="46" height="8" rx="2" fill="#B9B6AE"/>';
        out += '<path d="M136 1 v-16 q0 -6 8 -6 q8 0 8 6 v6" stroke="#9AA0A2" stroke-width="3.4" fill="none" stroke-linecap="round"/>';
        return out;
      }
    },

    island: {
      label: 'Остров', cat: 'floor', w: 152, h: 96, tint: '#2F3A42',
      draw: function (c) {
        var l = sh(c, 0.12);
        return '' +
          '<rect x="0" y="10" width="152" height="82" rx="3" fill="' + c + '"/>' +
          '<rect x="-6" y="0" width="164" height="12" rx="4" fill="#DEDCD6"/>' +
          '<rect x="-6" y="10" width="164" height="3" fill="#B9B6AE"/>' +
          '<rect x="8" y="20" width="60" height="62" rx="2.5" fill="' + l + '"/>' +
          '<rect x="84" y="20" width="60" height="62" rx="2.5" fill="' + l + '"/>' +
          '<rect x="28" y="27" width="22" height="3.4" rx="1.7" fill="' + METAL + '"/>' +
          '<rect x="104" y="27" width="22" height="3.4" rx="1.7" fill="' + METAL + '"/>' +
          '<rect x="0" y="92" width="152" height="4" fill="' + sh(c, -0.25) + '"/>';
      }
    },

    fridge: {
      against: true, label: 'Холодильник', cat: 'floor', w: 72, h: 188,
      draw: function () {
        var m = '#C8CBCC', d = '#9EA3A5';
        return '' +
          '<rect x="0" y="0" width="72" height="188" rx="5" fill="' + m + '"/>' +
          '<rect x="3" y="3" width="66" height="60" rx="3" fill="' + sh(m, 0.12) + '"/>' +
          '<rect x="3" y="67" width="66" height="118" rx="3" fill="' + sh(m, 0.12) + '"/>' +
          '<line x1="3" y1="64.5" x2="69" y2="64.5" stroke="' + d + '" stroke-width="2"/>' +
          '<rect x="56" y="20" width="4" height="34" rx="2" fill="' + d + '"/>' +
          '<rect x="56" y="78" width="4" height="46" rx="2" fill="' + d + '"/>' +
          '<rect x="6" y="6" width="10" height="176" rx="3" fill="#FFF" opacity=".22"/>';
      }
    },

    stove: {
      against: true, label: 'Плита', cat: 'floor', w: 64, h: 92,
      draw: function () {
        var m = '#C8CBCC';
        return '' +
          '<rect x="0" y="8" width="64" height="84" rx="3" fill="' + m + '"/>' +
          '<rect x="0" y="0" width="64" height="10" rx="2" fill="' + DARK + '"/>' +
          '<circle cx="18" cy="5" r="3.4" fill="#5B6265"/>' +
          '<circle cx="46" cy="5" r="3.4" fill="#5B6265"/>' +
          '<rect x="5" y="14" width="54" height="10" rx="2" fill="' + sh(m, -0.12) + '"/>' +
          '<circle cx="14" cy="19" r="3" fill="#7E8486"/><circle cx="26" cy="19" r="3" fill="#7E8486"/>' +
          '<circle cx="38" cy="19" r="3" fill="#7E8486"/><circle cx="50" cy="19" r="3" fill="#7E8486"/>' +
          '<rect x="5" y="30" width="54" height="56" rx="3" fill="#33393C"/>' +
          '<rect x="9" y="34" width="46" height="40" rx="2" fill="#4C5457"/>' +
          '<rect x="9" y="78" width="46" height="4" rx="2" fill="#9EA3A5"/>';
      }
    },

    diningTable: {
      label: 'Обеденный стол', cat: 'floor', w: 148, h: 76,
      draw: function () {
        return '' +
          '<rect x="14" y="12" width="7" height="64" fill="' + WOOD_D + '"/>' +
          '<rect x="127" y="12" width="7" height="64" fill="' + WOOD_D + '"/>' +
          '<rect x="18" y="18" width="112" height="5" fill="' + sh(WOOD, -0.1) + '"/>' +
          '<rect x="0" y="4" width="148" height="10" rx="4" fill="' + sh(WOOD, 0.08) + '"/>' +
          '<rect x="0" y="12" width="148" height="4" rx="2" fill="' + WOOD_D + '"/>' +
          '<rect x="6" y="5.5" width="136" height="3" rx="1.5" fill="' + sh(WOOD, 0.24) + '" opacity=".7"/>';
      }
    },

    diningChair: {
      label: 'Стул', cat: 'floor', w: 46, h: 92, tint: '#8A6A50',
      draw: function (c) {
        return '' +
          '<rect x="9" y="0" width="28" height="42" rx="6" fill="' + c + '"/>' +
          '<rect x="13" y="5" width="20" height="32" rx="4" fill="' + sh(c, 0.14) + '"/>' +
          '<rect x="3" y="42" width="40" height="8" rx="3" fill="' + sh(c, 0.06) + '"/>' +
          '<rect x="6" y="50" width="5" height="42" fill="' + sh(c, -0.24) + '"/>' +
          '<rect x="35" y="50" width="5" height="42" fill="' + sh(c, -0.24) + '"/>' +
          '<rect x="6" y="72" width="34" height="4" fill="' + sh(c, -0.18) + '"/>';
      }
    },

    /* ---------------------------------------------- декор на полу */
    plantBig: {
      label: 'Монстера', cat: 'floor', w: 88, h: 158,
      draw: function () {
        var g = '#3E6B4A', g2 = '#4F8259', pot = '#B9743F';
        function leaf(x, y, r, s) {
          return '<g transform="translate(' + x + ' ' + y + ') rotate(' + r + ') scale(' + s + ')">' +
            '<path d="M0 0 C22 -6 34 6 30 22 C26 38 8 44 -4 34 C-14 26 -12 8 0 0 Z" fill="' + g + '"/>' +
            '<path d="M2 4 C18 0 26 8 24 20" stroke="' + g2 + '" stroke-width="2" fill="none"/>' +
            '<path d="M28 12 l-9 3 M29 22 l-10 2 M22 32 l-8 -2" stroke="#2E5138" stroke-width="2.4" stroke-linecap="round"/>' +
            '</g>';
        }
        return '' +
          '<path d="M44 118 C40 92 34 70 26 52 M44 118 C48 92 56 72 66 56 M44 118 C44 96 44 74 44 44"' +
          ' stroke="#3F6B49" stroke-width="4" fill="none" stroke-linecap="round"/>' +
          leaf(6, 30, -18, 1.0) + leaf(52, 34, 12, 0.95) + leaf(24, 4, -4, 1.05) + leaf(58, 66, 26, 0.8) +
          leaf(2, 70, -30, 0.75) +
          '<path d="M22 118 h44 l-6 40 h-32 z" fill="' + pot + '"/>' +
          '<rect x="19" y="112" width="50" height="10" rx="3" fill="' + sh(pot, 0.12) + '"/>';
      }
    },

    plantSmall: {
      label: 'Растение', cat: 'floor', w: 44, h: 72,
      draw: function () {
        var pot = '#9A8B76';
        return '' +
          '<path d="M22 46 C10 40 6 24 12 12 C20 20 22 32 22 46 Z" fill="#4F8259"/>' +
          '<path d="M22 46 C34 40 40 24 34 10 C24 20 22 32 22 46 Z" fill="#3E6B4A"/>' +
          '<path d="M22 46 C22 34 22 20 22 6" stroke="#3E6B4A" stroke-width="3" fill="none" stroke-linecap="round"/>' +
          '<path d="M10 46 h24 l-3 26 h-18 z" fill="' + pot + '"/>' +
          '<rect x="8" y="42" width="28" height="7" rx="2.5" fill="' + sh(pot, 0.14) + '"/>';
      }
    },

    floorLamp: {
      label: 'Торшер', cat: 'floor', w: 46, h: 168,
      draw: function () {
        return '' +
          '<ellipse cx="23" cy="164" rx="18" ry="4.5" fill="' + DARK + '"/>' +
          '<rect x="20.5" y="36" width="5" height="128" fill="' + METAL + '"/>' +
          '<path d="M4 36 l8 -26 h22 l8 26 z" fill="#E4D9C4"/>' +
          '<path d="M4 36 l8 -26 h22 l8 26 z" fill="none" stroke="#C9BCA2" stroke-width="1.4"/>';
      },
      glow: { x: 23, y: 30, r: 90 }
    },

    rug: {
      label: 'Ковёр', cat: 'rug', w: 240, h: 170, tint: '#B8A990',
      draw: function (c) {
        var d = sh(c, -0.18), l = sh(c, 0.14);
        return '' +
          '<rect x="0" y="0" width="240" height="170" rx="6" fill="' + c + '"/>' +
          '<rect x="12" y="10" width="216" height="150" rx="4" fill="none" stroke="' + d + '" stroke-width="4"/>' +
          '<rect x="26" y="22" width="188" height="126" rx="3" fill="' + l + '" opacity=".55"/>' +
          '<path d="M60 22 v126 M120 22 v126 M180 22 v126" stroke="' + d + '" stroke-width="2" opacity=".35"/>';
      }
    },

    rugRound: {
      label: 'Круглый ковёр', cat: 'rug', w: 190, h: 190, tint: '#8C9A8E',
      draw: function (c) {
        var d = sh(c, -0.2), l = sh(c, 0.16);
        return '' +
          '<ellipse cx="95" cy="95" rx="95" ry="95" fill="' + c + '"/>' +
          '<ellipse cx="95" cy="95" rx="76" ry="76" fill="none" stroke="' + l + '" stroke-width="8"/>' +
          '<ellipse cx="95" cy="95" rx="50" ry="50" fill="none" stroke="' + d + '" stroke-width="6"/>' +
          '<ellipse cx="95" cy="95" rx="24" ry="24" fill="' + l + '" opacity=".7"/>';
      }
    },

    /* ---------------------------------------------- настенные */
    tv: {
      label: 'Телевизор', cat: 'wall', w: 132, h: 78,
      draw: function () {
        return '' +
          '<rect x="0" y="0" width="132" height="76" rx="3" fill="#191C1F"/>' +
          '<rect x="3" y="3" width="126" height="66" rx="2" fill="#20343F"/>' +
          '<rect x="3" y="3" width="126" height="66" rx="2" fill="url(#screenGlow)" opacity=".5"/>' +
          '<rect x="3" y="3" width="126" height="20" rx="2" fill="#FFF" opacity=".06"/>';
      },
      glow: { x: 66, y: 38, r: 110 }
    },

    artLarge: {
      label: 'Картина', cat: 'wall', w: 92, h: 118, tint: '#7C8F9E',
      draw: function (c) {
        return '' +
          '<rect x="0" y="0" width="92" height="118" rx="2" fill="' + sh(WOOD, 0.1) + '"/>' +
          '<rect x="6" y="6" width="80" height="106" fill="#F2EFE8"/>' +
          '<rect x="12" y="12" width="68" height="94" fill="' + c + '"/>' +
          '<path d="M12 82 L34 52 L52 76 L66 60 L80 82 Z" fill="' + sh(c, -0.3) + '"/>' +
          '<circle cx="62" cy="34" r="9" fill="' + sh(c, 0.35) + '"/>';
      }
    },

    posterTrio: {
      label: 'Постеры', cat: 'wall', w: 128, h: 70, tint: '#C8794F',
      draw: function (c) {
        return '' +
          '<rect x="0" y="4" width="38" height="52" rx="1.5" fill="#EFECE5" stroke="#2F3336" stroke-width="1.6"/>' +
          '<rect x="6" y="10" width="26" height="40" fill="' + c + '"/>' +
          '<rect x="46" y="0" width="38" height="60" rx="1.5" fill="#EFECE5" stroke="#2F3336" stroke-width="1.6"/>' +
          '<circle cx="65" cy="30" r="14" fill="' + sh(c, -0.25) + '"/>' +
          '<rect x="92" y="8" width="36" height="48" rx="1.5" fill="#EFECE5" stroke="#2F3336" stroke-width="1.6"/>' +
          '<path d="M98 48 l10 -18 l8 12 l6 -8 v14 z" fill="' + sh(c, 0.2) + '"/>';
      }
    },

    shelfWall: {
      label: 'Полка', cat: 'wall', w: 112, h: 36,
      draw: function () {
        var out = '<rect x="0" y="26" width="112" height="7" rx="2" fill="' + sh(WOOD, 0.06) + '"/>';
        out += '<rect x="0" y="31" width="112" height="3" rx="1.5" fill="' + WOOD_D + '"/>';
        var cols = ['#8C5A4A', '#3F5D6B', '#C7A05A', '#5E6B4E', '#7C6B8C'];
        for (var i = 0; i < 6; i++) {
          out += '<rect x="' + (8 + i * 7) + '" y="' + (26 - (16 + (i % 3) * 4)) + '" width="5.6" height="' +
            (16 + (i % 3) * 4) + '" rx="1" fill="' + cols[i % 5] + '"/>';
        }
        out += '<path d="M74 26 C68 20 70 12 78 12 C86 12 88 20 82 26 Z" fill="#4F8259"/>';
        out += '<rect x="74" y="18" width="12" height="8" rx="2" fill="#9A8B76"/>';
        return out;
      }
    },

    mirror: {
      label: 'Зеркало', cat: 'wall', w: 60, h: 92,
      draw: function () {
        return '' +
          '<rect x="0" y="0" width="60" height="92" rx="30" fill="' + METAL + '"/>' +
          '<rect x="4" y="4" width="52" height="84" rx="26" fill="#C7D6DB"/>' +
          '<path d="M12 70 L34 24 L48 48 L48 84 L14 84 Z" fill="#FFF" opacity=".35"/>';
      }
    },

    windowUnit: {
      label: 'Окно', cat: 'wall', w: 156, h: 132,
      draw: function () {
        return '' +
          '<rect x="-6" y="-6" width="168" height="144" rx="3" fill="#EFEDE7"/>' +
          '<rect x="0" y="0" width="156" height="132" fill="#BBD8E8"/>' +
          '<rect x="0" y="0" width="156" height="132" fill="url(#screenGlow)" opacity=".35"/>' +
          '<rect x="74" y="0" width="8" height="132" fill="#EFEDE7"/>' +
          '<rect x="0" y="62" width="156" height="8" fill="#EFEDE7"/>' +
          '<path d="M8 124 L58 8 L74 8 L20 124 Z" fill="#FFF" opacity=".3"/>' +
          '<rect x="-10" y="132" width="176" height="9" rx="2" fill="#E2DFD7"/>';
      },
      glow: { x: 78, y: 66, r: 150 }
    },

    stringLights: {
      label: 'Гирлянда', cat: 'wall', w: 220, h: 60,
      draw: function () {
        var out = '<path d="M0 6 Q55 46 110 14 Q165 46 220 8" stroke="#6E6A62" stroke-width="1.8" fill="none"/>';
        for (var i = 0; i <= 12; i++) {
          var t = i / 12, x, y;
          if (t < 0.5) { var u = t / 0.5; x = 110 * u; y = 6 + (46 - 6) * 2 * u * (1 - u) + (14 - 6) * u * u; }
          else { var v = (t - 0.5) / 0.5; x = 110 + 110 * v; y = 14 + (46 - 14) * 2 * v * (1 - v) + (8 - 14) * v * v; }
          out += '<circle cx="' + x.toFixed(1) + '" cy="' + (y + 5).toFixed(1) + '" r="3.6" fill="#F5D98C"/>';
        }
        return out;
      },
      glow: { x: 110, y: 24, r: 150 }
    },

    wallClock: {
      label: 'Часы', cat: 'wall', w: 42, h: 42,
      draw: function () {
        return '' +
          '<circle cx="21" cy="21" r="21" fill="' + DARK + '"/>' +
          '<circle cx="21" cy="21" r="17" fill="#EFEDE7"/>' +
          '<path d="M21 21 V9 M21 21 L30 26" stroke="' + DARK + '" stroke-width="2.4" stroke-linecap="round"/>' +
          '<circle cx="21" cy="21" r="2" fill="#B5533E"/>';
      }
    },

    upperCabinets: {
      label: 'Верхние шкафы', cat: 'wall', w: 196, h: 72, tint: '#4F5A56',
      draw: function (c) {
        var l = sh(c, 0.1), out = '<rect x="0" y="0" width="196" height="70" rx="3" fill="' + c + '"/>';
        for (var i = 0; i < 4; i++) {
          out += '<rect x="' + (5 + i * 48) + '" y="5" width="42" height="60" rx="2.5" fill="' + l + '"/>';
          out += '<rect x="' + (12 + i * 48) + '" y="55" width="28" height="3.4" rx="1.7" fill="' + METAL + '"/>';
        }
        out += '<rect x="0" y="70" width="196" height="3" fill="' + sh(c, -0.25) + '"/>';
        return out;
      }
    },

    pendantLamp: {
      label: 'Подвес', cat: 'wall', w: 54, h: 96,
      draw: function () {
        return '' +
          '<rect x="25" y="0" width="3" height="56" fill="' + METAL + '"/>' +
          '<path d="M2 92 L14 56 h26 l12 36 z" fill="' + sh('#C79A3C', -0.05) + '"/>' +
          '<ellipse cx="27" cy="92" rx="25" ry="5" fill="#F5E3B0"/>';
      },
      glow: { x: 27, y: 94, r: 100 }
    }
  };

  /* ---------------------------------------------- состав комнат */

  var ROOMS = [
    {
      id: 'living', label: 'Гостиная',
      wall: 'greige', floor: 'oakLight',
      items: ['sofa3', 'armchair', 'coffeeTable', 'mediaConsole', 'bookshelf', 'sideTable', 'pouf',
              'floorLamp', 'plantBig', 'plantSmall', 'rug', 'rugRound',
              'tv', 'artLarge', 'shelfWall', 'windowUnit', 'wallClock', 'pendantLamp']
    },
    {
      id: 'room', label: 'Моя комната',
      wall: 'navy', floor: 'oakMid',
      items: ['bedSingle', 'bedDouble', 'deskSetup', 'deskChair', 'wardrobe', 'nightstand', 'dresser',
              'beanbag', 'bookshelf', 'floorLamp', 'plantSmall', 'rugRound', 'rug',
              'posterTrio', 'stringLights', 'shelfWall', 'mirror', 'windowUnit', 'tv']
    },
    {
      id: 'kitchen', label: 'Кухня',
      wall: 'chalk', floor: 'checker',
      items: ['counterRun', 'island', 'fridge', 'stove', 'diningTable', 'diningChair',
              'plantSmall', 'rug', 'upperCabinets', 'pendantLamp', 'wallClock', 'windowUnit', 'shelfWall']
    }
  ];

  /* ==========================================================
     ЭКСТЕРЬЕР
     ========================================================== */

  var EXT_WALL = [
    { id: 'plasterW', label: 'Штукатурка', kind: 'plain',  color: '#EDE9E1' },
    { id: 'plasterG', label: 'Серый',      kind: 'plain',  color: '#B7B4AD' },
    { id: 'battenN',  label: 'Дерево',     kind: 'batten', color: '#C08F55' },
    { id: 'battenD',  label: 'Тёмное дерево', kind: 'batten', color: '#5E4632' },
    { id: 'brickR',   label: 'Кирпич',     kind: 'brick',  color: '#A8624E' },
    { id: 'brickW',   label: 'Белый кирпич', kind: 'brick', color: '#DCD7CE' },
    { id: 'stone',    label: 'Камень',     kind: 'stone',  color: '#A9A69D' },
    { id: 'charcoal', label: 'Графит',     kind: 'plain',  color: '#40444A' },
    { id: 'sageH',    label: 'Шалфей',     kind: 'plain',  color: '#93A48F' },
    { id: 'navyH',    label: 'Синий',      kind: 'plain',  color: '#3A5573' }
  ];

  var EXT_ROOF = [
    { id: 'seam',   label: 'Фальц',     kind: 'seam',   color: '#4C5257' },
    { id: 'seamD',  label: 'Тёмный металл', kind: 'seam', color: '#2C3134' },
    { id: 'tile',   label: 'Черепица',  kind: 'tile',   color: '#9A5745' },
    { id: 'tileG',  label: 'Серая черепица', kind: 'tile', color: '#6E7276' },
    { id: 'shingle',label: 'Гонт',      kind: 'shingle',color: '#5B4A3C' },
    { id: 'green',  label: 'Зелёная кровля', kind: 'grass', color: '#6B8C56' }
  ];

  var TIMES = [
    { id: 'day',    label: 'День',   sky: ['#8CC5E8', '#CFE7F4'], sun: '#FDF3D0', amb: 'rgba(0,0,0,0)',        glass: '#BBD8E8', glassOp: 1 },
    { id: 'sunset', label: 'Закат',  sky: ['#F0A860', '#F7D9A8'], sun: '#FFE7B0', amb: 'rgba(224,132,60,.20)', glass: '#F4C98A', glassOp: 1 },
    { id: 'night',  label: 'Ночь',   sky: ['#101C33', '#263A57'], sun: '#E8EEF8', amb: 'rgba(12,22,44,.46)',   glass: '#F7D48A', glassOp: 1 }
  ];

  /* --- вспомогательные текстуры для фасада --- */
  function facade(mat, x, y, w, h, p, rx) {
    var c = mat.color, out = '';
    out += '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="' + (rx || 0) + '" fill="' + c + '"/>';
    if (mat.kind === 'batten') {
      out += '<g>';
      for (var bx = x + 3; bx < x + w - 1; bx += 9) {
        out += '<rect x="' + bx.toFixed(1) + '" y="' + y + '" width="5.4" height="' + h + '" fill="' + sh(c, 0.08) + '"/>';
        out += '<rect x="' + (bx + 5.4).toFixed(1) + '" y="' + y + '" width="2.2" height="' + h + '" fill="' + sh(c, -0.3) + '"/>';
      }
      out += '</g>';
    } else if (mat.kind === 'brick') {
      var bh = 8, bw = 20, r = 0;
      out += '<g stroke="' + sh(c, -0.2) + '" stroke-width="1.1" opacity=".8">';
      for (var yy = y; yy < y + h; yy += bh, r++) {
        out += '<line x1="' + x + '" y1="' + yy.toFixed(1) + '" x2="' + (x + w) + '" y2="' + yy.toFixed(1) + '"/>';
        for (var xx = x + ((r % 2) ? bw / 2 : 0); xx < x + w; xx += bw) {
          out += '<line x1="' + xx.toFixed(1) + '" y1="' + yy.toFixed(1) + '" x2="' + xx.toFixed(1) +
            '" y2="' + Math.min(yy + bh, y + h).toFixed(1) + '"/>';
        }
      }
      out += '</g>';
    } else if (mat.kind === 'stone') {
      out += '<g stroke="' + sh(c, -0.22) + '" stroke-width="1.3" fill="none" opacity=".75">';
      for (var sy = y + 10; sy < y + h; sy += 13) {
        out += '<line x1="' + x + '" y1="' + sy.toFixed(1) + '" x2="' + (x + w) + '" y2="' + sy.toFixed(1) + '"/>';
        var seed = (sy * 7) % 23;
        for (var sx = x + 8 + seed; sx < x + w; sx += 26 + (seed % 9)) {
          out += '<line x1="' + sx.toFixed(1) + '" y1="' + sy.toFixed(1) + '" x2="' + sx.toFixed(1) +
            '" y2="' + Math.min(sy + 13, y + h).toFixed(1) + '"/>';
        }
      }
      out += '</g>';
    }
    /* общий объём: свет слева, тень справа */
    out += '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="' + (rx || 0) +
      '" fill="url(#' + p + 'facade)"/>';
    return out;
  }

  function roofTex(mat, pts, p, id) {
    var c = mat.color, out = '';
    out += '<clipPath id="' + p + id + '"><polygon points="' + pts + '"/></clipPath>';
    out += '<polygon points="' + pts + '" fill="' + c + '"/>';
    out += '<g clip-path="url(#' + p + id + ')">';
    var bb = pts.split(' ').map(function (s) { return s.split(',').map(Number); });
    var minX = Math.min.apply(null, bb.map(function (q) { return q[0]; }));
    var maxX = Math.max.apply(null, bb.map(function (q) { return q[0]; }));
    var minY = Math.min.apply(null, bb.map(function (q) { return q[1]; }));
    var maxY = Math.max.apply(null, bb.map(function (q) { return q[1]; }));
    if (mat.kind === 'seam') {
      out += '<g stroke="' + sh(c, -0.28) + '" stroke-width="1.6">';
      for (var x = minX; x <= maxX; x += 11) {
        out += '<line x1="' + x.toFixed(1) + '" y1="' + minY + '" x2="' + x.toFixed(1) + '" y2="' + maxY + '"/>';
      }
      out += '</g>';
    } else if (mat.kind === 'tile') {
      out += '<g fill="' + sh(c, -0.16) + '">';
      for (var ty = minY; ty <= maxY; ty += 9) {
        for (var tx = minX; tx <= maxX; tx += 12) {
          out += '<rect x="' + (tx + ((ty / 9 | 0) % 2 ? 6 : 0)).toFixed(1) + '" y="' + ty.toFixed(1) +
            '" width="10" height="4" rx="2"/>';
        }
      }
      out += '</g>';
    } else if (mat.kind === 'shingle') {
      out += '<g fill="' + sh(c, -0.18) + '">';
      for (var sy = minY; sy <= maxY; sy += 7) {
        for (var sx2 = minX; sx2 <= maxX; sx2 += 16) {
          out += '<rect x="' + (sx2 + ((sy / 7 | 0) % 2 ? 8 : 0)).toFixed(1) + '" y="' + sy.toFixed(1) +
            '" width="14" height="3" rx="1"/>';
        }
      }
      out += '</g>';
    } else if (mat.kind === 'grass') {
      out += '<g stroke="' + sh(c, -0.22) + '" stroke-width="1.4" stroke-linecap="round">';
      for (var gx = minX; gx <= maxX; gx += 6) {
        out += '<line x1="' + gx.toFixed(1) + '" y1="' + (minY + ((gx * 3) % 9)).toFixed(1) +
          '" x2="' + (gx + 2).toFixed(1) + '" y2="' + (minY + ((gx * 3) % 9) + 6).toFixed(1) + '"/>';
      }
      out += '</g>';
    }
    out += '<polygon points="' + pts + '" fill="url(#' + p + 'roofShade)"/>';
    out += '</g>';
    return out;
  }

  function win(x, y, w, h, cols, rows) {
    var out = '<rect x="' + (x - 2) + '" y="' + (y - 2) + '" width="' + (w + 4) + '" height="' + (h + 4) +
      '" rx="1.5" class="frame"/>';
    out += '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" class="glass"/>';
    out += '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" fill="url(#glassSheen)"/>';
    var i;
    for (i = 1; i < (cols || 1); i++) {
      out += '<rect x="' + (x + w * i / cols - 1.2) + '" y="' + y + '" width="2.4" height="' + h + '" class="frame"/>';
    }
    for (i = 1; i < (rows || 1); i++) {
      out += '<rect x="' + x + '" y="' + (y + h * i / rows - 1.2) + '" width="' + w + '" height="2.4" class="frame"/>';
    }
    return out;
  }

  function door(x, y, w, h) {
    return '' +
      '<rect x="' + (x - 2.5) + '" y="' + (y - 2.5) + '" width="' + (w + 5) + '" height="' + (h + 2.5) + '" rx="2" class="frame"/>' +
      '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="1.5" class="door"/>' +
      '<rect x="' + (x + 4) + '" y="' + (y + 5) + '" width="' + (w - 8) + '" height="' + (h * 0.42) + '" rx="1" class="doorPanel"/>' +
      '<rect x="' + (x + 4) + '" y="' + (y + h * 0.5 + 3) + '" width="' + (w - 8) + '" height="' + (h * 0.38) + '" rx="1" class="doorPanel"/>' +
      '<circle cx="' + (x + w - 6) + '" cy="' + (y + h * 0.55) + '" r="2.2" fill="#D7B25E"/>';
  }

  /* --- стили домов (viewBox 0 0 460 300, земля на y=300) --- */
  var HOUSE_STYLES = [
    {
      id: 'nordic', label: 'Скандинавский',
      lights: [[157, 206, 78], [307, 206, 78], [230, 112, 52], [230, 266, 56]],
      draw: function (wm, rm, p) {
        var out = '';
        out += roofTex(rm, '72,148 230,44 388,148 366,148 230,64 94,148', p, 'r1');
        out += facade(wm, 96, 146, 268, 154, p);
        out += '<rect x="94" y="144" width="272" height="6" class="frame"/>';
        out += win(126, 168, 62, 76, 2, 2);
        out += win(276, 168, 62, 76, 2, 2);
        out += win(206, 92, 48, 40, 2, 1);
        out += door(206, 232, 48, 68);
        out += '<rect x="196" y="228" width="68" height="5" rx="2" class="frame"/>';
        out += '<rect x="300" y="62" width="22" height="52" fill="' + sh(wm.color, -0.24) + '"/>';
        out += '<rect x="296" y="56" width="30" height="9" rx="2" fill="' + sh(wm.color, -0.36) + '"/>';
        return out;
      }
    },
    {
      id: 'modern', label: 'Современный',
      lights: [[149, 247, 92], [244, 136, 70], [352, 136, 70], [278, 260, 58]],
      draw: function (wm, rm, p) {
        var out = '';
        /* нижний объём */
        out += facade(wm, 60, 186, 340, 114, p);
        out += roofTex(rm, '48,178 412,178 412,190 48,190', p, 'r1');
        /* верхний объём со сдвигом — консоль */
        out += facade({ kind: 'plain', color: sh(wm.color, -0.3) }, 176, 84, 236, 104, p);
        out += roofTex(rm, '166,76 422,76 422,88 166,88', p, 'r2');
        /* панорамное остекление */
        out += win(84, 206, 130, 82, 3, 1);
        out += win(196, 104, 96, 64, 2, 1);
        out += win(306, 104, 92, 64, 2, 1);
        out += door(252, 220, 52, 80);
        out += '<rect x="240" y="296" width="76" height="4" rx="2" class="frame"/>';
        /* навес-карпорт */
        out += '<rect x="46" y="186" width="10" height="114" fill="' + sh(wm.color, -0.4) + '"/>';
        return out;
      }
    },
    {
      id: 'twoStory', label: 'Двухэтажный',
      lights: [[151, 168, 62], [230, 168, 62], [309, 168, 62], [151, 249, 66], [309, 249, 66], [230, 263, 54]],
      draw: function (wm, rm, p) {
        var out = '';
        out += roofTex(rm, '76,124 230,40 384,124 360,124 230,58 100,124', p, 'r1');
        out += facade(wm, 100, 122, 260, 178, p);
        out += '<rect x="98" y="120" width="264" height="6" class="frame"/>';
        out += win(124, 142, 54, 52, 2, 1);
        out += win(203, 142, 54, 52, 2, 1);
        out += win(282, 142, 54, 52, 2, 1);
        out += win(124, 220, 54, 58, 2, 2);
        out += win(282, 220, 54, 58, 2, 2);
        out += door(204, 226, 52, 74);
        /* балкон */
        out += '<rect x="192" y="196" width="76" height="5" rx="2" class="frame"/>';
        out += '<g stroke="#8E9398" stroke-width="2.4">';
        for (var bx = 196; bx <= 264; bx += 9) out += '<line x1="' + bx + '" y1="176" x2="' + bx + '" y2="196"/>';
        out += '</g><rect x="190" y="174" width="80" height="4" rx="2" fill="#8E9398"/>';
        out += '<rect x="322" y="54" width="20" height="52" fill="' + sh(wm.color, -0.24) + '"/>';
        return out;
      }
    },
    {
      id: 'aframe', label: 'A-frame',
      lights: [[230, 180, 118], [230, 266, 56]],
      draw: function (wm, rm, p) {
        var out = '';
        out += facade(wm, 148, 150, 164, 150, p);
        out += roofTex(rm, '56,300 230,28 404,300 356,300 230,90 104,300', p, 'r1');
        /* фронтальное остекление треугольником */
        out += '<polygon points="230,96 336,262 124,262" class="glass"/>';
        out += '<polygon points="230,96 336,262 124,262" fill="url(#glassSheen)"/>';
        out += '<g class="frameStroke">';
        out += '<path d="M230 96 V262 M177 179 H283 M151 230 H309" stroke="currentColor" stroke-width="4"/>';
        out += '</g>';
        out += '<polygon points="230,96 336,262 124,262" fill="none" class="frameLine"/>';
        out += door(206, 232, 48, 68);
        out += '<rect x="196" y="228" width="68" height="5" rx="2" class="frame"/>';
        return out;
      }
    }
  ];

  /* --- деревья, кусты и прочая зелень --- */
  function treeDeciduous(x, groundY, s, tone) {
    var g1 = sh('#4F7A46', tone), g2 = sh('#3D6338', tone), g3 = sh('#639158', tone);
    return '<g transform="translate(' + x + ' ' + groundY + ') scale(' + s + ')">' +
      '<path d="M-4 0 L-3 -46 L3 -46 L4 0 Z" fill="#6B5137"/>' +
      '<path d="M0 -44 L-14 -58 M0 -50 L13 -62" stroke="#6B5137" stroke-width="3.4" stroke-linecap="round"/>' +
      '<ellipse cx="0" cy="-78" rx="36" ry="30" fill="' + g2 + '"/>' +
      '<ellipse cx="-16" cy="-70" rx="26" ry="22" fill="' + g1 + '"/>' +
      '<ellipse cx="16" cy="-86" rx="24" ry="21" fill="' + g3 + '"/>' +
      '<ellipse cx="4" cy="-98" rx="20" ry="16" fill="' + g1 + '"/>' +
      '</g>';
  }

  function treeConifer(x, groundY, s, tone) {
    var g1 = sh('#39603C', tone), g2 = sh('#2C4B30', tone);
    return '<g transform="translate(' + x + ' ' + groundY + ') scale(' + s + ')">' +
      '<rect x="-3.5" y="-22" width="7" height="22" fill="#5B452F"/>' +
      '<path d="M0 -128 L26 -74 L-26 -74 Z" fill="' + g1 + '"/>' +
      '<path d="M0 -104 L31 -44 L-31 -44 Z" fill="' + g2 + '"/>' +
      '<path d="M0 -78 L36 -18 L-36 -18 Z" fill="' + g1 + '"/>' +
      '</g>';
  }

  function bush(x, groundY, s) {
    return '<g transform="translate(' + x + ' ' + groundY + ') scale(' + s + ')">' +
      '<ellipse cx="0" cy="-14" rx="26" ry="16" fill="#426B3E"/>' +
      '<ellipse cx="-12" cy="-18" rx="16" ry="13" fill="#4F7A46"/>' +
      '<ellipse cx="13" cy="-20" rx="14" ry="12" fill="#5A8850"/>' +
      '</g>';
  }

  return {
    sh: sh, lum: lum, icon: icon, ICONS: ICONS,
    WALL_MATERIALS: WALL_MATERIALS, FLOOR_MATERIALS: FLOOR_MATERIALS,
    renderWall: renderWall, renderFloor: renderFloor,
    FURNITURE: FURNITURE, ROOMS: ROOMS,
    EXT_WALL: EXT_WALL, EXT_ROOF: EXT_ROOF, TIMES: TIMES,
    HOUSE_STYLES: HOUSE_STYLES,
    facade: facade, roofTex: roofTex, win: win, door: door,
    treeDeciduous: treeDeciduous, treeConifer: treeConifer, bush: bush
  };
})();
