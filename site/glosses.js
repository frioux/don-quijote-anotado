/* Personal glosses for the browser reader.
 *
 * Double-tap a word in the chapter and type your own English for it; it is
 * written small above the word (an HTML <ruby> annotation) and kept in this
 * browser's localStorage. A gloss is keyed by the paragraph id and the word's
 * position in the paragraph ("p1c02-p5:17"), which is stable because the
 * Spanish text is Gutenberg's, verbatim, and verified on every build.
 *
 * Usage: dqGlosses.init({ rendition: rendition, header: headerEl, before: elementInHeader })
 */
window.dqGlosses = (function () {
  "use strict";

  var STORE = "dq.glosses.v1";
  var PREFS = "dq.glosses.prefs.v1";
  var WORD = /[\p{L}\p{M}\d]+/gu;

  // ---- storage ------------------------------------------------------------

  var glosses = read(STORE, {});   // key -> { w: "aguardar", g: "to wait", t: 1700000000 }
  var prefs = read(PREFS, {});     // { show: true, tipSeen: true }
  if (prefs.show === undefined) prefs.show = true;

  function read(key, fallback) {
    try { return JSON.parse(localStorage.getItem(key)) || fallback; } catch (e) { return fallback; }
  }
  function write(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* private mode, full, etc. */ }
  }
  function saveGlosses() { write(STORE, glosses); updateCount(); }
  function savePrefs() { write(PREFS, prefs); }

  function count() { return Object.keys(glosses).length; }

  // The most recent gloss given to the same word form anywhere in the book.
  function suggestion(word) {
    var w = word.toLowerCase(), best = null;
    for (var k in glosses) {
      var e = glosses[k];
      if (e.w.toLowerCase() === w && (!best || e.t > best.t)) best = e;
    }
    return best && best.g;
  }

  // ---- words in a paragraph ------------------------------------------------

  // Text that is not part of the Spanish sentence: note numbers and the
  // glosses themselves.
  function skip(el) {
    var t = el.tagName.toLowerCase();
    return t === "rt" || t === "sup" || (t === "a" && el.classList.contains("nr"));
  }

  function textNodes(p) {
    var out = [];
    var walker = p.ownerDocument.createTreeWalker(p, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT, {
      acceptNode: function (n) {
        if (n.nodeType === 1) return skip(n) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_SKIP;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var n;
    while ((n = walker.nextNode())) out.push(n);
    return out;
  }

  // Every word of the paragraph, in order: { node, start, end, text }.
  // A glossed word is the text node inside its <ruby>, so wrapping and
  // unwrapping never change the numbering.
  function words(p) {
    var out = [];
    textNodes(p).forEach(function (node) {
      var s = node.nodeValue, m;
      WORD.lastIndex = 0;
      while ((m = WORD.exec(s))) out.push({ node: node, start: m.index, end: m.index + m[0].length, text: m[0] });
    });
    return out;
  }

  function rubyOf(node) {
    var el = node && node.parentNode;
    return el && el.nodeType === 1 && el.tagName.toLowerCase() === "ruby" && el.classList.contains("g") ? el : null;
  }

  // Wrap the word in <ruby class="g">word<rt>gloss</rt></ruby>, or update it.
  function wrap(w, key, gloss) {
    var ruby = rubyOf(w.node);
    if (ruby) { ruby.lastChild.textContent = gloss; return ruby; }
    var doc = w.node.ownerDocument, node = w.node;
    if (w.end < node.nodeValue.length) node.splitText(w.end);
    var mid = w.start > 0 ? node.splitText(w.start) : node;
    ruby = doc.createElement("ruby");
    ruby.className = "g";
    ruby.setAttribute("data-k", key);
    var rt = doc.createElement("rt");
    rt.textContent = gloss;
    mid.parentNode.insertBefore(ruby, mid);
    ruby.appendChild(mid);
    ruby.appendChild(rt);
    return ruby;
  }

  function unwrap(ruby) {
    var parent = ruby.parentNode;
    parent.insertBefore(ruby.firstChild, ruby);
    parent.removeChild(ruby);
    parent.normalize();
  }

  // Draw every stored gloss of a freshly rendered chapter.
  function decorate(doc) {
    var byPara = {};
    for (var k in glosses) {
      var i = k.lastIndexOf(":");
      (byPara[k.slice(0, i)] = byPara[k.slice(0, i)] || []).push(+k.slice(i + 1));
    }
    Array.prototype.forEach.call(doc.querySelectorAll("p[id]"), function (p) {
      var prefix = p.id + ":", idx = byPara[p.id];
      if (!idx) return;
      var ws = words(p);
      // Highest index first: splitting a text node leaves the words before the
      // split where they were, so earlier entries stay valid.
      idx.sort(function (a, b) { return b - a; }).forEach(function (i) {
        if (ws[i]) wrap(ws[i], prefix + i, glosses[prefix + i].g);
      });
    });
  }

  // ---- finding the tapped word ----------------------------------------------

  function caret(doc, x, y) {
    if (doc.caretPositionFromPoint) {
      var c = doc.caretPositionFromPoint(x, y);
      return c && { node: c.offsetNode, offset: c.offset };
    }
    if (doc.caretRangeFromPoint) {
      var r = doc.caretRangeFromPoint(x, y);
      return r && { node: r.startContainer, offset: r.startOffset };
    }
    return null;
  }

  // The word under (x, y) in the chapter frame: { p, index, key, w, ruby }.
  function wordAt(doc, x, y) {
    var el = doc.elementFromPoint(x, y);
    if (!el) return null;
    if (el.closest("a")) return null;                    // note refs, links
    var p = el.closest("p[id]");
    var ruby = el.closest("ruby.g");
    var node, start;
    if (ruby) {
      node = ruby.firstChild; start = 0;
    } else {
      var c = caret(doc, x, y);
      if (!c || c.node.nodeType !== 3) return null;
      node = c.node;
      if (!p) p = node.parentNode.closest("p[id]");
      var s = node.nodeValue, m, hit = null;
      WORD.lastIndex = 0;
      while ((m = WORD.exec(s))) {
        if (c.offset >= m.index && c.offset <= m.index + m[0].length) { hit = m; break; }
      }
      if (!hit) return null;
      start = hit.index;
    }
    if (!p) return null;
    var ws = words(p);
    for (var i = 0; i < ws.length; i++) {
      if (ws[i].node === node && ws[i].start === start) {
        return { p: p, index: i, key: p.id + ":" + i, w: ws[i], ruby: ruby || rubyOf(node) };
      }
    }
    return null;
  }

  // ---- the editor -----------------------------------------------------------

  var CSS = [
    "#viewer{touch-action:manipulation}",
    "#gl-editor{position:fixed;z-index:20;box-sizing:border-box;width:17rem;max-width:calc(100vw - 2rem);padding:.8rem .9rem .7rem;",
    "  background:var(--pop,#fff);color:var(--fg,#222);border:1px solid var(--line,#ccc);border-radius:12px;",
    "  box-shadow:0 10px 30px rgba(0,0,0,.22),0 2px 6px rgba(0,0,0,.12);font-family:system-ui,-apple-system,sans-serif;font-size:.9rem;}",
    "#gl-editor[hidden]{display:none}",
    "#gl-editor::before{content:'';position:absolute;left:var(--arrow-x,50%);top:-7px;width:12px;height:12px;margin-left:-6px;",
    "  background:var(--pop,#fff);border-left:1px solid var(--line,#ccc);border-top:1px solid var(--line,#ccc);transform:rotate(45deg)}",
    "#gl-editor.above::before{top:auto;bottom:-7px;transform:rotate(225deg)}",
    "#gl-editor .gl-word{font-family:Georgia,'Times New Roman',serif;font-style:italic;font-size:1.15rem;margin:0 0 .5rem;",
    "  display:flex;align-items:baseline;justify-content:space-between;gap:.5rem}",
    "#gl-editor .gl-word small{font-family:system-ui,-apple-system,sans-serif;font-style:normal;font-size:.72rem;opacity:.55;white-space:nowrap}",
    "#gl-editor input{font:inherit;font-size:1rem;width:100%;box-sizing:border-box;padding:.45rem .6rem;border:1px solid var(--line,#ccc);",
    "  border-radius:8px;background:var(--bg,#fff);color:var(--fg,#222);outline:none}",
    "#gl-editor input:focus{border-color:var(--accent,#7a3b1e);box-shadow:0 0 0 3px color-mix(in srgb,var(--accent,#7a3b1e) 22%,transparent)}",
    "#gl-editor .gl-row{display:flex;align-items:center;justify-content:space-between;gap:.5rem;margin-top:.55rem;font-size:.75rem;opacity:.7}",
    "#gl-editor .gl-row kbd{font:inherit;padding:0 .3em;border:1px solid var(--line,#ccc);border-bottom-width:2px;border-radius:4px}",
    "#gl-editor .gl-remove{font:inherit;color:var(--accent,#7a3b1e);background:none;border:0;padding:0;cursor:pointer;opacity:1}",
    "#gl-editor .gl-remove[hidden]{display:none}",
    "#gl-editor .gl-touch{display:none}",
    "#gl-editor .gl-sugg{display:none;margin-top:.5rem;font-size:.8rem;opacity:.8}",
    "#gl-editor .gl-sugg.on{display:block}",
    "#gl-editor .gl-sugg button{font:inherit;cursor:pointer;background:var(--bar,#eee);color:inherit;border:1px solid var(--line,#ccc);border-radius:999px;padding:.1rem .6rem;margin-left:.25rem}",
    "@media (max-width:699px){",
    "  #gl-editor{width:auto;max-width:none;left:0!important;right:0;top:auto!important;bottom:0;border-radius:16px 16px 0 0;",
    "    padding:1rem 1.1rem calc(.9rem + env(safe-area-inset-bottom));box-shadow:0 -8px 30px rgba(0,0,0,.25)}",
    "  #gl-editor::before{display:none}",
    "  #gl-editor .gl-word{font-size:1.35rem}",
    "  #gl-editor .gl-keys{display:none}",
    "  #gl-editor .gl-touch{display:inline}",
    "}",
    "#gl-tip{position:fixed;left:50%;bottom:1.25rem;transform:translateX(-50%);z-index:9;max-width:calc(100vw - 2rem);box-sizing:border-box;",
    "  padding:.6rem .9rem .6rem 1rem;border-radius:999px;background:var(--fg,#222);color:var(--bg,#fff);font-family:system-ui,-apple-system,sans-serif;font-size:.85rem;",
    "  display:flex;align-items:center;gap:.75rem;box-shadow:0 6px 24px rgba(0,0,0,.25);animation:gl-rise .5s ease-out}",
    "#gl-tip[hidden]{display:none}",
    "#gl-tip button{font:inherit;color:inherit;background:none;border:0;cursor:pointer;opacity:.7;padding:0 .2rem;font-size:1.1rem;line-height:1}",
    "@keyframes gl-rise{from{opacity:0;transform:translate(-50%,10px)}to{opacity:1;transform:translate(-50%,0)}}",
    "#gl-menu{position:relative}",
    "#gl-menu > button .gl-n{display:inline-block;min-width:1.3em;margin-left:.35em;padding:0 .35em;border-radius:999px;background:var(--accent,#7a3b1e);color:var(--bg,#fff);font-size:.75em;text-align:center;line-height:1.5}",
    "#gl-menu > button .gl-n:empty{display:none}",
    "#gl-panel{position:absolute;right:0;top:calc(100% + .4rem);z-index:15;min-width:15rem;padding:.75rem .9rem;background:var(--pop,#fff);color:var(--fg,#222);",
    "  border:1px solid var(--line,#ccc);border-radius:10px;box-shadow:0 10px 30px rgba(0,0,0,.2);font-size:.85rem;line-height:1.45}",
    "#gl-panel[hidden]{display:none}",
    "#gl-panel p{margin:0 0 .6rem}",
    "#gl-panel label{display:flex;align-items:center;gap:.5rem;margin:.4rem 0 .7rem;cursor:pointer}",
    "#gl-panel .gl-actions{display:flex;flex-wrap:wrap;gap:.4rem}",
    "#gl-panel .gl-actions button{font:inherit;font-size:.8rem}",
    "#gl-panel .gl-danger{color:#b3261e}",
    "@media (prefers-color-scheme:dark){#gl-panel .gl-danger{color:#f28b82}}"
  ].join("\n");

  // Styles for inside the chapter frame. --gl-accent is set by the reader's themes.
  var FRAME_CSS = [
    "html,body{touch-action:manipulation}",
    "p[id]{line-height:1.9}",
    "ruby.g{ruby-position:over;ruby-align:center;border-bottom:1px dotted color-mix(in srgb,var(--gl-accent,currentColor) 55%,transparent);cursor:pointer}",
    "ruby.g>rt{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;font-size:.52em;line-height:1;font-style:normal;font-weight:500;",
    "  letter-spacing:.01em;color:var(--gl-accent,currentColor);text-align:center;white-space:nowrap;user-select:none;-webkit-user-select:none;",
    "  transform:translateY(.2em)}",
    "ruby.g.editing{background:color-mix(in srgb,var(--gl-accent,currentColor) 16%,transparent);border-radius:3px}",
    "ruby.g.editing>rt:empty::before{content:'\\2026';opacity:.5}",
    "body.gl-hide ruby.g>rt{visibility:hidden}",
    "body.gl-hide ruby.g{border-bottom-color:transparent}"
  ].join("\n");

  var rendition, viewer, editor, input, wordEl, posEl, removeBtn, suggEl, tipEl, countEl, panel;
  var editing = null;   // { doc, frame, ruby, key, w, prev }

  function h(html) {
    var t = document.createElement("template");
    t.innerHTML = html.trim();
    return t.content.firstChild;
  }

  function buildEditor() {
    editor = h('<div id="gl-editor" hidden role="dialog" aria-label="Gloss">' +
      '<div class="gl-word"><span class="w"></span><small class="pos"></small></div>' +
      '<input type="text" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false" enterkeyhint="done" placeholder="your English for this word…">' +
      '<div class="gl-sugg">Earlier you wrote <button type="button"></button></div>' +
      '<div class="gl-row"><span class="gl-keys"><kbd>Enter</kbd> save · <kbd>Esc</kbd> cancel</span><span class="gl-touch">Tap anywhere else to save</span>' +
      '<button type="button" class="gl-remove" hidden>Remove</button></div>' +
      '</div>');
    document.body.appendChild(editor);
    input = editor.querySelector("input");
    wordEl = editor.querySelector(".w");
    posEl = editor.querySelector(".pos");
    removeBtn = editor.querySelector(".gl-remove");
    suggEl = editor.querySelector(".gl-sugg");

    input.addEventListener("input", function () {
      if (editing) editing.ruby.lastChild.textContent = input.value.trim();
    });
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") { e.preventDefault(); commit(); }
      else if (e.key === "Escape") { e.preventDefault(); cancel(); }
    });
    // Buttons must not steal focus from the input (which would commit early).
    editor.addEventListener("pointerdown", function (e) { if (e.target !== input) e.preventDefault(); });
    removeBtn.addEventListener("click", function () { input.value = ""; commit(); });
    suggEl.querySelector("button").addEventListener("click", function () {
      input.value = this.textContent;
      input.dispatchEvent(new Event("input"));
      commit();
    });
    // A tap anywhere else saves and closes.
    document.addEventListener("pointerdown", function (e) {
      if (editing && !editor.contains(e.target)) commit();
    }, true);
    document.addEventListener("scroll", function () { if (editing) place(); }, true);
    window.addEventListener("resize", function () { if (editing) place(); });
  }

  function narrow() { return window.matchMedia("(max-width: 699px)").matches; }

  // Put the editor under the word (or above it when there is no room).
  function place() {
    if (!editing || narrow()) return;
    var fr = editing.frame.getBoundingClientRect();
    var r = editing.ruby.getBoundingClientRect();
    var cx = fr.left + r.left + r.width / 2;
    var top = fr.top + r.bottom;
    var bottom = fr.top + r.top;
    var ew = editor.offsetWidth, eh = editor.offsetHeight;
    var left = Math.max(8, Math.min(cx - ew / 2, window.innerWidth - ew - 8));
    var above = top + 12 + eh > window.innerHeight && bottom - 12 - eh > 0;
    editor.classList.toggle("above", above);
    editor.style.left = left + "px";
    editor.style.top = (above ? bottom - 12 - eh : top + 12) + "px";
    editor.style.setProperty("--arrow-x", Math.max(14, Math.min(cx - left, ew - 14)) + "px");
  }

  function open(doc, frame, hit) {
    if (editing) commit();
    var entry = glosses[hit.key];
    var ruby = hit.ruby || wrap(hit.w, hit.key, entry ? entry.g : "");
    ruby.classList.add("editing");
    editing = { doc: doc, frame: frame, ruby: ruby, key: hit.key, w: hit.w, prev: entry ? entry.g : null };

    wordEl.textContent = hit.w.text;
    var m = /^p(\d+)c(\d+)-p(\d+)$/.exec(hit.p.id);
    posEl.textContent = m ? (m[1] === "1" ? "I" : "II") + "." + (+m[2]) + " ¶" + m[3] : "";
    input.value = entry ? entry.g : "";
    removeBtn.hidden = !entry;
    var sugg = entry ? null : suggestion(hit.w.text);
    suggEl.classList.toggle("on", !!sugg);
    if (sugg) suggEl.querySelector("button").textContent = sugg;

    editor.hidden = false;
    place();
    input.focus();
    input.select();

    // On a phone the sheet covers the bottom of the screen; bring the word
    // up into view so the gloss can be watched appearing as it is typed.
    if (narrow()) {
      var box = frame.closest(".epub-container");
      var fr = frame.getBoundingClientRect(), r = ruby.getBoundingClientRect();
      var limit = window.innerHeight - editor.offsetHeight - 40;
      if (box && fr.top + r.bottom > limit) box.scrollBy({ top: fr.top + r.bottom - limit + 40, behavior: "smooth" });
    }
  }

  function close() {
    if (!editing) return;
    editing.ruby.classList.remove("editing");
    editing = null;
    editor.hidden = true;
  }

  function commit() {
    if (!editing) return;
    var e = editing, g = input.value.trim();
    if (g) {
      glosses[e.key] = { w: e.w.text, g: g, t: Date.now() };
      e.ruby.lastChild.textContent = g;
      hideTip(true);
    } else {
      delete glosses[e.key];
      unwrap(e.ruby);
    }
    saveGlosses();
    close();
  }

  function cancel() {
    if (!editing) return;
    var e = editing;
    if (e.prev === null) unwrap(e.ruby); else e.ruby.lastChild.textContent = e.prev;
    close();
  }

  // ---- first-run tip ----------------------------------------------------------

  function showTip() {
    if (tipEl || prefs.tipSeen || count()) return;
    tipEl = h('<div id="gl-tip"><span>Double-tap any word to write your own English above it.</span><button type="button" aria-label="Dismiss">✕</button></div>');
    tipEl.querySelector("button").addEventListener("click", function () { hideTip(true); });
    document.body.appendChild(tipEl);
  }
  function hideTip(forever) {
    if (tipEl) { tipEl.remove(); tipEl = null; }
    if (forever && !prefs.tipSeen) { prefs.tipSeen = true; savePrefs(); }
  }

  // ---- header menu: count, show/hide, export, import, clear ----------------

  function buildMenu(header, before) {
    var menu = h('<div id="gl-menu"><button type="button" aria-haspopup="true">Glosses<span class="gl-n"></span></button>' +
      '<div id="gl-panel" hidden>' +
      '<p>Double-tap a word in the text to write your own English above it. Double-tap it again to change or remove it.</p>' +
      '<label><input type="checkbox" class="gl-show"> Show my glosses</label>' +
      '<div class="gl-actions"><button type="button" class="gl-export">Export…</button><button type="button" class="gl-import">Import…</button><button type="button" class="gl-clear gl-danger">Clear all</button></div>' +
      '<input type="file" accept="application/json,.json" hidden>' +
      '</div></div>');
    panel = menu.querySelector("#gl-panel");
    countEl = menu.querySelector(".gl-n");
    var toggle = menu.querySelector(".gl-show");
    var file = menu.querySelector('input[type=file]');
    toggle.checked = prefs.show;

    menu.firstChild.addEventListener("click", function () { panel.hidden = !panel.hidden; });
    document.addEventListener("pointerdown", function (e) {
      if (!panel.hidden && !menu.contains(e.target)) panel.hidden = true;
    }, true);
    toggle.addEventListener("change", function () {
      prefs.show = toggle.checked; savePrefs(); applyShow();
    });
    menu.querySelector(".gl-export").addEventListener("click", function () {
      var blob = new Blob([JSON.stringify({ format: "dq-glosses", version: 1, glosses: glosses }, null, 1)], { type: "application/json" });
      var a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "don-quijote-glosas.json";
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
    });
    menu.querySelector(".gl-import").addEventListener("click", function () { file.value = ""; file.click(); });
    file.addEventListener("change", function () {
      var f = file.files[0];
      if (!f) return;
      f.text().then(function (txt) {
        var data = JSON.parse(txt);
        var incoming = data && data.glosses ? data.glosses : data;
        var n = 0;
        for (var k in incoming) {
          var e = incoming[k];
          if (/^p\d+c\d+-p\d+:\d+$/.test(k) && e && typeof e.g === "string" && typeof e.w === "string") {
            glosses[k] = { w: e.w, g: e.g, t: +e.t || Date.now() }; n++;
          }
        }
        saveGlosses();
        redecorate();
        alert(n + " glosses imported.");
      }).catch(function () { alert("That file is not a glosses export."); });
    });
    menu.querySelector(".gl-clear").addEventListener("click", function () {
      if (!count() || !confirm("Remove all " + count() + " of your glosses from this browser? Export first if you want to keep them.")) return;
      glosses = {};
      saveGlosses();
      redecorate();
      panel.hidden = true;
    });
    header.insertBefore(menu, before || null);
    updateCount();
  }

  function updateCount() {
    if (countEl) countEl.textContent = count() ? String(count()) : "";
  }

  function eachFrameDoc(fn) {
    rendition.getContents().forEach(function (c) { if (c.document) fn(c.document); });
  }
  function applyShow() {
    eachFrameDoc(function (doc) { doc.body.classList.toggle("gl-hide", !prefs.show); });
  }
  function redecorate() {
    eachFrameDoc(function (doc) {
      Array.prototype.forEach.call(doc.querySelectorAll("ruby.g"), unwrap);
      decorate(doc);
    });
  }

  // ---- wiring ---------------------------------------------------------------

  function onContent(contents) {
    var doc = contents.document;
    var frame = contents.window.frameElement;
    var style = doc.createElement("style");
    style.textContent = FRAME_CSS;
    doc.head.appendChild(style);
    doc.body.classList.toggle("gl-hide", !prefs.show);
    decorate(doc);

    // Two taps within 400 ms and a few pixels: a double-tap. Pointer events
    // cover mouse and touch alike, and a touch that turns into a scroll ends
    // in pointercancel, not pointerup, so scrolling never counts.
    var last = null;
    doc.addEventListener("pointerup", function (e) {
      if (e.pointerType === "mouse" && e.button !== 0) return;
      var now = Date.now();
      if (last && now - last.t < 400 && Math.abs(e.clientX - last.x) < 24 && Math.abs(e.clientY - last.y) < 24) {
        last = null;
        var hit = wordAt(doc, e.clientX, e.clientY);
        if (hit) { e.preventDefault(); open(doc, frame, hit); }
      } else {
        last = { t: now, x: e.clientX, y: e.clientY };
      }
    });
    // The second click of a double-click would otherwise select the word.
    doc.addEventListener("mousedown", function (e) { if (e.detail > 1) e.preventDefault(); });
    // A tap in the text saves and closes the editor and the menu, like a tap
    // anywhere else on the page (frame events do not reach the page).
    doc.addEventListener("pointerdown", function () {
      if (editing) commit();
      if (panel) panel.hidden = true;
    }, true);
    doc.addEventListener("keydown", function (e) { if (e.key === "Escape") cancel(); });
  }

  function init(opts) {
    rendition = opts.rendition;
    var style = document.createElement("style");
    style.textContent = CSS;
    document.head.appendChild(style);
    buildEditor();
    if (opts.header) buildMenu(opts.header, opts.before);
    rendition.hooks.content.register(onContent);
    rendition.on("rendered", showTip);
  }

  return { init: init };
})();
