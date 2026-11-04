(function () {
  if (!document.body.dataset.auth) return;           // only for logged-in people
  var LIMIT = 180000, WARN = 30000, PING = 20000, KEY = "ags_last";
  var box = document.getElementById("idle"), secs = document.getElementById("idle-sec");
  var stay = document.getElementById("idle-stay"), out = document.getElementById("idle-out");
  var last = Date.now(), lastPing = Date.now();

  function store() { try { localStorage.setItem(KEY, String(last)); } catch (e) {} }
  function shared() { try { var v = parseInt(localStorage.getItem(KEY), 10); if (v > last) last = v; } catch (e) {} }
  function csrf() {
    var i = document.querySelector("form.lo input[name=csrfmiddlewaretoken]");
    return i ? i.value : "";
  }
  function logout() {
    var f = document.querySelector("form.lo");
    if (!f) { location.href = "/accounts/login/?timeout=1"; return; }
    var n = document.createElement("input");
    n.type = "hidden"; n.name = "next"; n.value = "/accounts/login/?timeout=1";
    f.appendChild(n); f.submit();
  }
  function ping() {
    lastPing = Date.now();
    fetch("/accounts/keepalive/", { method: "POST", headers: { "X-CSRFToken": csrf() }, credentials: "same-origin" })
      .then(function (r) { if (r.status === 401 || r.status === 403) logout(); })
      .catch(function () {});
  }
  function activity() {
    if (!box.hidden) return;                           // warning open: only the buttons count
    var now = Date.now();
    if (now - last < 1000) return;
    last = now; store();
    if (now - lastPing > PING) ping();
  }

  ["mousemove", "keydown", "click", "scroll", "touchstart"].forEach(function (e) {
    document.addEventListener(e, activity, { passive: true });
  });
  stay.onclick = function () { last = Date.now(); store(); ping(); box.hidden = true; };
  out.onclick = logout;

  setInterval(function () {
    shared();
    var idle = Date.now() - last;
    if (idle >= LIMIT) { logout(); return; }
    if (idle >= LIMIT - WARN) {
      if (box.hidden) { box.hidden = false; stay.focus(); }
      secs.textContent = Math.ceil((LIMIT - idle) / 1000);
    } else if (!box.hidden) { box.hidden = true; }
  }, 1000);
})();