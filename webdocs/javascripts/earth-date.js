(() => {
  let stopCurrent = () => {};

  function start() {
    stopCurrent();
    const target = document.querySelector('[data-live-earth-date]');
    if (!target) return;

    let sample = null;
    let timer = 0;
    let controller = null;

    function render() {
      if (!sample) return;
      const elapsed = (performance.now() - sample.received) / 1000;
      if (elapsed < 0 || elapsed > sample.validFor) return;

      let year = sample.year;
      let fraction = sample.fraction + sample.rate * elapsed;
      while (fraction >= 1) { fraction -= 1; year += 1; }
      while (fraction < 0) { fraction += 1; year -= 1; }

      // Truncate rather than round so the displayed coordinate never leads it.
      const digits = Math.floor(fraction * 10000).toString().padStart(4, '0');
      target.textContent = `${year}.${digits}`;
      target.closest('.earth-date')?.setAttribute(
        'aria-label', `Current NEPP Earth Date ${year}.${digits}`
      );
    }

    async function update() {
      controller?.abort();
      controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), 3000);
      const nonce = Array.from(crypto.getRandomValues(new Uint8Array(16)),
        byte => byte.toString(16).padStart(2, '0')).join('');
      const sent = performance.now();

      try {
        const response = await fetch(`/api/v2/state?nonce=${nonce}`, {
          cache: 'no-store', credentials: 'omit', redirect: 'error',
          signal: controller.signal
        });
        if (!response.ok) throw new Error('NEPP API unavailable');
        const data = await response.json();
        const received = performance.now();
        const rtt = (received - sent) / 1000;
        if (data.schema !== 'nepp-web-1' || data.protocol_version !== 2 ||
            data.nonce !== nonce || !data.ed ||
            !Number.isInteger(data.ed.year) ||
            !Number.isFinite(Number(data.ed.fraction)) ||
            !Number.isFinite(data.ed.rate) ||
            !Number.isFinite(data.processing_seconds) ||
            !Number.isFinite(data.max_extrapolation_seconds)) {
          throw new Error('Invalid NEPP response');
        }

        const oneWay = Math.max(0, (rtt - data.processing_seconds) / 2);
        sample = {
          year: data.ed.year,
          fraction: Number(data.ed.fraction) + data.ed.rate * oneWay,
          rate: data.ed.rate,
          received,
          validFor: Math.min(300, Math.max(0, data.max_extrapolation_seconds - oneWay))
        };
        render();
      } catch (_) {
        // Keep the last valid estimate, or the static example before first sync.
      } finally {
        window.clearTimeout(timeout);
        timer = window.setTimeout(update, 60000);
      }
    }

    const animation = window.setInterval(render, 1000);
    update();
    stopCurrent = () => {
      controller?.abort();
      window.clearTimeout(timer);
      window.clearInterval(animation);
    };
  }

  if (typeof document$ !== 'undefined') document$.subscribe(start);
  else if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
