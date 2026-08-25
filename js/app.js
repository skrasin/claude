/* ============================================================
   Дом мечты — логика приложения.
   Комната строится в одноточечной перспективе: предмет, стоящий
   дальше от зрителя, действительно меньше и уходит за ближние.
   ============================================================ */
(function () {
  'use strict';

  var A = window.ASSETS;
  var $ = function (id) { return document.getElementById(id); };

  /* ---------------------------------------------------------- геометрия комнаты */

  var ROOM = (function () {
    var W = 1000, H = 750;
    var HALF_CM = 350;                 /* полширины комнаты, см */
    var WALL_CM = 270;                 /* высота стены, см */
    var back = W / (HALF_CM * 2);      /* px на см у дальней стены */
    var wallY = WALL_CM * back;
    var DEPTH = 0.5;                   /* насколько крупнее предмет у зрителя */

    function pxAt(fy) { return back * (1 + DEPTH * fy); }
    function xAt(cm, fy) { return W / 2 + cm * pxAt(fy); }
    function yAt(fy) { return wallY + fy * (H - wallY); }
    function fyFromY(y) { return clamp((y - wallY) / (H - wallY), 0, 1); }
    function cmFromX(x, fy) { return (x - W / 2) / pxAt(fy); }

    /* Ближе к зрителю кадр «сужается» в сантиметрах — держим предмет в кадре. */
    function limFor(fy, wcm) {
      return Math.max(0, Math.min(HALF_CM, (W / 2) / pxAt(fy)) - wcm / 2);
    }

    return { W: W, H: H, HALF_CM: HALF_CM, WALL_CM: WALL_CM, back: back,
             wallY: wallY, pxAt: pxAt, xAt: xAt, yAt: yAt,
             fyFromY: fyFromY, cmFromX: cmFromX, limFor: limFor };
  })();

  var EXT = { W: 1000, H: 690, ground: 470, houseBase: 512, houseScale: 1.18 };

  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
  function uid() { return Math.random().toString(36).slice(2, 9) + Date.now().toString(36).slice(-4); }

  /* ---------------------------------------------------------- состояние */

  var KEY = 'dreamHouse.v2';

  var state = {
    houses: load(),
    houseId: null,
    roomId: null,
    extTab: 'style',
    roomTab: 'items',
    sel: null
  };

  function load() {
    try { var raw = localStorage.getItem(KEY); return raw ? JSON.parse(raw) : []; }
    catch (e) { return []; }
  }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(state.houses)); } catch (e) {}
  }
  function house() {
    for (var i = 0; i < state.houses.length; i++) {
      if (state.houses[i].id === state.houseId) return state.houses[i];
    }
    return null;
  }
  function findHouse(id) {
    for (var i = 0; i < state.houses.length; i++) if (state.houses[i].id === id) return state.houses[i];
    return null;
  }
  function room() { var h = house(); return h ? h.rooms[state.roomId] : null; }
  function roomDef(id) {
    for (var i = 0; i < A.ROOMS.length; i++) if (A.ROOMS[i].id === id) return A.ROOMS[i];
    return null;
  }
  function mat(list, id) {
    for (var i = 0; i < list.length; i++) if (list[i].id === id) return list[i];
    return list[0];
  }

  var DOOR_COLORS = ['#2F3336', '#7A4A32', '#2E6A57', '#8C3F35', '#D8D4CB', '#3A5573', '#A8802E', '#5B4A3C'];
  var PATHS = [
    { id: 'stone',  label: 'Плитка',  colors: ['#CDC8BE', '#B8B2A6'] },
    { id: 'gravel', label: 'Гравий',  colors: ['#C4BCAA', '#ADA492'] },
    { id: 'deck',   label: 'Дерево',  colors: ['#B08A5C', '#95714A'] },
    { id: 'dark',   label: 'Бетон',   colors: ['#9C9A94', '#89877F'] }
  ];
  var LAWNS = ['#6E9B4E', '#5C8B45', '#84A85E', '#7E9668'];

  function newHouse(name) {
    var h = {
      id: uid(),
      name: name || 'Дом мечты',
      created: Date.now(),
      ext: {
        style: 'nordic', wall: 'plasterW', roof: 'seam',
        door: '#2F3336', frame: '#EFEDE7',
        time: 'day', lawn: 0, path: 'stone',
        trees: 3, conifer: false, bushes: true, flowers: true, fence: false, lights: true
      },
      rooms: {}
    };
    A.ROOMS.forEach(function (r) {
      h.rooms[r.id] = { wall: r.wall, floor: r.floor, mood: 'day', items: [] };
    });
    return h;
  }

  /* ---------------------------------------------------------- звук */

  var actx = null;
  function tick(freq, vol) {
    try {
      var AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return;
      if (!actx) actx = new AC();
      if (actx.state === 'suspended') actx.resume();
      var o = actx.createOscillator(), g = actx.createGain();
      o.type = 'triangle';
      o.frequency.value = freq || 520;
      g.gain.setValueAtTime(0.0001, actx.currentTime);
      g.gain.exponentialRampToValueAtTime(vol || 0.05, actx.currentTime + 0.008);
      g.gain.exponentialRampToValueAtTime(0.0001, actx.currentTime + 0.11);
      o.connect(g); g.connect(actx.destination);
      o.start(); o.stop(actx.currentTime + 0.13);
    } catch (e) {}
  }

  var toastT = null;
  function toast(msg) {
    var t = $('toast');
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(toastT);
    toastT = setTimeout(function () { t.classList.remove('show'); }, 1900);
  }

  var confirmCb = null;
  function ask(title, text, label, cb) {
    $('confirm-title').textContent = title;
    $('confirm-text').textContent = text;
    $('confirm-yes').textContent = label;
    $('confirm').hidden = false;
    confirmCb = cb;
  }

  /* ==========================================================
     ОБЩИЕ DEFS
     ========================================================== */

  function defs(p) {
    return '<defs>' +
      '<linearGradient id="screenGlow" x1="0" y1="0" x2="0.6" y2="1">' +
        '<stop offset="0" stop-color="#FFFFFF" stop-opacity=".45"/>' +
        '<stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient>' +
      '<linearGradient id="glassSheen" x1="0" y1="0" x2="0.7" y2="1">' +
        '<stop offset="0" stop-color="#FFFFFF" stop-opacity=".38"/>' +
        '<stop offset=".55" stop-color="#FFFFFF" stop-opacity=".05"/>' +
        '<stop offset="1" stop-color="#FFFFFF" stop-opacity=".16"/></linearGradient>' +
      '<pattern id="' + p + 'wgrain" width="7" height="7" patternUnits="userSpaceOnUse">' +
        '<circle cx="1.5" cy="1.5" r="0.9" fill="#000" opacity=".05"/>' +
        '<circle cx="5" cy="4" r="0.7" fill="#fff" opacity=".07"/>' +
        '<circle cx="3" cy="6" r="0.6" fill="#000" opacity=".04"/></pattern>' +
      '<radialGradient id="' + p + 'wvign" cx="0.5" cy="0.32" r="0.85">' +
        '<stop offset="0" stop-color="#fff" stop-opacity=".10"/>' +
        '<stop offset=".55" stop-color="#000" stop-opacity="0"/>' +
        '<stop offset="1" stop-color="#000" stop-opacity=".16"/></radialGradient>' +
      '<linearGradient id="' + p + 'fshade" x1="0" y1="0" x2="0" y2="1">' +
        '<stop offset="0" stop-color="#000" stop-opacity=".20"/>' +
        '<stop offset=".45" stop-color="#000" stop-opacity=".04"/>' +
        '<stop offset="1" stop-color="#fff" stop-opacity=".07"/></linearGradient>' +
      '<radialGradient id="' + p + 'lamp" cx="0.5" cy="0.5" r="0.5">' +
        '<stop offset="0" stop-color="#FFD98A" stop-opacity=".62"/>' +
        '<stop offset=".45" stop-color="#FFC96B" stop-opacity=".26"/>' +
        '<stop offset="1" stop-color="#FFC96B" stop-opacity="0"/></radialGradient>' +
      '<linearGradient id="' + p + 'facade" x1="0" y1="0" x2="1" y2="0.25">' +
        '<stop offset="0" stop-color="#fff" stop-opacity=".14"/>' +
        '<stop offset=".55" stop-color="#000" stop-opacity="0"/>' +
        '<stop offset="1" stop-color="#000" stop-opacity=".18"/></linearGradient>' +
      '<linearGradient id="' + p + 'roofShade" x1="0" y1="0" x2="0.3" y2="1">' +
        '<stop offset="0" stop-color="#fff" stop-opacity=".12"/>' +
        '<stop offset="1" stop-color="#000" stop-opacity=".22"/></linearGradient>' +
      '</defs>';
  }

  /* ==========================================================
     РЕНДЕР КОМНАТЫ
     ========================================================== */

  function itemDef(id) { return A.FURNITURE[id]; }

  function itemArt(it) {
    var d = itemDef(it.id);
    return d.draw(it.color || d.tint || null);
  }

  /** Экранная рамка предмета: {x,y,w,h} в координатах вьюбокса. */
  function itemBox(it) {
    var d = itemDef(it.id);
    var s = it.scale || 1;
    if (d.cat === 'wall') {
      var pw = d.w * ROOM.back * s, ph = d.h * ROOM.back * s;
      var cx = ROOM.xAt(it.x, 0), cy = (it.wy || 0.4) * ROOM.wallY;
      return { x: cx - pw / 2, y: cy - ph / 2, w: pw, h: ph, px: ROOM.back * s };
    }
    var k = ROOM.pxAt(it.fy) * s;
    if (d.cat === 'rug') {
      var rw = d.w * k, rh = d.h * k * 0.26;   /* лежит на полу — сильное сжатие по высоте */
      return { x: ROOM.xAt(it.x, it.fy) - rw / 2, y: ROOM.yAt(it.fy) - rh, w: rw, h: rh, px: k, flat: true };
    }
    var w = d.w * k, h = d.h * k;
    return { x: ROOM.xAt(it.x, it.fy) - w / 2, y: ROOM.yAt(it.fy) - h, w: w, h: h, px: k };
  }

  function drawItem(it, selected) {
    var d = itemDef(it.id);
    var b = itemBox(it);
    var out = '';

    /* контактная тень — предмет должен «стоять»; ковёр лежит, ему тень не нужна */
    if (d.cat === 'floor') {
      var sw = b.w * 0.52, sy = b.y + b.h;
      out += '<ellipse cx="' + (b.x + b.w / 2).toFixed(1) + '" cy="' + sy.toFixed(1) +
        '" rx="' + sw.toFixed(1) + '" ry="' + Math.max(3, b.w * 0.055).toFixed(1) +
        '" fill="#000" opacity=".15"/>';
    } else if (d.cat === 'wall') {
      out += '<rect x="' + (b.x + b.w * 0.06).toFixed(1) + '" y="' + (b.y + b.h * 0.06).toFixed(1) +
        '" width="' + b.w.toFixed(1) + '" height="' + b.h.toFixed(1) + '" fill="#000" opacity=".10"/>';
    }

    var sx = it.flip ? -1 : 1;
    var scaleY = b.flat ? (b.h / d.h) : (b.w / d.w);
    var tx = b.x + (it.flip ? b.w : 0);
    out += '<g class="obj' + (selected ? ' is-selected' : '') + '" data-uid="' + it.uid + '"' +
      ' transform="translate(' + tx.toFixed(2) + ' ' + b.y.toFixed(2) + ') scale(' +
      (sx * b.w / d.w).toFixed(4) + ' ' + scaleY.toFixed(4) + ')">' +
      itemArt(it) + '</g>';

    if (selected) {
      var pad = 7;
      out += '<rect class="sel-ring" pointer-events="none" x="' + (b.x - pad).toFixed(1) + '" y="' + (b.y - pad).toFixed(1) +
        '" width="' + (b.w + pad * 2).toFixed(1) + '" height="' + (b.h + pad * 2).toFixed(1) + '" rx="10"/>';
    }
    return out;
  }

  function glowFor(it, p) {
    var d = itemDef(it.id);
    if (!d.glow) return '';
    var b = itemBox(it);
    var k = b.w / d.w;
    var gx = b.x + d.glow.x * k * (it.flip ? -1 : 1) + (it.flip ? b.w : 0);
    var gy = b.y + d.glow.y * (b.flat ? b.h / d.h : k);
    var r = d.glow.r * k;
    return '<ellipse cx="' + gx.toFixed(1) + '" cy="' + gy.toFixed(1) + '" rx="' + r.toFixed(1) +
      '" ry="' + r.toFixed(1) + '" fill="url(#' + p + 'lamp)" pointer-events="none"/>';
  }

  function renderRoom(r, opts) {
    opts = opts || {};
    var p = opts.p || ('r' + Math.random().toString(36).slice(2, 7) + '_');
    var wm = mat(A.WALL_MATERIALS, r.wall);
    var fm = mat(A.FLOOR_MATERIALS, r.floor);
    var geo = { W: ROOM.W, H: ROOM.H, wallY: ROOM.wallY, xAt: ROOM.xAt, yAt: ROOM.yAt };

    var out = '<svg viewBox="0 0 ' + ROOM.W + ' ' + ROOM.H + '" preserveAspectRatio="xMidYMid slice">';
    out += defs(p);

    /* стена + плинтус + пол */
    out += A.renderWall(wm, 0, 0, ROOM.W, ROOM.wallY, p);
    out += A.renderFloor(fm, geo, p);
    out += '<rect x="0" y="' + (ROOM.wallY - 11).toFixed(1) + '" width="' + ROOM.W +
      '" height="11" fill="' + A.sh(wm.color, A.lum(wm.color) > 0.5 ? -0.08 : 0.16) + '"/>';
    out += '<rect x="0" y="' + (ROOM.wallY - 11).toFixed(1) + '" width="' + ROOM.W +
      '" height="3" fill="#000" opacity=".10"/>';

    /* порядок: ковры → настенное → напольное по глубине */
    var rugs = [], walls = [], floors = [];
    r.items.forEach(function (it) {
      var d = itemDef(it.id);
      if (!d) return;
      if (d.cat === 'rug') rugs.push(it);
      else if (d.cat === 'wall') walls.push(it);
      else floors.push(it);
    });
    rugs.sort(function (a, b) { return a.fy - b.fy; });
    floors.sort(function (a, b) { return a.fy - b.fy; });

    var sel = opts.sel;
    rugs.concat(walls, floors).forEach(function (it) {
      out += drawItem(it, it.uid === sel);
    });

    /* вечер: приглушаем свет и зажигаем лампы */
    if (r.mood === 'evening') {
      out += '<rect x="0" y="0" width="' + ROOM.W + '" height="' + ROOM.H +
        '" fill="#101A2E" opacity=".46" pointer-events="none"/>';
      r.items.forEach(function (it) { out += glowFor(it, p); });
      out += '<rect x="0" y="0" width="' + ROOM.W + '" height="' + ROOM.H +
        '" fill="#FFC96B" opacity=".07" pointer-events="none"/>';
    }

    out += '</svg>';
    return out;
  }

  /* ==========================================================
     РЕНДЕР ЭКСТЕРЬЕРА
     ========================================================== */

  function renderExterior(e, opts) {
    opts = opts || {};
    var mini = !!opts.mini;
    var p = opts.p || ('e' + Math.random().toString(36).slice(2, 7) + '_');
    var W = EXT.W, H = EXT.H, G = EXT.ground;
    var t = mat(A.TIMES, e.time);
    var wm = mat(A.EXT_WALL, e.wall);
    var rm = mat(A.EXT_ROOF, e.roof);
    var style = A.HOUSE_STYLES.filter(function (s) { return s.id === e.style; })[0] || A.HOUSE_STYLES[0];
    var lawn = LAWNS[e.lawn || 0];
    var pathM = PATHS.filter(function (x) { return x.id === e.path; })[0] || PATHS[0];
    var night = e.time === 'night';

    var out = '<svg viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="xMidYMid slice">';
    out += defs(p);
    out += '<defs><linearGradient id="' + p + 'sky" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0" stop-color="' + t.sky[0] + '"/>' +
      '<stop offset="1" stop-color="' + t.sky[1] + '"/></linearGradient>' +
      '<radialGradient id="' + p + 'sun" cx="0.5" cy="0.5" r="0.5">' +
      '<stop offset="0" stop-color="' + t.sun + '" stop-opacity=".95"/>' +
      '<stop offset=".4" stop-color="' + t.sun + '" stop-opacity=".35"/>' +
      '<stop offset="1" stop-color="' + t.sun + '" stop-opacity="0"/></radialGradient>' +
      '<linearGradient id="' + p + 'lawn" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0" stop-color="' + A.sh(lawn, -0.22) + '"/>' +
      '<stop offset=".35" stop-color="' + lawn + '"/>' +
      '<stop offset="1" stop-color="' + A.sh(lawn, 0.12) + '"/></linearGradient></defs>';

    /* стили окон и двери */
    out += '<style>' +
      '.glass{fill:' + t.glass + '}' +
      '.frame{fill:' + e.frame + '}' +
      '.frameLine{stroke:' + e.frame + ';stroke-width:4}' +
      '.frameStroke{color:' + e.frame + '}' +
      '.door{fill:' + e.door + '}' +
      '.doorPanel{fill:' + A.sh(e.door, A.lum(e.door) > 0.5 ? -0.1 : 0.14) + '}' +
      '</style>';

    /* --- небо --- */
    out += '<rect x="0" y="0" width="' + W + '" height="' + G + '" fill="url(#' + p + 'sky)"/>';
    if (night && !mini) {
      for (var s = 0; s < 34; s++) {
        var sx = (s * 173) % W, sy = (s * 97) % (G - 120);
        out += '<circle cx="' + sx + '" cy="' + sy + '" r="' + (s % 3 === 0 ? 1.8 : 1.1) +
          '" fill="#fff" opacity="' + (0.35 + (s % 5) * 0.12) + '"/>';
      }
    }
    var sunX = night ? 178 : (e.time === 'sunset' ? 812 : 806);
    var sunY = night ? 96 : (e.time === 'sunset' ? 300 : 106);
    out += '<circle cx="' + sunX + '" cy="' + sunY + '" r="120" fill="url(#' + p + 'sun)"/>';
    if (night) {
      out += '<circle cx="' + sunX + '" cy="' + sunY + '" r="34" fill="#E8EEF8"/>';
      out += '<circle cx="' + (sunX - 13) + '" cy="' + (sunY - 9) + '" r="30" fill="' + t.sky[0] + '"/>';
    } else {
      out += '<circle cx="' + sunX + '" cy="' + sunY + '" r="' + (e.time === 'sunset' ? 46 : 34) +
        '" fill="' + t.sun + '"/>';
    }
    if (!mini && !night) {
      out += '<g fill="#FFFFFF" opacity="' + (e.time === 'sunset' ? 0.55 : 0.8) + '">' +
        '<ellipse cx="196" cy="118" rx="62" ry="24"/><ellipse cx="246" cy="106" rx="46" ry="27"/>' +
        '<ellipse cx="150" cy="126" rx="40" ry="18"/>' +
        '<ellipse cx="614" cy="72" rx="48" ry="18"/><ellipse cx="652" cy="64" rx="34" ry="20"/>' +
        '</g>';
    }

    /* --- дальний лес --- */
    var forest = '';
    for (var i = 0; i < 26; i++) {
      var fx = i * 42 - 10;
      var fh = 46 + ((i * 37) % 40);
      forest += '<path d="M' + fx + ' ' + G + ' L' + (fx + 21) + ' ' + (G - fh) + ' L' + (fx + 42) + ' ' + G + ' Z"/>';
    }
    out += '<g fill="' + A.sh(night ? '#1B2E3A' : '#4C6B4F', night ? 0 : -0.28) + '" opacity=".9">' + forest + '</g>';
    out += '<rect x="0" y="' + (G - 4) + '" width="' + W + '" height="8" fill="' + A.sh(lawn, -0.3) + '"/>';

    /* --- газон --- */
    out += '<rect x="0" y="' + G + '" width="' + W + '" height="' + (H - G) + '" fill="url(#' + p + 'lawn)"/>';
    if (!mini) {
      out += '<g fill="#000" opacity=".05">';
      var yy = G, band = 12;
      while (yy < H) {
        out += '<rect x="0" y="' + yy.toFixed(1) + '" width="' + W + '" height="' + (band / 2).toFixed(1) + '"/>';
        yy += band; band *= 1.22;
      }
      out += '</g>';
    }

    /* --- дом --- */
    var hs = EXT.houseScale, hw = 460 * hs;
    var hx = (W - hw) / 2, hy = EXT.houseBase - 300 * hs;
    out += '<g transform="translate(' + hx.toFixed(1) + ' ' + hy.toFixed(1) + ') scale(' + hs + ')">';
    out += style.draw(wm, rm, p);
    out += '</g>';
    /* тень дома на газоне */
    out += '<ellipse cx="' + (W / 2 + 30) + '" cy="' + (EXT.houseBase + 4) + '" rx="' + (hw * 0.46) +
      '" ry="16" fill="#000" opacity=".16"/>';

    /* --- дорожка от двери --- */
    var px0 = W / 2, doorW = 60;
    out += '<polygon points="' + (px0 - doorW / 2) + ',' + EXT.houseBase + ' ' + (px0 + doorW / 2) + ',' + EXT.houseBase +
      ' ' + (px0 + doorW * 1.9) + ',' + H + ' ' + (px0 - doorW * 1.9) + ',' + H +
      '" fill="' + pathM.colors[0] + '"/>';
    if (!mini) {
      var rowY = EXT.houseBase, gap = 9;
      out += '<g stroke="' + pathM.colors[1] + '" stroke-width="2.4">';
      while (rowY < H) {
        var f = (rowY - EXT.houseBase) / (H - EXT.houseBase);
        var halfW = doorW / 2 + (doorW * 1.9 - doorW / 2) * f;
        out += '<line x1="' + (px0 - halfW).toFixed(1) + '" y1="' + rowY.toFixed(1) +
          '" x2="' + (px0 + halfW).toFixed(1) + '" y2="' + rowY.toFixed(1) + '"/>';
        rowY += gap; gap *= 1.24;
      }
      if (e.path === 'deck') {
        out += '<line x1="' + px0 + '" y1="' + EXT.houseBase + '" x2="' + px0 + '" y2="' + H + '"/>';
      }
      out += '</g>';
    }

    /* --- озеленение --- */
    var n = e.trees || 0;
    var slots = [[92, 0.98], [908, 1.05], [196, 0.74], [812, 0.8], [40, 0.62]];
    for (var k = 0; k < n && k < slots.length; k++) {
      var sp = slots[k];
      var gy = EXT.houseBase + (k >= 2 ? 26 : 8) + (k === 4 ? 34 : 0);
      out += '<ellipse cx="' + sp[0] + '" cy="' + (gy + 2) + '" rx="' + (34 * sp[1]) + '" ry="9" fill="#000" opacity=".14"/>';
      out += e.conifer
        ? A.treeConifer(sp[0], gy, sp[1], night ? -0.3 : 0)
        : A.treeDeciduous(sp[0], gy, sp[1], night ? -0.3 : 0);
    }
    if (e.bushes) {
      [[318, 0.9], [682, 0.95], [252, 0.7], [748, 0.72]].forEach(function (b) {
        out += A.bush(b[0], EXT.houseBase + 6, b[1]);
      });
    }
    if (e.flowers && !mini) {
      var fl = ['#E4737F', '#F0C64E', '#C77FD0', '#EE9A4B'];
      for (var q = 0; q < 22; q++) {
        var fx2 = 60 + (q * 173) % 880;
        var fy2 = EXT.houseBase + 24 + (q * 61) % 130;
        if (Math.abs(fx2 - W / 2) < 130) continue;
        out += '<circle cx="' + fx2 + '" cy="' + fy2 + '" r="4.4" fill="' + fl[q % 4] + '"/>';
        out += '<circle cx="' + fx2 + '" cy="' + fy2 + '" r="1.6" fill="#FFF3CB"/>';
      }
    }
    if (e.fence) {
      out += '<g>';
      [[-10, 250], [750, 1010]].forEach(function (seg) {
        out += '<rect x="' + seg[0] + '" y="' + (EXT.houseBase - 44) + '" width="' + (seg[1] - seg[0]) +
          '" height="7" rx="3" fill="#8C7355"/>';
        out += '<rect x="' + seg[0] + '" y="' + (EXT.houseBase - 24) + '" width="' + (seg[1] - seg[0]) +
          '" height="7" rx="3" fill="#8C7355"/>';
        for (var fx3 = seg[0] + 6; fx3 < seg[1]; fx3 += 26) {
          out += '<rect x="' + fx3 + '" y="' + (EXT.houseBase - 56) + '" width="9" height="60" rx="3" fill="#9C8262"/>';
        }
      });
      out += '</g>';
    }
    if (e.lights) {
      [[px0 - 118, EXT.houseBase + 40], [px0 + 118, EXT.houseBase + 40],
       [px0 - 168, EXT.houseBase + 108], [px0 + 168, EXT.houseBase + 108]].forEach(function (L) {
        out += '<rect x="' + (L[0] - 2.5) + '" y="' + (L[1] - 26) + '" width="5" height="26" fill="#4A4E52"/>';
        out += '<path d="M' + (L[0] - 9) + ' ' + (L[1] - 26) + ' h18 l-4 -10 h-10 z" fill="#5B6165"/>';
        if (night) {
          out += '<ellipse cx="' + L[0] + '" cy="' + (L[1] + 6) + '" rx="46" ry="18" fill="url(#' + p + 'lamp)"/>';
        }
      });
    }

    /* --- свет из окон и общий тон времени суток --- */
    if (night && style.lights) {
      style.lights.forEach(function (L) {
        out += '<ellipse cx="' + (hx + L[0] * hs).toFixed(1) + '" cy="' + (hy + L[1] * hs).toFixed(1) +
          '" rx="' + (L[2] * hs).toFixed(1) + '" ry="' + (L[2] * hs * 0.8).toFixed(1) +
          '" fill="url(#' + p + 'lamp)" pointer-events="none"/>';
      });
    }
    if (t.amb !== 'rgba(0,0,0,0)') {
      out += '<rect x="0" y="0" width="' + W + '" height="' + H + '" fill="' + t.amb + '" pointer-events="none"/>';
    }

    out += '</svg>';
    return out;
  }

  /* ==========================================================
     ЭКРАНЫ
     ========================================================== */

  function show(id) {
    var list = document.querySelectorAll('.screen');
    for (var i = 0; i < list.length; i++) list[i].classList.remove('active');
    $(id).classList.add('active');
    var panels = document.querySelectorAll('.panel, .house-list, .room-grid, .summary');
    for (var j = 0; j < panels.length; j++) panels[j].scrollTop = 0;
  }

  function countItems(h) {
    var n = 0;
    for (var k in h.rooms) if (h.rooms.hasOwnProperty(k)) n += h.rooms[k].items.length;
    return n;
  }

  function plural(n, one, few, many) {
    var a = Math.abs(n) % 100, b = a % 10;
    if (a > 10 && a < 20) return many;
    if (b > 1 && b < 5) return few;
    if (b === 1) return one;
    return many;
  }

  /* ---------------------------------------------------------- главная */

  function renderHome() {
    var wrap = $('house-list');
    if (!state.houses.length) {
      wrap.innerHTML = '<div class="empty"><strong>Пока пусто</strong>' +
        'Создай первый проект — выбери форму дома, материалы и обставь комнаты.</div>';
      return;
    }
    var list = state.houses.slice().sort(function (a, b) { return b.created - a.created; });
    var html = '';
    list.forEach(function (h) {
      var n = countItems(h);
      html += '<div class="house-card">' +
        '<button class="house-thumb" data-open="' + h.id + '" aria-label="Открыть ' + esc(h.name) + '"></button>' +
        '<button class="house-meta" data-open="' + h.id + '">' +
          '<span class="house-name">' + esc(h.name) + '</span>' +
          '<span class="house-facts"><span>' + fmtDate(h.created) + '</span><span>' +
            n + ' ' + plural(n, 'предмет', 'предмета', 'предметов') + '</span></span>' +
        '</button>' +
        '<span class="house-actions">' +
          '<button class="iconbtn" data-view="' + h.id + '" aria-label="Посмотреть">' + A.icon('eye') + '</button>' +
          '<button class="iconbtn danger" data-del="' + h.id + '" aria-label="Удалить">' + A.icon('trash') + '</button>' +
        '</span>' +
      '</div>';
    });
    wrap.innerHTML = html;
    var thumbs = wrap.querySelectorAll('.house-thumb');
    for (var i = 0; i < thumbs.length; i++) {
      var h = findHouse(thumbs[i].dataset.open);
      if (h) thumbs[i].innerHTML = renderExterior(h.ext, { mini: true, p: 't' + i + '_' });
    }
  }

  function esc(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
  function fmtDate(ts) {
    var d = new Date(ts);
    return String(d.getDate()).padStart(2, '0') + '.' + String(d.getMonth() + 1).padStart(2, '0') + '.' + d.getFullYear();
  }

  /* ---------------------------------------------------------- экстерьер */

  var EXT_TABS = [
    { id: 'style', label: 'Дом' },
    { id: 'wall',  label: 'Фасад' },
    { id: 'roof',  label: 'Крыша' },
    { id: 'door',  label: 'Дверь' },
    { id: 'yard',  label: 'Участок' }
  ];

  function swatchArt(inner, w, h) {
    return '<svg class="swatch-art" viewBox="0 0 ' + w + ' ' + h + '" preserveAspectRatio="none">' + inner + '</svg>';
  }

  function renderExt() {
    var h = house(); if (!h) return;
    var e = h.ext;
    $('ext-title').textContent = h.name;
    $('ext-stage').innerHTML = renderExterior(e, { p: 'ex_' });
    $('btn-time').innerHTML = A.icon(e.time === 'night' ? 'moon' : 'sun');

    $('ext-tabs').innerHTML = EXT_TABS.map(function (t) {
      return '<button class="seg" role="tab" data-tab="' + t.id + '" aria-selected="' +
        (state.extTab === t.id) + '">' + t.label + '</button>';
    }).join('');

    var out = '';
    if (state.extTab === 'style') {
      out += '<div class="panel-label">Форма дома</div><div class="catalog">';
      A.HOUSE_STYLES.forEach(function (s) {
        var prev = '<svg viewBox="60 20 340 290" preserveAspectRatio="xMidYMax meet">' +
          defs('sp' + s.id + '_') +
          '<style>.glass{fill:#BBD8E8}.frame{fill:#EFEDE7}.frameLine{stroke:#EFEDE7;stroke-width:4}' +
          '.frameStroke{color:#EFEDE7}.door{fill:' + e.door + '}.doorPanel{fill:' + A.sh(e.door, 0.12) + '}</style>' +
          s.draw(mat(A.EXT_WALL, e.wall), mat(A.EXT_ROOF, e.roof), 'sp' + s.id + '_') + '</svg>';
        out += '<button class="cat-item" data-style="' + s.id + '"' +
          (e.style === s.id ? ' style="border-color:var(--accent)"' : '') + '>' +
          prev + '<span class="cat-name">' + s.label + '</span></button>';
      });
      out += '</div>';
    } else if (state.extTab === 'wall') {
      out += '<div class="panel-label">Материал фасада</div><div class="swatches">';
      A.EXT_WALL.forEach(function (m) {
        out += '<button class="swatch" data-extwall="' + m.id + '" aria-pressed="' + (e.wall === m.id) + '">' +
          swatchArt(defs('sw' + m.id + '_') + A.facade(m, 0, 0, 100, 80, 'sw' + m.id + '_'), 100, 80) +
          '<span class="swatch-name">' + m.label + '</span></button>';
      });
      out += '</div>';
      out += '<div class="panel-label">Цвет рам</div><div class="swatches">';
      ['#EFEDE7', '#D6D2C8', '#2F3336', '#5B4A3C', '#3A5573', '#2E6A57'].forEach(function (c) {
        out += '<button class="swatch" data-frame="' + c + '" aria-pressed="' + (e.frame === c) + '">' +
          swatchArt('<rect width="100" height="80" fill="' + c + '"/>', 100, 80) +
          '<span class="swatch-name">Рама</span></button>';
      });
      out += '</div>';
    } else if (state.extTab === 'roof') {
      out += '<div class="panel-label">Кровля</div><div class="swatches">';
      A.EXT_ROOF.forEach(function (m) {
        out += '<button class="swatch" data-extroof="' + m.id + '" aria-pressed="' + (e.roof === m.id) + '">' +
          swatchArt(defs('sr' + m.id + '_') + A.roofTex(m, '0,0 100,0 100,80 0,80', 'sr' + m.id + '_', 'q'), 100, 80) +
          '<span class="swatch-name">' + m.label + '</span></button>';
      });
      out += '</div>';
    } else if (state.extTab === 'door') {
      out += '<div class="panel-label">Входная дверь</div><div class="swatches">';
      DOOR_COLORS.forEach(function (c, i) {
        out += '<button class="swatch" data-door="' + c + '" aria-pressed="' + (e.door === c) + '">' +
          swatchArt('<rect width="100" height="80" fill="' + A.sh(c, 0.06) + '"/>' +
            '<rect x="14" y="8" width="72" height="72" rx="3" fill="' + c + '"/>' +
            '<rect x="24" y="16" width="52" height="26" rx="2" fill="' + A.sh(c, A.lum(c) > 0.5 ? -0.1 : 0.16) + '"/>' +
            '<rect x="24" y="48" width="52" height="24" rx="2" fill="' + A.sh(c, A.lum(c) > 0.5 ? -0.1 : 0.16) + '"/>' +
            '<circle cx="74" cy="52" r="3.4" fill="#D7B25E"/>', 100, 80) +
          '<span class="swatch-name">Цвет ' + (i + 1) + '</span></button>';
      });
      out += '</div>';
    } else if (state.extTab === 'yard') {
      out += '<div class="panel-label">Газон</div><div class="swatches">';
      LAWNS.forEach(function (c, i) {
        out += '<button class="swatch" data-lawn="' + i + '" aria-pressed="' + (e.lawn === i) + '">' +
          swatchArt('<rect width="100" height="80" fill="' + c + '"/>' +
            '<rect y="20" width="100" height="10" fill="#000" opacity=".05"/>' +
            '<rect y="46" width="100" height="12" fill="#000" opacity=".05"/>', 100, 80) +
          '<span class="swatch-name">Трава</span></button>';
      });
      out += '</div>';
      out += '<div class="panel-label">Дорожка</div><div class="swatches">';
      PATHS.forEach(function (m) {
        out += '<button class="swatch" data-path="' + m.id + '" aria-pressed="' + (e.path === m.id) + '">' +
          swatchArt('<rect width="100" height="80" fill="' + m.colors[0] + '"/>' +
            '<g stroke="' + m.colors[1] + '" stroke-width="3">' +
            '<line x1="0" y1="18" x2="100" y2="18"/><line x1="0" y1="40" x2="100" y2="40"/>' +
            '<line x1="0" y1="64" x2="100" y2="64"/></g>', 100, 80) +
          '<span class="swatch-name">' + m.label + '</span></button>';
      });
      out += '</div>';
      out += '<div class="panel-label">Озеленение</div><div class="rows">';
      out += ctlStepper('Деревья', e.trees, 'trees');
      out += ctlSwitch('Хвойные', e.conifer, 'conifer');
      out += ctlSwitch('Кусты', e.bushes, 'bushes');
      out += ctlSwitch('Цветы', e.flowers, 'flowers');
      out += ctlSwitch('Забор', e.fence, 'fence');
      out += ctlSwitch('Садовые фонари', e.lights, 'lights');
      out += '</div>';
    }
    $('ext-panel').innerHTML = out;
  }

  function ctlSwitch(label, on, key) {
    return '<div class="row-ctl"><span class="lbl">' + label + '</span>' +
      '<button class="switch" role="switch" aria-checked="' + !!on + '" data-toggle="' + key + '"></button></div>';
  }
  function ctlStepper(label, val, key) {
    return '<div class="row-ctl"><span class="lbl">' + label + '</span><span class="stepper">' +
      '<button data-step="' + key + '" data-dir="-1" aria-label="Меньше">−</button>' +
      '<span class="val">' + val + '</span>' +
      '<button data-step="' + key + '" data-dir="1" aria-label="Больше">+</button></span></div>';
  }

  /* ---------------------------------------------------------- список комнат */

  function renderRooms() {
    var h = house(); if (!h) return;
    var out = '';
    A.ROOMS.forEach(function (rd, i) {
      var r = h.rooms[rd.id];
      var n = r.items.length;
      out += '<button class="room-tile" data-room="' + rd.id + '">' +
        '<span class="room-tile-art" data-art="' + rd.id + '"></span>' +
        '<span class="room-tile-meta">' +
          '<span class="room-tile-name">' + rd.label + '</span>' +
          '<span class="room-tile-count">' + (n ? n + ' ' + plural(n, 'предмет', 'предмета', 'предметов') : 'пусто') + '</span>' +
        '</span>' +
        '<span class="room-tile-go">' + A.icon('arrowRight') + '</span>' +
      '</button>';
    });
    $('room-grid').innerHTML = out;
    var arts = $('room-grid').querySelectorAll('[data-art]');
    for (var i = 0; i < arts.length; i++) {
      arts[i].innerHTML = renderRoom(h.rooms[arts[i].dataset.art], { p: 'rt' + i + '_' });
    }
  }

  /* ---------------------------------------------------------- редактор комнаты */

  var ROOM_TABS = [
    { id: 'items', label: 'Предметы' },
    { id: 'wall',  label: 'Стены' },
    { id: 'floor', label: 'Пол' }
  ];

  function renderRoomEditor() {
    var h = house(); if (!h) return;
    var rd = roomDef(state.roomId), r = h.rooms[state.roomId];
    $('room-title').textContent = rd.label;
    $('btn-mood').innerHTML = A.icon(r.mood === 'evening' ? 'moon' : 'sun');

    var stage = $('room-stage');
    var toolbar = $('obj-toolbar');
    stage.innerHTML = renderRoom(r, { sel: state.sel, p: 'rm_' });
    stage.appendChild(toolbar);
    bindStage(stage.querySelector('svg'));
    syncToolbar();

    $('room-tabs').innerHTML = ROOM_TABS.map(function (t) {
      return '<button class="seg" role="tab" data-tab="' + t.id + '" aria-selected="' +
        (state.roomTab === t.id) + '">' + t.label + '</button>';
    }).join('');

    var out = '';
    if (state.roomTab === 'items') {
      out += '<div class="panel-label">Нажми, чтобы добавить</div><div class="catalog">';
      rd.items.forEach(function (id) {
        var d = A.FURNITURE[id];
        if (!d) return;
        out += '<button class="cat-item" data-add="' + id + '">' +
          '<svg viewBox="0 0 ' + d.w + ' ' + d.h + '" preserveAspectRatio="xMidYMax meet">' +
          defs('c' + id + '_') + d.draw(d.tint || null) + '</svg>' +
          '<span class="cat-name">' + d.label + '</span></button>';
      });
      out += '</div>';
    } else if (state.roomTab === 'wall') {
      out += '<div class="panel-label">Отделка стен</div><div class="swatches">';
      A.WALL_MATERIALS.forEach(function (m) {
        out += '<button class="swatch" data-wall="' + m.id + '" aria-pressed="' + (r.wall === m.id) + '">' +
          swatchArt(defs('mw' + m.id + '_') + A.renderWall(m, 0, 0, 100, 80, 'mw' + m.id + '_'), 100, 80) +
          '<span class="swatch-name">' + m.label + '</span></button>';
      });
      out += '</div>';
    } else {
      out += '<div class="panel-label">Покрытие пола</div><div class="swatches">';
      A.FLOOR_MATERIALS.forEach(function (m) {
        var g = { W: 100, H: 80, wallY: 0,
          xAt: function (cm, fy) { return 50 + cm * (0.1 + 0.1 * fy); },
          yAt: function (fy) { return fy * 80; } };
        out += '<button class="swatch" data-floor="' + m.id + '" aria-pressed="' + (r.floor === m.id) + '">' +
          swatchArt(defs('mf' + m.id + '_') + A.renderFloor(m, g, 'mf' + m.id + '_'), 100, 80) +
          '<span class="swatch-name">' + m.label + '</span></button>';
      });
      out += '</div>';
    }
    $('room-panel').innerHTML = out;
  }

  function selItem() {
    var r = room();
    if (!r || !state.sel) return null;
    for (var i = 0; i < r.items.length; i++) if (r.items[i].uid === state.sel) return r.items[i];
    return null;
  }

  function syncToolbar() {
    var tb = $('obj-toolbar');
    var it = selItem();
    if (!it) { tb.hidden = true; tb.innerHTML = ''; return; }
    var d = itemDef(it.id);
    var html = '<button data-act="smaller" aria-label="Меньше">' + A.icon('shrink') + '</button>' +
      '<button data-act="bigger" aria-label="Больше">' + A.icon('grow') + '</button>' +
      '<button data-act="flip" aria-label="Отразить">' + A.icon('flip') + '</button>' +
      '<button data-act="dup" aria-label="Дублировать">' + A.icon('copy') + '</button>';
    if (d.cat !== 'wall') {
      html += '<button data-act="front" aria-label="Вперёд">' + A.icon('front') + '</button>';
    }
    html += '<span class="sep"></span>' +
      '<button data-act="del" class="danger" aria-label="Удалить">' + A.icon('trash') + '</button>';
    tb.innerHTML = html;
    tb.hidden = false;
  }

  /* --- перетаскивание --- */

  function svgPt(svg, ev) {
    var m = svg.getScreenCTM();
    if (!m) return { x: 0, y: 0 };
    var pt = svg.createSVGPoint();
    pt.x = ev.clientX; pt.y = ev.clientY;
    var q = pt.matrixTransform(m.inverse());
    return { x: q.x, y: q.y };
  }

  function bindStage(svg) {
    if (!svg) return;
    svg.addEventListener('pointerdown', function (ev) {
      var g = ev.target.closest ? ev.target.closest('.obj') : null;
      var r = room();
      if (!g) {
        if (state.sel) { state.sel = null; renderRoomEditor(); }
        return;
      }
      ev.preventDefault();
      var uidAttr = g.dataset.uid;
      if (state.sel !== uidAttr) { state.sel = uidAttr; tick(600, .035); renderRoomEditor(); }

      var it = selItem(); if (!it) return;
      var d = itemDef(it.id);
      var live = $('room-stage').querySelector('svg');
      var start = svgPt(live, ev);
      var moved = false, grab;

      if (d.cat === 'wall') {
        grab = { x: it.x - ROOM.cmFromX(start.x, 0), wy: (it.wy || .4) - start.y / ROOM.wallY };
      } else {
        var f0 = ROOM.fyFromY(start.y);
        grab = { x: it.x - ROOM.cmFromX(start.x, f0), fy: it.fy - f0 };
      }

      function move(mv) {
        moved = true;
        var p2 = svgPt(live, mv);
        var sc = it.scale || 1;
        if (d.cat === 'wall') {
          var wlim = ROOM.limFor(0, d.w * sc);
          it.x = clamp(ROOM.cmFromX(p2.x, 0) + grab.x, -wlim, wlim);
          var hh = d.h * ROOM.back * sc / 2;
          it.wy = clamp(p2.y / ROOM.wallY + grab.wy, hh / ROOM.wallY, 1 - hh / ROOM.wallY - 0.02);
        } else {
          it.fy = clamp(ROOM.fyFromY(p2.y) + grab.fy, 0, 1);
          var lim = ROOM.limFor(it.fy, d.w * sc);
          it.x = clamp(ROOM.cmFromX(p2.x, it.fy) + grab.x, -lim, lim);
        }
        redrawStage();
      }
      function up() {
        window.removeEventListener('pointermove', move);
        window.removeEventListener('pointerup', up);
        window.removeEventListener('pointercancel', up);
        if (moved) { save(); renderRoomEditor(); }
      }
      window.addEventListener('pointermove', move);
      window.addEventListener('pointerup', up);
      window.addEventListener('pointercancel', up);
    });
  }

  /** Быстрая перерисовка только сцены — без пересборки панели. */
  function redrawStage() {
    var stage = $('room-stage'), tb = $('obj-toolbar');
    var r = room(); if (!r) return;
    stage.innerHTML = renderRoom(r, { sel: state.sel, p: 'rm_' });
    stage.appendChild(tb);
    bindStage(stage.querySelector('svg'));
  }

  /**
   * Ищет самое свободное место для нового предмета: перебирает сетку
   * позиций и берёт ту, что дальше всего от уже стоящих соседей.
   */
  function findSlot(r, d) {
    var same = r.items.filter(function (x) {
      var od = itemDef(x.id);
      return od && od.cat === d.cat;
    });
    var cands = [];
    var xs = [-0.68, -0.34, 0, 0.34, 0.68];
    var ds;
    if (d.cat === 'wall') ds = [0.3, 0.52, 0.16];
    else if (d.cat === 'rug') ds = [0.5, 0.75];
    else if (d.against) ds = [0.03, 0.12];       /* гарнитур, шкаф — к стене */
    else ds = [0.22, 0.46, 0.72, 0.96];
    xs.forEach(function (fx) {
      ds.forEach(function (fd) {
        var lim = ROOM.limFor(d.cat === 'wall' ? 0 : fd, d.w);
        cands.push({ x: clamp(fx * ROOM.HALF_CM, -lim, lim), d: fd });
      });
    });

    var best = cands[0], bestScore = -1;
    cands.forEach(function (c) {
      var worst = 1e9;
      same.forEach(function (o) {
        var od = itemDef(o.id);
        var dx = Math.abs(c.x - o.x) / Math.max(60, (d.w + od.w) / 2);
        var dy = Math.abs(c.d - (d.cat === 'wall' ? (o.wy || 0.4) : o.fy)) * 3.2;
        worst = Math.min(worst, Math.sqrt(dx * dx + dy * dy));
      });
      /* лёгкое предпочтение центру, когда всё свободно */
      var score = worst - Math.abs(c.x) / (ROOM.HALF_CM * 12);
      if (score > bestScore) { bestScore = score; best = c; }
    });
    return best;
  }

  function addItem(id) {
    var r = room(); if (!r) return;
    var d = A.FURNITURE[id];
    var it = { uid: uid(), id: id, scale: 1, flip: false };
    var slot = findSlot(r, d);
    it.x = slot.x;
    if (d.cat === 'wall') it.wy = slot.d;
    else it.fy = slot.d;
    r.items.push(it);
    state.sel = it.uid;
    save();
    tick(760, .05);
    renderRoomEditor();
  }

  /* ---------------------------------------------------------- итог */

  function renderFinal() {
    var h = house(); if (!h) return;
    $('final-title').textContent = h.name;
    var out = '<div class="summary-block">' +
      '<div class="summary-head"><h3>Снаружи</h3><span>' +
      (A.HOUSE_STYLES.filter(function (s) { return s.id === h.ext.style; })[0] || {}).label + '</span></div>' +
      '<div class="summary-art" style="aspect-ratio:16/11" data-ext="1"></div></div>';
    A.ROOMS.forEach(function (rd) {
      var n = h.rooms[rd.id].items.length;
      out += '<div class="summary-block">' +
        '<div class="summary-head"><h3>' + rd.label + '</h3><span>' +
        (n ? n + ' ' + plural(n, 'предмет', 'предмета', 'предметов') : 'пусто') + '</span></div>' +
        '<div class="summary-art" style="aspect-ratio:4/3" data-sroom="' + rd.id + '"></div></div>';
    });
    $('summary').innerHTML = out;
    $('summary').querySelector('[data-ext]').innerHTML = renderExterior(h.ext, { p: 'fx_' });
    var rs = $('summary').querySelectorAll('[data-sroom]');
    for (var i = 0; i < rs.length; i++) {
      rs[i].innerHTML = renderRoom(h.rooms[rs[i].dataset.sroom], { p: 'fr' + i + '_' });
      rs[i].dataset.click = rs[i].dataset.sroom;
    }
  }

  /* ==========================================================
     НАВИГАЦИЯ
     ========================================================== */

  function goHome() { state.houseId = null; state.sel = null; renderHome(); show('s-home'); }
  function goExt() { state.extTab = 'style'; renderExt(); show('s-ext'); }
  function goRooms() { renderRooms(); show('s-rooms'); }
  function goRoom(id) { state.roomId = id; state.roomTab = 'items'; state.sel = null; renderRoomEditor(); show('s-room'); }
  function goFinal() { renderFinal(); show('s-final'); }

  /* ==========================================================
     СОБЫТИЯ
     ========================================================== */

  $('btn-new').innerHTML = A.icon('plus') + '<span>Новый проект</span>';
  $('btn-name-back').innerHTML = A.icon('back');
  $('btn-name-next').innerHTML = '<span>Дальше</span>' + A.icon('arrowRight');
  $('btn-ext-back').innerHTML = A.icon('back');
  $('btn-ext-next').innerHTML = '<span>К комнатам</span>' + A.icon('arrowRight');
  $('btn-rooms-back').innerHTML = A.icon('back');
  $('btn-rooms-done').innerHTML = A.icon('check') + '<span>Готово</span>';
  $('btn-room-back').innerHTML = A.icon('back');
  $('btn-final-back').innerHTML = A.icon('back');
  $('btn-final-edit').innerHTML = A.icon('edit') + '<span>Изменить</span>';
  $('btn-final-home').innerHTML = A.icon('home') + '<span>Мои дома</span>';

  var SUGGEST = ['Дом на холме', 'Лесная студия', 'Дом у моря', 'Городской лофт', 'Дом с террасой'];
  $('name-suggest').innerHTML = SUGGEST.map(function (s) {
    return '<button class="chip" data-suggest="' + s + '">' + s + '</button>';
  }).join('');
  $('name-suggest').addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-suggest]');
    if (!b) return;
    $('name-field').value = b.dataset.suggest;
    tick(560, .03);
  });

  $('btn-new').addEventListener('click', function () {
    tick(700, .05);
    $('name-field').value = '';
    show('s-name');
    setTimeout(function () { $('name-field').focus(); }, 240);
  });

  $('btn-name-back').addEventListener('click', function () { tick(420, .03); goHome(); });

  $('btn-name-next').addEventListener('click', function () {
    var name = $('name-field').value.trim() || 'Дом мечты';
    var h = newHouse(name);
    state.houses.push(h);
    state.houseId = h.id;
    save();
    tick(720, .05);
    goExt();
  });
  $('name-field').addEventListener('keydown', function (ev) {
    if (ev.key === 'Enter') $('btn-name-next').click();
  });

  $('btn-ext-back').addEventListener('click', function () { tick(420, .03); goHome(); });
  $('btn-ext-next').addEventListener('click', function () { tick(700, .05); goRooms(); });

  $('btn-time').addEventListener('click', function () {
    var e = house().ext;
    var order = ['day', 'sunset', 'night'];
    e.time = order[(order.indexOf(e.time) + 1) % 3];
    save(); tick(620, .04); renderExt();
    toast(mat(A.TIMES, e.time).label);
  });

  $('ext-tabs').addEventListener('click', function (ev) {
    var b = ev.target.closest('.seg'); if (!b) return;
    state.extTab = b.dataset.tab; tick(540, .03); renderExt();
  });

  $('ext-panel').addEventListener('click', function (ev) {
    var h = house(); if (!h) return;
    var e = h.ext, b, changed = true;
    if ((b = ev.target.closest('[data-style]'))) e.style = b.dataset.style;
    else if ((b = ev.target.closest('[data-extwall]'))) e.wall = b.dataset.extwall;
    else if ((b = ev.target.closest('[data-extroof]'))) e.roof = b.dataset.extroof;
    else if ((b = ev.target.closest('[data-door]'))) e.door = b.dataset.door;
    else if ((b = ev.target.closest('[data-frame]'))) e.frame = b.dataset.frame;
    else if ((b = ev.target.closest('[data-lawn]'))) e.lawn = +b.dataset.lawn;
    else if ((b = ev.target.closest('[data-path]'))) e.path = b.dataset.path;
    else if ((b = ev.target.closest('[data-toggle]'))) e[b.dataset.toggle] = !e[b.dataset.toggle];
    else if ((b = ev.target.closest('[data-step]'))) {
      e[b.dataset.step] = clamp(e[b.dataset.step] + (+b.dataset.dir), 0, 5);
    } else changed = false;
    if (changed) { save(); tick(600, .035); renderExt(); }
  });

  $('btn-rooms-back').addEventListener('click', function () { tick(420, .03); goExt(); });
  $('btn-rooms-done').addEventListener('click', function () { tick(780, .05); goFinal(); });

  $('room-grid').addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-room]'); if (!b) return;
    tick(620, .04); goRoom(b.dataset.room);
  });

  $('btn-room-back').addEventListener('click', function () { tick(420, .03); goRooms(); });

  $('btn-mood').addEventListener('click', function () {
    var r = room();
    r.mood = r.mood === 'evening' ? 'day' : 'evening';
    save(); tick(600, .04); renderRoomEditor();
    toast(r.mood === 'evening' ? 'Вечер' : 'День');
  });

  $('room-tabs').addEventListener('click', function (ev) {
    var b = ev.target.closest('.seg'); if (!b) return;
    state.roomTab = b.dataset.tab; tick(540, .03); renderRoomEditor();
  });

  $('room-panel').addEventListener('click', function (ev) {
    var r = room(); if (!r) return;
    var b;
    if ((b = ev.target.closest('[data-add]'))) { addItem(b.dataset.add); return; }
    if ((b = ev.target.closest('[data-wall]'))) { r.wall = b.dataset.wall; }
    else if ((b = ev.target.closest('[data-floor]'))) { r.floor = b.dataset.floor; }
    else return;
    save(); tick(600, .035); renderRoomEditor();
  });

  $('obj-toolbar').addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-act]'); if (!b) return;
    var r = room(), it = selItem(); if (!it) return;
    var act = b.dataset.act;
    if (act === 'bigger') it.scale = clamp((it.scale || 1) + 0.12, 0.55, 1.8);
    else if (act === 'smaller') it.scale = clamp((it.scale || 1) - 0.12, 0.55, 1.8);
    else if (act === 'flip') it.flip = !it.flip;
    else if (act === 'front') it.fy = clamp(it.fy + 0.14, 0, 1);
    else if (act === 'dup') {
      var copy = JSON.parse(JSON.stringify(it));
      copy.uid = uid();
      if (itemDef(it.id).cat === 'wall') copy.x = clamp(copy.x + 70, -ROOM.HALF_CM, ROOM.HALF_CM);
      else copy.x = clamp(copy.x + 80, -ROOM.HALF_CM, ROOM.HALF_CM);
      r.items.push(copy);
      state.sel = copy.uid;
    } else if (act === 'del') {
      r.items = r.items.filter(function (x) { return x.uid !== it.uid; });
      state.sel = null;
    }
    save();
    tick(act === 'del' ? 340 : 620, .04);
    renderRoomEditor();
  });

  $('btn-final-back').addEventListener('click', function () { tick(420, .03); goRooms(); });
  $('btn-final-edit').addEventListener('click', function () { tick(560, .04); goRooms(); });
  $('btn-final-home').addEventListener('click', function () {
    tick(720, .05); toast('Проект сохранён'); goHome();
  });

  $('summary').addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-sroom]'); if (!b) return;
    tick(600, .04); goRoom(b.dataset.sroom);
  });

  $('house-list').addEventListener('click', function (ev) {
    var b;
    if ((b = ev.target.closest('[data-del]'))) {
      var h = findHouse(b.dataset.del); if (!h) return;
      ask('Удалить проект?', '«' + h.name + '» исчезнет навсегда.', 'Удалить', function () {
        state.houses = state.houses.filter(function (x) { return x.id !== h.id; });
        save(); tick(340, .04); renderHome(); toast('Проект удалён');
      });
      return;
    }
    if ((b = ev.target.closest('[data-view]'))) {
      state.houseId = b.dataset.view; tick(620, .04); goFinal(); return;
    }
    if ((b = ev.target.closest('[data-open]'))) {
      state.houseId = b.dataset.open; tick(620, .04); goExt();
    }
  });

  $('confirm-yes').addEventListener('click', function () {
    $('confirm').hidden = true;
    if (confirmCb) confirmCb();
    confirmCb = null;
  });
  $('confirm-no').addEventListener('click', function () {
    $('confirm').hidden = true; confirmCb = null;
  });
  $('confirm').addEventListener('click', function (ev) {
    if (ev.target === $('confirm')) { $('confirm').hidden = true; confirmCb = null; }
  });

  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') {
      if (!$('confirm').hidden) { $('confirm').hidden = true; confirmCb = null; }
      else if (state.sel) { state.sel = null; renderRoomEditor(); }
    }
    if ((ev.key === 'Delete' || ev.key === 'Backspace') && state.sel &&
        $('s-room').classList.contains('active') && document.activeElement.tagName !== 'INPUT') {
      ev.preventDefault();
      var r = room();
      r.items = r.items.filter(function (x) { return x.uid !== state.sel; });
      state.sel = null; save(); renderRoomEditor();
    }
  });

  /* ---------------------------------------------------------- старт */
  renderHome();
  show('s-home');
})();
