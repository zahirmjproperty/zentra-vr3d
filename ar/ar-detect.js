/* ar-detect.js — ZENTRA VR3D-AR
   Pengesanan keupayaan AR + penghalaan peranti.

   PENTING (kajian 28 Sep 2026): JANGAN guna navigator.platform / user-agent untuk
   memutuskan laluan. Guna pengesanan CIRI sahaja — UA mudah dipalsukan dan mudah
   basi. Tiga ciri berbeza menentukan tiga laluan berbeza:

     1. WebXR immersive-ar  -> Android Chrome: AR penuh dalam pelayar
     2. rel="ar" (Quick Look) -> iPhone/iPad Safari: AR asli iOS
     3. Tiada               -> desktop: pratonton 3D sahaja

   iPhone TIDAK menyokong WebXR immersive-ar. Jangan percayai artikel yang
   mendakwa sebaliknya; uji pada peranti sebenar.                        */
(function () {
  'use strict';

  var KEPUTUSAN = {
    QUICK_LOOK: 'quick-look',   // iOS Safari
    WEBXR: 'webxr',             // Android Chrome
    TIGA_D: '3d'                // desktop / pelayar tanpa AR
  };

  function sokongQuickLook() {
    try {
      var a = document.createElement('a');
      return !!(a.relList && a.relList.supports && a.relList.supports('ar'));
    } catch (e) { return false; }
  }

  function sokongWebXR() {
    if (!navigator.xr || !navigator.xr.isSessionSupported) return Promise.resolve(false);
    return navigator.xr.isSessionSupported('immersive-ar')
      .then(function (v) { return !!v; })
      .catch(function () { return false; });
  }

  function sokongKamera() {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
  }

  /* Pulangkan objek keupayaan. Sengaja MENDAHULUKAN Quick Look: Safari iOS
     kadangkala melaporkan xr sebagai ada tetapi sesi gagal pada peranti. */
  function kesan() {
    var ql = sokongQuickLook();
    return sokongWebXR().then(function (xr) {
      var laluan = KEPUTUSAN.TIGA_D;
      if (ql) laluan = KEPUTUSAN.QUICK_LOOK;
      else if (xr) laluan = KEPUTUSAN.WEBXR;
      return {
        quickLook: ql,
        webxr: xr,
        kamera: sokongKamera(),
        laluan: laluan,
        bolehAR: ql || xr,
        https: location.protocol === 'https:'
      };
    });
  }

  /* Guna pada elemen untuk memaparkan/menyembunyikan butang AR.
     Butang AR disembunyikan pada desktop; pratonton 3D kekal. */
  function sapu(akar) {
    return kesan().then(function (k) {
      (akar || document).querySelectorAll('[data-ar-only]').forEach(function (el) {
        el.hidden = !k.bolehAR;
      });
      (akar || document).querySelectorAll('[data-ar-3d-only]').forEach(function (el) {
        el.hidden = k.bolehAR;
      });
      (akar || document).querySelectorAll('[data-ar-http-warn]').forEach(function (el) {
        el.hidden = k.https;
      });
      document.documentElement.setAttribute('data-ar-route', k.laluan);
      return k;
    });
  }

  window.ZVR3D_AR = { KEPUTUSAN: KEPUTUSAN, kesan: kesan, sapu: sapu };
})();
