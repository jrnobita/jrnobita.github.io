/* fx.js — click sparks + confetti, no dependencies.
   One shared canvas and one rAF loop that only runs while something is
   actually on screen, so the idle cost is zero.

   Exposes window.fx:
     fx.confetti(x, y [, count])  burst from a viewport point
     fx.burstFrom(el [, count])   burst from an element's centre
     fx.spark(x, y)               the click starburst on its own          */
(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');

  /* site palette — accent green, amber, red, mint, ink, paygate violet */
  var COLORS = ['#2C6E5B', '#FFBD2E', '#FF5F56', '#3DDC97', '#15171A', '#6C74E8'];
  var SPARK_INK = '#15171A';

  var SPARK_COUNT = 8;      /* rays, at 45deg intervals   */
  var SPARK_RADIUS = 15;    /* how far they fly           */
  var SPARK_SIZE = 10;      /* ray length at t=0          */
  var SPARK_MS = 400;

  var cv, ctx, sparks = [], bits = [], running = false, vw = 0, vh = 0;

  function mount() {
    if (cv) return true;
    if (!document.body) return false;
    cv = document.createElement('canvas');
    cv.setAttribute('aria-hidden', 'true');
    cv.style.cssText = 'position:fixed;left:0;top:0;pointer-events:none;z-index:9999';
    document.body.appendChild(cv);
    ctx = cv.getContext('2d');
    fit();
    window.addEventListener('resize', fit);
    return true;
  }

  /* Size from documentElement.clientWidth, not innerWidth: innerWidth counts
     the classic scrollbar, so the backing store came out wider than the
     element's CSS box and every burst landed left of the pointer. */
  function fit() {
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    vw = document.documentElement.clientWidth;
    vh = document.documentElement.clientHeight;
    cv.style.width = vw + 'px';
    cv.style.height = vh + 'px';
    cv.width = Math.round(vw * dpr);
    cv.height = Math.round(vh * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function start() {
    if (running) return;
    running = true;
    requestAnimationFrame(frame);
  }

  function frame(now) {
    ctx.clearRect(0, 0, vw, vh);

    /* --- click sparks: 8 short rays flying outward and shortening --- */
    ctx.strokeStyle = SPARK_INK;
    ctx.lineWidth = 1.6;
    ctx.lineCap = 'round';
    sparks = sparks.filter(function (s) { return now - s.t < SPARK_MS; });
    sparks.forEach(function (s) {
      var p = (now - s.t) / SPARK_MS;
      var e = 1 - Math.pow(1 - p, 3);              /* ease-out cubic */
      var dist = SPARK_RADIUS * e;
      var len = SPARK_SIZE * (1 - e);
      ctx.globalAlpha = 1 - p;
      for (var i = 0; i < SPARK_COUNT; i++) {
        var a = (i * 2 * Math.PI) / SPARK_COUNT;
        var cos = Math.cos(a), sin = Math.sin(a);
        ctx.beginPath();
        ctx.moveTo(s.x + cos * dist, s.y + sin * dist);
        ctx.lineTo(s.x + cos * (dist + len), s.y + sin * (dist + len));
        ctx.stroke();
      }
    });
    ctx.globalAlpha = 1;

    /* --- confetti: paper rectangles under gravity, fluttering --- */
    bits = bits.filter(function (b) {
      return b.life < b.max && b.y < vh + 40;
    });
    bits.forEach(function (b) {
      b.vy += 0.28;                 /* gravity   */
      b.vx *= 0.99; b.vy *= 0.99;   /* drag      */
      b.x += b.vx; b.y += b.vy;
      b.rot += b.vr;
      b.flut += 0.13;
      b.life++;

      var fade = b.life / b.max;
      ctx.globalAlpha = fade > 0.7 ? (1 - fade) / 0.3 : 1;
      ctx.save();
      ctx.translate(b.x, b.y);
      ctx.rotate(b.rot);
      ctx.scale(Math.cos(b.flut), 1);   /* edge-on flip as it tumbles */
      ctx.fillStyle = b.c;
      ctx.fillRect(-b.w / 2, -b.h / 2, b.w, b.h);
      ctx.restore();
    });
    ctx.globalAlpha = 1;

    if (sparks.length || bits.length) {
      requestAnimationFrame(frame);
    } else {
      running = false;
      ctx.clearRect(0, 0, vw, vh);
    }
  }

  function spark(x, y) {
    if (reduce.matches || !mount()) return;
    sparks.push({ x: x, y: y, t: performance.now() });
    start();
  }

  function confetti(x, y, count) {
    if (reduce.matches || !mount()) return;
    var n = count || 80;
    for (var i = 0; i < n; i++) {
      var a = -Math.PI / 2 + (Math.random() - 0.5) * 1.6;   /* upward cone */
      var sp = 5 + Math.random() * 8;
      bits.push({
        x: x, y: y,
        vx: Math.cos(a) * sp,
        vy: Math.sin(a) * sp,
        w: 5 + Math.random() * 4,
        h: 3 + Math.random() * 3,
        rot: Math.random() * Math.PI,
        vr: (Math.random() - 0.5) * 0.4,
        flut: Math.random() * Math.PI,
        c: COLORS[(Math.random() * COLORS.length) | 0],
        life: 0,
        max: 95 + Math.random() * 55
      });
    }
    start();
  }

  function burstFrom(el, count) {
    if (!el) return;
    var r = el.getBoundingClientRect();
    confetti(r.left + r.width / 2, r.top + r.height / 2, count);
  }

  /* every click on the page gets a spark */
  document.addEventListener('pointerdown', function (e) {
    if (e.button !== 0 && e.pointerType === 'mouse') return;
    spark(e.clientX, e.clientY);
  }, { passive: true });

  window.fx = { spark: spark, confetti: confetti, burstFrom: burstFrom };
})();
