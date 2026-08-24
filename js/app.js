(function () {
  'use strict';

  /* ============================ DATA ============================ */

  var STORAGE_KEY = 'kidsHouseGame.houses.v1';

  var COLOR_PALETTE = [
    '#FFFFFF', '#F8D7E3', '#FFE8B5', '#FFF6B0', '#D4F5C0',
    '#C3E9FF', '#D9C7F0', '#FF6B6B', '#4ECDC4', '#4D96FF',
    '#FFB84D', '#8B5E3C', '#3A3A3A'
  ];

  var HOUSE_SHAPES = [
    { id: 'cottage', label: 'Домик', emoji: '🏠' },
    { id: 'twostory', label: 'Два этажа', emoji: '🏘️' },
    { id: 'bungalow', label: 'Широкий дом', emoji: '🏡' }
  ];

  var ROOM_TYPES = [
    {
      id: 'living', label: 'Гостиная', emoji: '🛋️',
      furniture: [
        { id: 'sofa', emoji: '🛋️', label: 'Диван' },
        { id: 'chair', emoji: '🪑', label: 'Кресло' },
        { id: 'tv', emoji: '📺', label: 'Телевизор' },
        { id: 'plant', emoji: '🪴', label: 'Растение' },
        { id: 'picture', emoji: '🖼️', label: 'Картина' },
        { id: 'lamp', emoji: '💡', label: 'Лампа' },
        { id: 'books', emoji: '📚', label: 'Книги' },
        { id: 'fish', emoji: '🐠', label: 'Аквариум' }
      ]
    },
    {
      id: 'bedroom', label: 'Спальня', emoji: '🛏️',
      furniture: [
        { id: 'bed', emoji: '🛏️', label: 'Кровать' },
        { id: 'teddy', emoji: '🧸', label: 'Мишка' },
        { id: 'mirror', emoji: '🪞', label: 'Зеркало' },
        { id: 'lamp2', emoji: '💡', label: 'Лампа' },
        { id: 'books2', emoji: '📚', label: 'Книги' },
        { id: 'balloon', emoji: '🎈', label: 'Шарик' },
        { id: 'star', emoji: '🌟', label: 'Ночник' },
        { id: 'plant2', emoji: '🪴', label: 'Растение' }
      ]
    },
    {
      id: 'kitchen', label: 'Кухня', emoji: '🍳',
      furniture: [
        { id: 'table', emoji: '🍽️', label: 'Стол' },
        { id: 'chair2', emoji: '🪑', label: 'Стул' },
        { id: 'cupcake', emoji: '🧁', label: 'Кекс' },
        { id: 'fruit', emoji: '🍎', label: 'Фрукты' },
        { id: 'coffee', emoji: '☕', label: 'Чашка' },
        { id: 'flower', emoji: '🌻', label: 'Цветок' },
        { id: 'kettle', emoji: '🫖', label: 'Чайник' },
        { id: 'basket', emoji: '🧺', label: 'Корзина' }
      ]
    }
  ];

  /* ============================ STATE ============================ */

  var state = {
    houses: loadHouses(),
    currentHouseId: null,
    editingRoomId: null,
    exteriorTab: 'shape',
    roomTab: 'furniture',
    selectedItemUid: null
  };

  function loadHouses() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  }

  function persistHouses() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state.houses));
    } catch (e) { /* storage unavailable, ignore */ }
  }

  function getCurrentHouse() {
    var i;
    for (i = 0; i < state.houses.length; i++) {
      if (state.houses[i].id === state.currentHouseId) return state.houses[i];
    }
    return null;
  }

  function saveCurrent() {
    persistHouses();
  }

  function uid() {
    return Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
  }

  function makeEmptyRoom() {
    return { wallpaper: '#FFF6B0', floor: '#D9C7F0', items: [] };
  }

  function createHouse(name) {
    var house = {
      id: uid(),
      name: name || 'Дом мечты',
      createdAt: Date.now(),
      exterior: {
        shape: 'cottage',
        wall: '#FFE8B5',
        roof: '#8B5E3C',
        door: '#8B5E3C',
        window: '#FFFFFF',
        grass: '#8BC34A',
        trees: 2,
        flowers: true,
        fence: false,
        path: true
      },
      rooms: {
        living: makeEmptyRoom(),
        bedroom: makeEmptyRoom(),
        kitchen: makeEmptyRoom()
      }
    };
    house.rooms.living.wallpaper = '#FFE8B5';
    house.rooms.living.floor = '#8B5E3C';
    house.rooms.bedroom.wallpaper = '#F8D7E3';
    house.rooms.bedroom.floor = '#D9C7F0';
    house.rooms.kitchen.wallpaper = '#D4F5C0';
    house.rooms.kitchen.floor = '#FFF6B0';
    return house;
  }

  /* ============================ SOUND ============================ */

  var audioCtx = null;
  function playPop(freq) {
    try {
      if (!audioCtx) {
        var AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return;
        audioCtx = new AC();
      }
      if (audioCtx.state === 'suspended') audioCtx.resume();
      var osc = audioCtx.createOscillator();
      var gain = audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.value = freq || 660;
      gain.gain.setValueAtTime(0.001, audioCtx.currentTime);
      gain.gain.linearRampToValueAtTime(0.12, audioCtx.currentTime + 0.01);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.18);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.2);
    } catch (e) { /* ignore */ }
  }

  var toastTimer = null;
  function showToast(msg) {
    var t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.classList.remove('show'); }, 1600);
  }

  /* ============================ NAVIGATION ============================ */

  function showScreen(id) {
    var screens = document.querySelectorAll('.screen');
    screens.forEach(function (s) { s.classList.remove('active'); });
    document.getElementById(id).classList.add('active');
    window.scrollTo(0, 0);
  }

  function goHome() {
    state.currentHouseId = null;
    renderHome();
    showScreen('screen-home');
  }

  function goNameScreen() {
    document.getElementById('house-name-input').value = '';
    showScreen('screen-name');
    setTimeout(function () {
      document.getElementById('house-name-input').focus();
    }, 200);
  }

  function goExterior() {
    state.exteriorTab = 'shape';
    renderExteriorEditor();
    showScreen('screen-exterior');
  }

  function goRooms() {
    renderRoomsList();
    showScreen('screen-rooms');
  }

  function goRoomEditor(roomId) {
    state.editingRoomId = roomId;
    state.roomTab = 'furniture';
    state.selectedItemUid = null;
    renderRoomEditor();
    showScreen('screen-room');
  }

  function goFinal() {
    renderFinal();
    showScreen('screen-final');
  }

  /* ============================ EXTERIOR RENDER ============================ */

  function houseShapeSvg(shapeId) {
    if (shapeId === 'twostory') {
      return (
        '<svg viewBox="0 0 300 220">' +
        '<rect class="chimney" x="196" y="30" width="16" height="40"/>' +
        '<polygon class="roof" points="55,72 150,15 245,72"/>' +
        '<rect class="wall" x="70" y="72" width="160" height="138"/>' +
        '<rect class="window-frame" x="90" y="90" width="28" height="28" rx="3"/>' +
        '<rect class="window-glass" x="94" y="94" width="20" height="20" rx="2"/>' +
        '<rect class="window-frame" x="182" y="90" width="28" height="28" rx="3"/>' +
        '<rect class="window-glass" x="186" y="94" width="20" height="20" rx="2"/>' +
        '<rect class="window-frame" x="90" y="132" width="28" height="28" rx="3"/>' +
        '<rect class="window-glass" x="94" y="136" width="20" height="20" rx="2"/>' +
        '<rect class="window-frame" x="182" y="132" width="28" height="28" rx="3"/>' +
        '<rect class="window-glass" x="186" y="136" width="20" height="20" rx="2"/>' +
        '<rect class="door" x="134" y="160" width="32" height="50" rx="4"/>' +
        '<circle class="door-knob" cx="158" cy="187" r="2.5"/>' +
        '</svg>'
      );
    }
    if (shapeId === 'bungalow') {
      return (
        '<svg viewBox="0 0 300 220">' +
        '<rect class="chimney" x="208" y="88" width="14" height="34"/>' +
        '<polygon class="roof" points="42,132 100,86 200,86 258,132"/>' +
        '<rect class="wall" x="55" y="132" width="190" height="78"/>' +
        '<rect class="window-frame" x="78" y="150" width="32" height="30" rx="3"/>' +
        '<rect class="window-glass" x="82" y="154" width="24" height="22" rx="2"/>' +
        '<rect class="window-frame" x="190" y="150" width="32" height="30" rx="3"/>' +
        '<rect class="window-glass" x="194" y="154" width="24" height="22" rx="2"/>' +
        '<rect class="door" x="138" y="160" width="30" height="50" rx="4"/>' +
        '<circle class="door-knob" cx="160" cy="187" r="2.5"/>' +
        '</svg>'
      );
    }
    /* cottage (default) */
    return (
      '<svg viewBox="0 0 300 220">' +
      '<rect class="chimney" x="188" y="72" width="16" height="38"/>' +
      '<polygon class="roof" points="62,120 150,58 238,120"/>' +
      '<rect class="wall" x="75" y="120" width="150" height="90"/>' +
      '<rect class="window-frame" x="95" y="140" width="30" height="30" rx="3"/>' +
      '<rect class="window-glass" x="99" y="144" width="22" height="22" rx="2"/>' +
      '<rect class="window-frame" x="175" y="140" width="30" height="30" rx="3"/>' +
      '<rect class="window-glass" x="179" y="144" width="22" height="22" rx="2"/>' +
      '<rect class="door" x="135" y="160" width="30" height="50" rx="4"/>' +
      '<circle class="door-knob" cx="158" cy="187" r="2.5"/>' +
      '</svg>'
    );
  }

  function renderExteriorInto(container, ext, opts) {
    opts = opts || {};
    var mini = !!opts.mini;
    var yardHtml = '';
    if (!mini) {
      var decor = '';
      var i, leftPositions = [8, 20], rightPositions = [78, 90];
      for (i = 0; i < ext.trees; i++) {
        var pos = i < 2 ? (i === 0 ? 6 : 88) : 46;
        decor += '<span class="yard-emoji" style="left:' + pos + '%; font-size:' + (30 - i * 2) + 'px;">🌳</span>';
      }
      if (ext.flowers) {
        decor += '<span class="yard-emoji" style="left:30%; font-size:16px;">🌸</span>';
        decor += '<span class="yard-emoji" style="left:64%; font-size:16px;">🌼</span>';
      }
      if (ext.fence) {
        decor += '<span class="yard-emoji" style="left:2%; bottom:0; font-size:18px;">🪵</span>';
        decor += '<span class="yard-emoji" style="left:96%; bottom:0; font-size:18px;">🪵</span>';
      }
      yardHtml = '<div class="exterior-yard-decor">' + decor + '</div>';
    }
    var pathHtml = (!mini && ext.path) ? '<div class="exterior-path"></div>' : '';
    var cloudsHtml = mini ? '' :
      '<span class="exterior-cloud" style="top:10px; left:12px;">☁️</span>' +
      '<span class="exterior-cloud" style="top:26px; right:20px;">☁️</span>';

    container.innerHTML =
      '<div class="exterior-render' + (mini ? ' mini' : '') + '" style="' +
        '--wall-color:' + ext.wall + ';' +
        '--roof-color:' + ext.roof + ';' +
        '--door-color:' + ext.door + ';' +
        '--window-color:' + ext.window + ';' +
        '--grass-color:' + ext.grass + ';">' +
        '<div class="exterior-sky"></div>' +
        (mini ? '' : '<span class="exterior-sun">☀️</span>') +
        cloudsHtml +
        '<div class="exterior-svg-wrap">' + houseShapeSvg(ext.shape) + '</div>' +
        '<div class="exterior-ground">' + pathHtml + '</div>' +
        yardHtml +
      '</div>';
  }

  function renderExteriorEditor() {
    var house = getCurrentHouse();
    if (!house) return;
    renderExteriorInto(document.getElementById('exterior-preview'), house.exterior);

    document.querySelectorAll('#exterior-tabs .tab-btn').forEach(function (btn) {
      btn.classList.toggle('active', btn.dataset.tab === state.exteriorTab);
    });

    var panel = document.getElementById('exterior-panel');
    var ext = house.exterior;
    var html = '';

    if (state.exteriorTab === 'shape') {
      html += '<div class="shape-grid">';
      HOUSE_SHAPES.forEach(function (s) {
        html += '<button class="option-card' + (ext.shape === s.id ? ' active' : '') + '" data-shape="' + s.id + '">' +
          '<span class="opt-emoji">' + s.emoji + '</span>' + s.label + '</button>';
      });
      html += '</div>';
    } else if (state.exteriorTab === 'wall' || state.exteriorTab === 'roof' || state.exteriorTab === 'door' || state.exteriorTab === 'window') {
      html += swatchGridHtml(ext[state.exteriorTab], state.exteriorTab);
    } else if (state.exteriorTab === 'yard') {
      html += '<div class="swatch-grid">' + swatchesOnly(ext.grass, 'grass') + '</div>';
      html += '<div class="stepper"><button data-act="tree-minus">−</button>' +
        '<span class="stepper-val">🌳 ' + ext.trees + '</span>' +
        '<button data-act="tree-plus">+</button></div>';
      html += toggleRowHtml('flowers', '🌸 Цветы', ext.flowers);
      html += toggleRowHtml('fence', '🪵 Забор', ext.fence);
      html += toggleRowHtml('path', '🪨 Дорожка', ext.path);
    }
    panel.innerHTML = html;
  }

  function swatchesOnly(current, field) {
    var html = '';
    COLOR_PALETTE.forEach(function (c) {
      html += '<button class="swatch' + (sameColor(c, current) ? ' active' : '') + '" ' +
        'style="background:' + c + '" data-field="' + field + '" data-color="' + c + '"></button>';
    });
    html += '<label class="swatch swatch-custom" title="Свой цвет">🎨' +
      '<input type="color" data-field="' + field + '" data-custom="1" value="' + current + '"></label>';
    return html;
  }

  function swatchGridHtml(current, field) {
    return '<div class="swatch-grid">' + swatchesOnly(current, field) + '</div>';
  }

  function toggleRowHtml(field, label, on) {
    return '<div class="toggle-row"><span>' + label + '</span>' +
      '<button class="switch' + (on ? ' on' : '') + '" data-toggle="' + field + '"></button></div>';
  }

  function sameColor(a, b) {
    return (a || '').toLowerCase() === (b || '').toLowerCase();
  }

  /* ============================ ROOMS LIST ============================ */

  function renderRoomsList() {
    var house = getCurrentHouse();
    if (!house) return;
    var wrap = document.getElementById('room-cards');
    var html = '';
    ROOM_TYPES.forEach(function (rt) {
      var room = house.rooms[rt.id];
      html += '<button class="room-card" data-room="' + rt.id + '">' +
        '<span class="room-card-icon">' + rt.emoji + '</span>' +
        '<span class="room-card-name">' + rt.label + '</span>' +
        '<span class="room-card-count">' + room.items.length + ' 🪑</span>' +
        '</button>';
    });
    wrap.innerHTML = html;
  }

  /* ============================ ROOM EDITOR ============================ */

  function roomTypeById(id) {
    var i;
    for (i = 0; i < ROOM_TYPES.length; i++) {
      if (ROOM_TYPES[i].id === id) return ROOM_TYPES[i];
    }
    return null;
  }

  function renderRoomVisual(container, room, roomType, opts) {
    opts = opts || {};
    var interactive = !!opts.interactive;
    var html = '<div class="room-wall" style="background:' + room.wallpaper + '"></div>' +
      '<div class="room-floor" style="background:' + room.floor + '"></div>';
    room.items.forEach(function (item) {
      var scale = item.scale || 1;
      var flip = item.flip ? -1 : 1;
      html += '<div class="room-item' + (interactive && item.uid === state.selectedItemUid ? ' selected' : '') + '" ' +
        'data-uid="' + item.uid + '" style="left:' + item.x + '%; top:' + item.y + '%; ' +
        'font-size:' + (opts.baseSize || 40) * scale + 'px; ' +
        'transform:translate(-50%,-50%) scaleX(' + flip + ');">' + item.emoji + '</div>';
    });
    container.innerHTML = html;

    if (interactive) {
      container.querySelectorAll('.room-item').forEach(function (el) {
        el.addEventListener('pointerdown', function (ev) {
          onItemPointerDown(ev, el, container);
        });
      });
    }
  }

  function renderRoomEditor() {
    var house = getCurrentHouse();
    if (!house) return;
    var roomId = state.editingRoomId;
    var roomType = roomTypeById(roomId);
    var room = house.rooms[roomId];

    document.getElementById('room-title').textContent = roomType.emoji + ' ' + roomType.label;

    var canvas = document.getElementById('room-canvas');
    renderRoomVisual(canvas, room, roomType, { interactive: true, baseSize: 40 });

    document.getElementById('item-toolbar').hidden = !state.selectedItemUid;

    document.querySelectorAll('#room-tabs .tab-btn').forEach(function (btn) {
      btn.classList.toggle('active', btn.dataset.tab === state.roomTab);
    });

    var panel = document.getElementById('room-panel');
    var html = '';
    if (state.roomTab === 'furniture') {
      html += '<div class="furniture-tray">';
      roomType.furniture.forEach(function (f) {
        html += '<button class="furniture-btn" data-add="' + f.id + '">' +
          '<span class="f-emoji">' + f.emoji + '</span><span class="f-label">' + f.label + '</span></button>';
      });
      html += '</div>';
    } else if (state.roomTab === 'wallpaper') {
      html += swatchGridHtml(room.wallpaper, 'wallpaper');
    } else if (state.roomTab === 'floor') {
      html += swatchGridHtml(room.floor, 'floor');
    }
    panel.innerHTML = html;
  }

  function onItemPointerDown(ev, el, container) {
    ev.preventDefault();
    state.selectedItemUid = el.dataset.uid;
    document.querySelectorAll('.room-item').forEach(function (n) { n.classList.remove('selected'); });
    el.classList.add('selected');
    document.getElementById('item-toolbar').hidden = false;

    var house = getCurrentHouse();
    var room = house.rooms[state.editingRoomId];
    var item = findItem(room, state.selectedItemUid);
    if (!item) return;

    var rect = container.getBoundingClientRect();
    var moved = false;

    function onMove(mv) {
      moved = true;
      var x = ((mv.clientX - rect.left) / rect.width) * 100;
      var y = ((mv.clientY - rect.top) / rect.height) * 100;
      x = Math.max(3, Math.min(97, x));
      y = Math.max(3, Math.min(97, y));
      item.x = x;
      item.y = y;
      el.style.left = x + '%';
      el.style.top = y + '%';
    }
    function onUp() {
      document.removeEventListener('pointermove', onMove);
      document.removeEventListener('pointerup', onUp);
      if (moved) saveCurrent();
    }
    document.addEventListener('pointermove', onMove);
    document.addEventListener('pointerup', onUp);
  }

  function findItem(room, itemUid) {
    var i;
    for (i = 0; i < room.items.length; i++) {
      if (room.items[i].uid === itemUid) return room.items[i];
    }
    return null;
  }

  /* ============================ FINAL SCREEN ============================ */

  function renderFinal() {
    var house = getCurrentHouse();
    if (!house) return;
    document.getElementById('final-title').textContent = '🏡 ' + house.name;
    renderExteriorInto(document.getElementById('final-exterior'), house.exterior);

    var wrap = document.getElementById('final-rooms');
    wrap.innerHTML = '';
    ROOM_TYPES.forEach(function (rt) {
      var block = document.createElement('div');
      block.className = 'final-room-block';
      var label = document.createElement('div');
      label.className = 'final-room-label';
      label.textContent = rt.emoji + ' ' + rt.label;
      block.appendChild(label);
      var canvas = document.createElement('div');
      canvas.className = 'final-room-canvas';
      block.appendChild(canvas);
      canvas.addEventListener('click', function () { goRoomEditor(rt.id); });
      wrap.appendChild(block);
      renderRoomVisual(canvas, house.rooms[rt.id], rt, { interactive: false, baseSize: 24 });
    });
  }

  /* ============================ HOME SCREEN ============================ */

  function formatDate(ts) {
    var d = new Date(ts);
    var dd = String(d.getDate()).padStart(2, '0');
    var mm = String(d.getMonth() + 1).padStart(2, '0');
    return dd + '.' + mm + '.' + d.getFullYear();
  }

  function renderHome() {
    var wrap = document.getElementById('house-list');
    if (!state.houses.length) {
      wrap.innerHTML = '<div class="house-empty">Пока нет домов.<br>Нажми «Новый дом», чтобы построить первый! 🏡✨</div>';
      return;
    }
    var sorted = state.houses.slice().sort(function (a, b) { return b.createdAt - a.createdAt; });
    var html = '';
    sorted.forEach(function (h) {
      html += '<div class="house-card" data-open="' + h.id + '">' +
        '<div class="house-card-thumb" data-thumb="' + h.id + '"></div>' +
        '<div class="house-card-info">' +
          '<div class="house-card-name">' + escapeHtml(h.name) + '</div>' +
          '<div class="house-card-date">' + formatDate(h.createdAt) + '</div>' +
        '</div>' +
        '<div class="house-card-actions">' +
          '<button class="icon-btn" data-view="' + h.id + '" title="Смотреть">👀</button>' +
          '<button class="icon-btn" data-delete="' + h.id + '" title="Удалить">🗑️</button>' +
        '</div>' +
      '</div>';
    });
    wrap.innerHTML = html;
    wrap.querySelectorAll('[data-thumb]').forEach(function (el) {
      var h = findHouse(el.dataset.thumb);
      if (h) renderExteriorInto(el, h.exterior, { mini: true });
    });
  }

  function escapeHtml(s) {
    var div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  function findHouse(id) {
    var i;
    for (i = 0; i < state.houses.length; i++) {
      if (state.houses[i].id === id) return state.houses[i];
    }
    return null;
  }

  /* ============================ EVENTS ============================ */

  document.getElementById('btn-new-house').addEventListener('click', function () {
    playPop(700);
    goNameScreen();
  });

  document.getElementById('btn-name-back').addEventListener('click', function () {
    playPop(440);
    goHome();
  });

  document.getElementById('btn-name-next').addEventListener('click', function () {
    var input = document.getElementById('house-name-input');
    var name = input.value.trim() || 'Дом мечты';
    var house = createHouse(name);
    state.houses.push(house);
    state.currentHouseId = house.id;
    saveCurrent();
    playPop(700);
    goExterior();
  });

  document.getElementById('house-name-input').addEventListener('keydown', function (ev) {
    if (ev.key === 'Enter') document.getElementById('btn-name-next').click();
  });

  document.getElementById('btn-exterior-back').addEventListener('click', function () {
    playPop(440);
    goHome();
  });
  document.getElementById('btn-exterior-next').addEventListener('click', function () {
    playPop(700);
    goRooms();
  });

  document.getElementById('exterior-tabs').addEventListener('click', function (ev) {
    var btn = ev.target.closest('.tab-btn');
    if (!btn) return;
    state.exteriorTab = btn.dataset.tab;
    playPop(520);
    renderExteriorEditor();
  });

  document.getElementById('exterior-panel').addEventListener('click', function (ev) {
    var house = getCurrentHouse();
    if (!house) return;
    var shapeBtn = ev.target.closest('[data-shape]');
    if (shapeBtn) {
      house.exterior.shape = shapeBtn.dataset.shape;
      saveCurrent();
      playPop(600);
      renderExteriorEditor();
      return;
    }
    var swatch = ev.target.closest('[data-field]');
    if (swatch && !swatch.hasAttribute('data-custom')) {
      house.exterior[swatch.dataset.field] = swatch.dataset.color;
      saveCurrent();
      playPop(600);
      renderExteriorEditor();
      return;
    }
    var stepBtn = ev.target.closest('[data-act]');
    if (stepBtn) {
      if (stepBtn.dataset.act === 'tree-plus') house.exterior.trees = Math.min(3, house.exterior.trees + 1);
      if (stepBtn.dataset.act === 'tree-minus') house.exterior.trees = Math.max(0, house.exterior.trees - 1);
      saveCurrent();
      playPop(560);
      renderExteriorEditor();
      return;
    }
    var toggleBtn = ev.target.closest('[data-toggle]');
    if (toggleBtn) {
      var f = toggleBtn.dataset.toggle;
      house.exterior[f] = !house.exterior[f];
      saveCurrent();
      playPop(560);
      renderExteriorEditor();
    }
  });

  document.getElementById('exterior-panel').addEventListener('input', function (ev) {
    var custom = ev.target.closest('[data-custom]');
    if (!custom) return;
    var house = getCurrentHouse();
    if (!house) return;
    house.exterior[custom.dataset.field] = custom.value;
    saveCurrent();
    renderExteriorEditor();
  });

  document.getElementById('btn-rooms-back').addEventListener('click', function () {
    playPop(440);
    goExterior();
  });
  document.getElementById('btn-rooms-done').addEventListener('click', function () {
    playPop(760);
    goFinal();
  });

  document.getElementById('room-cards').addEventListener('click', function (ev) {
    var card = ev.target.closest('[data-room]');
    if (!card) return;
    playPop(600);
    goRoomEditor(card.dataset.room);
  });

  document.getElementById('btn-room-back').addEventListener('click', function () {
    playPop(440);
    goRooms();
  });

  document.getElementById('room-tabs').addEventListener('click', function (ev) {
    var btn = ev.target.closest('.tab-btn');
    if (!btn) return;
    state.roomTab = btn.dataset.tab;
    playPop(520);
    renderRoomEditor();
  });

  document.getElementById('room-panel').addEventListener('click', function (ev) {
    var house = getCurrentHouse();
    if (!house) return;
    var room = house.rooms[state.editingRoomId];

    var addBtn = ev.target.closest('[data-add]');
    if (addBtn) {
      var roomType = roomTypeById(state.editingRoomId);
      var fdef = roomType.furniture.filter(function (f) { return f.id === addBtn.dataset.add; })[0];
      if (fdef) {
        var newItem = {
          uid: uid(),
          itemId: fdef.id,
          emoji: fdef.emoji,
          x: 30 + Math.random() * 40,
          y: 30 + Math.random() * 40,
          scale: 1,
          flip: false
        };
        room.items.push(newItem);
        state.selectedItemUid = newItem.uid;
        saveCurrent();
        playPop(760);
        renderRoomEditor();
      }
      return;
    }

    var swatch = ev.target.closest('[data-field]');
    if (swatch && !swatch.hasAttribute('data-custom')) {
      room[swatch.dataset.field] = swatch.dataset.color;
      saveCurrent();
      playPop(600);
      renderRoomEditor();
    }
  });

  document.getElementById('room-panel').addEventListener('input', function (ev) {
    var custom = ev.target.closest('[data-custom]');
    if (!custom) return;
    var house = getCurrentHouse();
    if (!house) return;
    var room = house.rooms[state.editingRoomId];
    room[custom.dataset.field] = custom.value;
    saveCurrent();
    renderRoomEditor();
  });

  document.getElementById('room-canvas').addEventListener('pointerdown', function (ev) {
    if (ev.target.closest('.room-item')) return;
    state.selectedItemUid = null;
    document.querySelectorAll('.room-item').forEach(function (n) { n.classList.remove('selected'); });
    document.getElementById('item-toolbar').hidden = true;
  });

  document.getElementById('item-toolbar').addEventListener('click', function (ev) {
    var btn = ev.target.closest('[data-act]');
    if (!btn) return;
    var house = getCurrentHouse();
    var room = house.rooms[state.editingRoomId];
    var item = findItem(room, state.selectedItemUid);
    if (!item) return;
    var act = btn.dataset.act;
    if (act === 'bigger') item.scale = Math.min(2.0, (item.scale || 1) + 0.15);
    if (act === 'smaller') item.scale = Math.max(0.5, (item.scale || 1) - 0.15);
    if (act === 'flip') item.flip = !item.flip;
    if (act === 'delete') {
      room.items = room.items.filter(function (i) { return i.uid !== item.uid; });
      state.selectedItemUid = null;
      document.getElementById('item-toolbar').hidden = true;
    }
    saveCurrent();
    playPop(act === 'delete' ? 380 : 600);
    renderRoomEditor();
  });

  document.getElementById('btn-final-edit').addEventListener('click', function () {
    playPop(440);
    goRooms();
  });
  document.getElementById('btn-final-home').addEventListener('click', function () {
    playPop(700);
    showToast('Дом сохранён! 🎉');
    goHome();
  });

  document.getElementById('house-list').addEventListener('click', function (ev) {
    var del = ev.target.closest('[data-delete]');
    if (del) {
      var h = findHouse(del.dataset.delete);
      if (h && window.confirm('Удалить дом «' + h.name + '»?')) {
        state.houses = state.houses.filter(function (x) { return x.id !== h.id; });
        saveCurrent();
        playPop(380);
        renderHome();
      }
      return;
    }
    var view = ev.target.closest('[data-view]');
    if (view) {
      state.currentHouseId = view.dataset.view;
      playPop(600);
      goFinal();
      return;
    }
    var open = ev.target.closest('[data-open]');
    if (open) {
      state.currentHouseId = open.dataset.open;
      playPop(600);
      goExterior();
    }
  });

  /* ============================ INIT ============================ */

  renderHome();
  showScreen('screen-home');
})();
