/* The Word Became Compute — shared site behaviour
   (display prefs, place-saving, infobox toggles, reading progress,
    helpers for the interactive panels) */
(function () {
  'use strict';

  var LS = {
    get: function (k, fb) {
      try { var v = localStorage.getItem(k); return v === null ? fb : JSON.parse(v); }
      catch (e) { return fb; }
    },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} },
    del: function (k) { try { localStorage.removeItem(k); } catch (e) {} },
    keys: function () { try { return Object.keys(localStorage); } catch (e) { return []; } }
  };

  var FONTS = {
    'Literata':          { g: 'Literata:ital,opsz,wght@0,7..72,400..700;1,7..72,400..700', kind: 'serif' },
    'Gentium Book Plus': { g: 'Gentium+Book+Plus:ital,wght@0,400;0,700;1,400;1,700', kind: 'serif' },
    'Source Serif 4':    { g: 'Source+Serif+4:ital,opsz,wght@0,8..60,400..700;1,8..60,400..700', kind: 'serif' },
    'Figtree':           { g: 'Figtree:ital,wght@0,400..700;1,400..700', kind: 'sans-serif' },
    'Inter':             { g: 'Inter:ital,opsz,wght@0,14..32,400..700;1,14..32,400..700', kind: 'sans-serif' },
    'Lato':              { g: 'Lato:ital,wght@0,400;0,700;1,400;1,700', kind: 'sans-serif' },
    'Lexend':            { g: 'Lexend:wght@400..700', kind: 'sans-serif' },
    'Manrope':           { g: 'Manrope:wght@400..700', kind: 'sans-serif' },
    'Palatino':          { local: true, kind: 'serif' },
    'Atkinson Hyperlegible': { g: 'Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400;1,700', kind: 'sans-serif' }
  };
  var SIZES = [15, 16, 17, 18, 19, 20, 21, 22, 23];

  var prefs = {
    theme: LS.get('twbc.theme', 'standard'),
    font:  LS.get('twbc.font', 'Palatino'),
    size:  LS.get('twbc.size', 18),
    hideInteractive: LS.get('twbc.hideInteractive', false),
    hideTimeline: LS.get('twbc.hideTimeline', false)
  };
  if (!FONTS[prefs.font]) prefs.font = 'Literata';
  if (SIZES.indexOf(prefs.size) < 0) prefs.size = 18;

  var loadedFonts = { 'Literata': true, 'Figtree': true };
  function loadFont(name) {
    if (loadedFonts[name] || !FONTS[name] || FONTS[name].local) return;
    loadedFonts[name] = true;
    var l = document.createElement('link');
    l.rel = 'stylesheet';
    l.href = 'https://fonts.googleapis.com/css2?family=' + FONTS[name].g + '&display=swap';
    document.head.appendChild(l);
  }

  function repaint() {
    window.dispatchEvent(new CustomEvent('twbc:repaint'));
  }

  function applyPrefs() {
    var de = document.documentElement;
    de.setAttribute('data-theme', prefs.theme);
    de.classList.toggle('hide-interactives', !!prefs.hideInteractive);
    de.classList.toggle('hide-timeline', !!prefs.hideTimeline);
    loadFont(prefs.font);
    de.style.setProperty('--font-body',
      '"' + prefs.font + '", ' + (FONTS[prefs.font].kind === 'serif' ? 'Georgia, serif' : 'system-ui, sans-serif'));
    de.style.fontSize = prefs.size + 'px';
    LS.set('twbc.theme', prefs.theme);
    LS.set('twbc.font', prefs.font);
    LS.set('twbc.size', prefs.size);
    LS.set('twbc.hideInteractive', !!prefs.hideInteractive);
    LS.set('twbc.hideTimeline', !!prefs.hideTimeline);
    setTimeout(repaint, 60);
    setTimeout(repaint, 420);
  }
  applyPrefs();

  /* ---------- helpers exposed to interactive panels ---------- */
  window.TWBC = {
    cssVar: function (name, el) {
      return getComputedStyle(el || document.documentElement).getPropertyValue(name).trim();
    },
    fitCanvas: function (cv) {
      var r = cv.getBoundingClientRect(), d = window.devicePixelRatio || 1;
      cv.width = Math.max(1, Math.round(r.width * d));
      cv.height = Math.max(1, Math.round(r.height * d));
      var ctx = cv.getContext('2d');
      ctx.setTransform(d, 0, 0, d, 0, 0);
      return ctx;
    },
    onRepaint: function (fn) {
      window.addEventListener('twbc:repaint', fn);
      window.addEventListener('resize', fn);
    },
    fmt: function (x) {
      x = Math.round(x);
      if (x >= 1e9) return (x / 1e9).toFixed(1) + 'B';
      if (x >= 1e6) return (x / 1e6).toFixed(1) + 'M';
      if (x >= 1e3) return (x / 1e3).toFixed(0) + 'k';
      return x.toLocaleString('en-GB');
    }
  };

  document.addEventListener('DOMContentLoaded', function () {

    /* ---------- display controls ---------- */
    var btn = document.getElementById('ctl-btn');
    var pop = document.getElementById('ctl-pop');
    if (btn && pop) {
      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        var open = !pop.hidden;
        pop.hidden = open;
        btn.setAttribute('aria-expanded', String(!open));
      });
      document.addEventListener('click', function (e) {
        if (!pop.hidden && !pop.contains(e.target)) {
          pop.hidden = true; btn.setAttribute('aria-expanded', 'false');
        }
      });
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && !pop.hidden) {
          pop.hidden = true; btn.setAttribute('aria-expanded', 'false');
        }
      });

      var sel = document.getElementById('font-sel');
      if (sel) {
        sel.value = prefs.font;
        sel.addEventListener('change', function () {
          prefs.font = sel.value; applyPrefs();
        });
      }
      var minus = document.getElementById('size-minus');
      var plus = document.getElementById('size-plus');
      var val = document.getElementById('size-val');
      function showSize() { if (val) val.textContent = prefs.size + 'px'; }
      showSize();
      function step(d) {
        var i = SIZES.indexOf(prefs.size) + d;
        if (i < 0 || i >= SIZES.length) return;
        prefs.size = SIZES[i]; applyPrefs(); showSize();
      }
      if (minus) minus.addEventListener('click', function () { step(-1); });
      if (plus) plus.addEventListener('click', function () { step(1); });

      var hideIx = document.getElementById('hide-ix-toggle');
      if (hideIx) {
        hideIx.checked = !!prefs.hideInteractive;
        hideIx.addEventListener('change', function () {
          prefs.hideInteractive = !!hideIx.checked;
          applyPrefs();
        });
      }
      var hideTl = document.getElementById('hide-tl-toggle');
      if (hideTl) {
        hideTl.checked = !!prefs.hideTimeline;
        hideTl.addEventListener('change', function () {
          prefs.hideTimeline = !!hideTl.checked;
          applyPrefs();
        });
      }

      var segs = pop.querySelectorAll('.theme-seg button');
      function paintSeg() {
        segs.forEach(function (b) {
          b.setAttribute('aria-pressed', String(b.dataset.theme === prefs.theme));
        });
      }
      segs.forEach(function (b) {
        b.addEventListener('click', function () {
          prefs.theme = b.dataset.theme; applyPrefs(); paintSeg();
        });
      });
      paintSeg();
    }

    /* ---------- infoboxes: redraw canvases when opened ---------- */
    document.querySelectorAll('details.infobox').forEach(function (d) {
      d.addEventListener('toggle', function () { if (d.open) repaint(); });
    });

    /* ---------- reading progress + place saving ---------- */
    var slug = document.body.getAttribute('data-slug');
    var bar = document.getElementById('progress');
    function docRange() {
      return Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
    }
    var saveT = null;
    function onScroll() {
      var r = window.scrollY / docRange();
      if (bar) bar.style.width = (Math.min(1, Math.max(0, r)) * 100) + '%';
      if (slug && slug !== 'index' && slug !== 'research') {
        clearTimeout(saveT);
        saveT = setTimeout(function () {
          LS.set('twbc.pos.' + slug, { r: r, t: Date.now() });
          LS.set('twbc.last', slug);
        }, 250);
      }
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();

    // restore position on part pages
    if (slug && slug !== 'index' && slug !== 'research' && !location.hash) {
      var pos = LS.get('twbc.pos.' + slug, null);
      if (pos && pos.r > 0.03 && pos.r < 0.97) {
        if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
        requestAnimationFrame(function () {
          window.scrollTo(0, pos.r * docRange());
          var pill = document.getElementById('resume-pill');
          if (pill) {
            pill.classList.add('show');
            var top = pill.querySelector('button');
            if (top) top.addEventListener('click', function () {
              window.scrollTo({ top: 0, behavior: 'smooth' });
              pill.classList.remove('show');
            });
            setTimeout(function () { pill.classList.remove('show'); }, 6000);
          }
        });
      }
    }

    // index page: continue / start-over CTAs + per-part progress
    if (slug === 'index') {
      var last = LS.get('twbc.last', null);
      var lastPos = last ? LS.get('twbc.pos.' + last, null) : null;
      var started = !!(lastPos && lastPos.r > 0.03);
      var begin = document.getElementById('cta-begin');
      var cont = document.getElementById('continue-btn');
      if (started && cont && begin) {
        var card = document.querySelector('.toc-row[data-slug="' + last + '"]');
        var name = card ? card.getAttribute('data-name') : 'reading';
        cont.textContent = 'Continue ' + name;
        cont.href = '/' + last;
        cont.hidden = false;
        begin.textContent = 'Start over';
        begin.className = 'btn-text';
        begin.addEventListener('click', function () {
          LS.keys().forEach(function (k) {
            if (k.indexOf('twbc.pos.') === 0) LS.del(k);
          });
          LS.del('twbc.last');
        });
      }
      document.querySelectorAll('.toc-row').forEach(function (c) {
        var p = LS.get('twbc.pos.' + c.getAttribute('data-slug'), null);
        if (p && p.r > 0.03) {
          var pct = Math.min(100, Math.round(p.r * 100));
          var b = c.querySelector('.bar');
          if (b) b.style.width = pct + '%';
          var t = c.querySelector('.pct');
          if (t) t.textContent = pct >= 97 ? ' · read' : ' · ' + pct + '%';
        }
      });
    }

    repaint();
  });
})();

/* ============================================================
   The chronicle rail — live state-of-the-story panel.
   Reads #rail-data (embedded by build.py), tracks scroll
   through the scene sections, and updates the snapshot.
   ============================================================ */
(function () {
  'use strict';
  document.addEventListener('DOMContentLoaded', function () {
    var dataEl = document.getElementById('rail-data');
    var rail = document.getElementById('rail');
    if (!dataEl || !rail || !window.TWBC) return;

    var D = JSON.parse(dataEl.textContent);
    var C = D.chron;
    var scenes = [].slice.call(document.querySelectorAll('main .scene'));
    var partOrder = Object.keys(C.parts);
    var css = TWBC.cssVar;

    /* ---------- tooltip ---------- */
    var tip = document.createElement('div');
    tip.id = 'tip';
    document.body.appendChild(tip);
    var tipFor = null;
    function showTip(el) {
      var t = el.getAttribute('data-tip');
      if (!t) return;
      tip.textContent = t;
      tip.classList.add('show');
      tipFor = el;
      var r = el.getBoundingClientRect();
      tip.style.left = '0px'; tip.style.top = '-200px';
      var tw = tip.offsetWidth, th = tip.offsetHeight;
      var x = Math.min(Math.max(8, r.left + r.width / 2 - tw / 2), window.innerWidth - tw - 8);
      var y = r.top - th - 8;
      if (y < 8) y = r.bottom + 8;
      tip.style.left = x + 'px'; tip.style.top = y + 'px';
    }
    function hideTip() { tip.classList.remove('show'); tipFor = null; }
    document.addEventListener('mouseover', function (e) {
      var el = e.target.closest ? e.target.closest('[data-tip]') : null;
      if (el) showTip(el); else if (tipFor) hideTip();
    });
    document.addEventListener('focusin', function (e) {
      var el = e.target.closest ? e.target.closest('[data-tip]') : null;
      if (el) showTip(el);
    });
    document.addEventListener('focusout', hideTip);
    window.addEventListener('scroll', hideTip, { passive: true });

    /* ---------- timeline ---------- */
    var ticksBox = rail.querySelector('.tl-ticks');
    var partsBox = rail.querySelector('.tl-parts');
    var tickEls = [];
    (C.ticks || []).forEach(function (tk) {
      var d = document.createElement('span');
      d.className = 'tl-tick';
      d.style.left = (tk.t * 100) + '%';
      d.setAttribute('data-tip', tk.label + ' — ' + tk.tip);
      d.setAttribute('tabindex', '0');
      d._t = tk.t;
      ticksBox.appendChild(d);
      tickEls.push(d);
    });
    var romans = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII'];
    for (var i = 0; i < D.partCount; i++) {
      var p = document.createElement('span');
      p.className = 'tl-part' + (i === D.partIndex ? ' here' : '');
      p.style.left = ((i + 0.5) / D.partCount * 100) + '%';
      p.textContent = romans[i] || (i + 1);
      partsBox.appendChild(p);
    }
    var tlFill = rail.querySelector('.tl-fill');
    var tlNow = rail.querySelector('.tl-now');

    /* ---------- claims ---------- */
    var chipEls = {};
    [].slice.call(rail.querySelectorAll('.chip-pool .chip')).forEach(function (ch) {
      chipEls[ch.getAttribute('data-claim')] = ch;
    });
    var colEls = {};
    ['u', 'f', 'o'].forEach(function (k) {
      colEls[k] = rail.querySelector('.cl-col[data-col="' + k + '"] .cl-list');
    });
    var claimsBox = rail.querySelector('.rail-claims');
    var claimInit = {};
    (C.claims || []).forEach(function (c) { claimInit[c.id] = c.init; });
    function updateClaimColumns() {
      var shown = 0;
      ['u', 'f', 'o'].forEach(function (k) {
        var list = colEls[k];
        if (!list) return;
        var col = list.closest('.cl-col');
        if (!col) return;
        var hasItems = list.children.length > 0;
        col.hidden = !hasItems;
        col.setAttribute('data-empty', hasItems ? 'false' : 'true');
        if (hasItems) shown++;
      });
      if (claimsBox) claimsBox.style.setProperty('--claim-cols', String(Math.max(1, shown)));
    }

    /* ---------- keyframes flattened to global story time ---------- */
    var frames = [];
    partOrder.forEach(function (pslug, pi) {
      (C.parts[pslug].keys || []).forEach(function (k) {
        frames.push({ gt: (pi + (k.at || 0)) / partOrder.length, k: k });
      });
    });
    frames.sort(function (a, b) { return a.gt - b.gt; });

    function stateAt(gT) {
      var st = { year: '—', ada: '—', stats: {}, cast: {}, dots: { users: 0, fellow: 0 }, claims: {} };
      for (var cid in claimInit) st.claims[cid] = claimInit[cid];
      frames.forEach(function (f) {
        if (f.gt > gT + 1e-9) return;
        var k = f.k;
        if (k.year) st.year = k.year;
        if (k.ada) st.ada = k.ada;
        var key;
        for (key in (k.stats || {})) st.stats[key] = k.stats[key];
        for (key in (k.cast || {})) st.cast[key] = k.cast[key];
        for (key in (k.claims || {})) st.claims[key] = k.claims[key];
        if (k.dots) st.dots = k.dots;
      });
      return st;
    }

    /* ---------- canvases ---------- */
    var dotsCv = document.getElementById('rail-dots');
    function drawDots(users, fellow) {
      if (!dotsCv) return;
      var pitch = 7, size = 5;
      var w = dotsCv.getBoundingClientRect().width;
      var cols = Math.max(1, Math.floor(w / pitch));
      var total = Math.round(users / 5);          // 1 square = 5M
      var fel = Math.round(fellow / 5);
      var rows = Math.max(1, Math.ceil(total / cols));
      dotsCv.style.height = (rows * pitch) + 'px';   // no dead space below
      var ctx = TWBC.fitCanvas(dotsCv);
      var h = dotsCv.getBoundingClientRect().height;
      ctx.clearRect(0, 0, w, h);
      var base = css('--line'), hot = css('--accent');
      for (var n = 0; n < total; n++) {
        var cx = (n % cols) * pitch, cy = Math.floor(n / cols) * pitch;
        if (cy + size > h) break;
        ctx.fillStyle = n < fel ? hot : base;
        ctx.fillRect(cx, cy, size, size);
      }
    }

    function bandAt(t) {
      var B = C.bands;
      if (t <= B[0].t) return B[0];
      for (var j = 1; j < B.length; j++) {
        if (t <= B[j].t) {
          var a = B[j - 1], b = B[j], f = (t - a.t) / (b.t - a.t || 1);
          return { people: a.people + (b.people - a.people) * f,
                   ada: a.ada + (b.ada - a.ada) * f };
        }
      }
      return B[B.length - 1];
    }
    var qbar = rail.querySelector('.qbar');
    function drawChart(gT) {
      if (!qbar) return;
      var b = bandAt(gT);
      var nobody = Math.max(0, 1 - b.people - b.ada);
      qbar.querySelector('.q-people').style.width = (b.people * 100) + '%';
      qbar.querySelector('.q-nobody').style.width = (nobody * 100) + '%';
      qbar.querySelector('.q-ada').style.width = (b.ada * 100) + '%';
    }

    function linkedInfoboxVisible(item) {
      var boxId = item.getAttribute('data-box-id');
      if (!boxId) return false;
      var box = document.getElementById(boxId);
      if (!box) return false;
      var r = box.getBoundingClientRect();
      var vh = window.innerHeight || document.documentElement.clientHeight;
      var vw = window.innerWidth || document.documentElement.clientWidth;
      var topbar = document.getElementById('topbar');
      var topInset = topbar ? Math.max(0, topbar.getBoundingClientRect().bottom) : 0;
      var visH = Math.min(r.bottom, vh) - Math.max(r.top, topInset);
      var visW = Math.min(r.right, vw) - Math.max(r.left, 0);
      if (visH <= 0 || visW <= 0) return false;
      var minVisiblePx = 24;
      var minVisibleRatio = 0.2;
      var needed = Math.min(Math.max(minVisiblePx, r.height * minVisibleRatio), r.height);
      return visH >= needed;
    }

    /* ---------- apply state ---------- */
    var prev = { year: null, stats: {}, cast: {}, claims: {} };
    function setFlash(el, txt) {
      if (el.textContent === txt) return;
      el.textContent = txt;
      el.classList.remove('flash');
      void el.offsetWidth;
      el.classList.add('flash');
    }
    function apply(st, gT, sceneIdx) {
      [].slice.call(document.querySelectorAll('[data-r="year"]')).forEach(function (el) {
        el.textContent = st.year;
      });
      var mu = document.querySelector('[data-r="musers"]');
      if (mu) mu.textContent = (st.stats.users || '') + (st.stats.fellowship && st.stats.fellowship !== '—' ? ' · ' + st.stats.fellowship : '');
      for (var k in st.stats) {
        var el = rail.querySelector('[data-stat="' + k + '"]');
        if (el) setFlash(el, st.stats[k]);
      }
      for (var cid in st.cast) {
        var chip = rail.querySelector('.cast-chip[data-cast="' + cid + '"]');
        if (!chip) continue;
        setFlash(chip.querySelector('i'), st.cast[cid].s);
        chip.setAttribute('data-tip', st.cast[cid].tip || '');
      }
      // ada version doubles as the Ada chip when no cast entry present
      var adaChip = rail.querySelector('.cast-chip[data-cast="ada"] i');
      if (adaChip && !st.cast.ada && st.ada) setFlash(adaChip, st.ada);
      for (var id in st.claims) {
        var target = colEls[st.claims[id]];
        var c = chipEls[id];
        if (c && target && c.parentNode !== target) {
          target.appendChild(c);
          c.classList.remove('moved');
          void c.offsetWidth;
          c.classList.add('moved');
        }
      }
      updateClaimColumns();
      tlFill.style.width = (gT * 100) + '%';
      tlNow.style.left = (gT * 100) + '%';
      tickEls.forEach(function (t) { t.classList.toggle('passed', t._t <= gT); });
      drawDots(st.dots.users || 0, st.dots.fellow || 0);
      drawChart(gT);
      // interactive slot
      var items = [].slice.call(rail.querySelectorAll('.rail-ix-item'));
      var show = null;
      if (!document.documentElement.classList.contains('hide-interactives')) {
        items.forEach(function (it) {
          if (+it.getAttribute('data-at') <= sceneIdx && linkedInfoboxVisible(it)) show = it;
        });
      }
      var changed = false;
      items.forEach(function (it) {
        var want = (it === show);
        if (want === it.hidden) { it.hidden = !want; changed = true; }
      });
      var empty = rail.querySelector('.rail-ix-empty');
      if (empty) empty.hidden = !!show;
      if (changed) window.dispatchEvent(new CustomEvent('twbc:repaint'));
    }

    /* ---------- scroll driver ---------- */
    function currentPos() {
      var mid = window.innerHeight * 0.45, idx = 0, within = 0;
      for (var i = 0; i < scenes.length; i++) {
        var r = scenes[i].getBoundingClientRect();
        if (r.top < mid) {
          idx = i;
          within = Math.min(1, Math.max(0, (mid - r.top) / Math.max(1, r.height)));
        }
      }
      return { idx: idx, frac: scenes.length ? Math.min(1, (idx + within) / scenes.length) : 0 };
    }
    var pend = false;
    function update() {
      var pos = currentPos();
      var gT = (D.partIndex + pos.frac) / D.partCount;
      apply(stateAt(gT), gT, pos.idx);
    }
    function onScroll() {
      if (pend) return;
      pend = true;
      requestAnimationFrame(function () { pend = false; update(); });
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    window.addEventListener('twbc:repaint', function () {
      update();
    });

    /* ---------- mobile overlay ---------- */
    var miniBtn = document.getElementById('rail-mini-open');
    var closeBtn = rail.querySelector('.rail-close');
    if (miniBtn) miniBtn.addEventListener('click', function () {
      document.body.classList.add('rail-open');
      setTimeout(function () { window.dispatchEvent(new CustomEvent('twbc:repaint')); update(); }, 30);
    });
    if (closeBtn) closeBtn.addEventListener('click', function () {
      document.body.classList.remove('rail-open');
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') document.body.classList.remove('rail-open');
    });

    update();
  });
})();
