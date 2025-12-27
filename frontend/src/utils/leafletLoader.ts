export function loadLeafletAssets() {
  return new Promise<void>((resolve, reject) => {
    if (typeof window === "undefined") {
      resolve();
      return;
    }
    if (window.L) {
      resolve();
      return;
    }

    const existingScript = document.querySelector('script[data-leaflet="true"]');
    const existingCss = document.querySelector('link[data-leaflet="true"]');
    let pending = 0;

    const finish = () => {
      pending -= 1;
      if (pending <= 0) resolve();
    };

    if (!existingCss) {
      pending += 1;
      const css = document.createElement("link");
      css.rel = "stylesheet";
      css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      css.dataset.leaflet = "true";
      css.onload = finish;
      css.onerror = reject;
      document.head.appendChild(css);
    }

    if (!existingScript) {
      pending += 1;
      const script = document.createElement("script");
      script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
      script.defer = true;
      script.dataset.leaflet = "true";
      script.onload = finish;
      script.onerror = reject;
      document.body.appendChild(script);
    }

    if (pending === 0) {
      resolve();
    }
  });
}
