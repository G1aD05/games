// ShawGames: offline stand-in for the GamePush SDK.
// School filters often block GamePush (eponesh.com / gamepush.com); the game then
// waits forever on its loading screen. If the real SDK has not started within
// WAIT_MS, start the game with this stub instead. Player data is kept in localStorage.
(function () {
  var WAIT_MS = 15000;
  var KEY = "sg-gp-player";
  var started = false;
  var realInit;

  var store = {};
  try { store = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) {}
  function save() { try { localStorage.setItem(KEY, JSON.stringify(store)); } catch (e) {} }

  function noop() {}
  function done() { return Promise.resolve(); }

  // Any method not listed fails like a network error (the game's bridge chains .then/.catch
  // on most calls); any "is/has/can" property reads as false.
  function mod(name, own) {
    return new Proxy(own, {
      get: function (t, k) {
        if (k in t || typeof k === "symbol") return t[k];
        if (/^(is|has|can)[A-Z]/.test(k)) return false;
        if (window.SG_GP_DEBUG) console.warn("GP stub", name + "." + k);
        return function () { var p = Promise.reject(new Error("offline")); p.catch(noop); return p; };
      },
    });
  }

  function withEvents(o) {
    var handlers = {};
    o.on = function (e, f) { (handlers[e] = handlers[e] || []).push(f); };
    o.once = o.on;
    o.off = function (e, f) { handlers[e] = (handlers[e] || []).filter(function (h) { return h !== f; }); };
    o.emit = function (e, v) { (handlers[e] || []).forEach(function (f) { try { f(v); } catch (err) {} }); };
    return o;
  }

  // No ads offline: report each ad as started and closed unsuccessfully, so the game moves on.
  function ad(kind) {
    return function () {
      ads.emit(kind + ":start"); ads.emit("start");
      setTimeout(function () { ads.emit(kind + ":close", false); ads.emit("close", false); }, 0);
      return Promise.resolve(false);
    };
  }
  var ads = withEvents({ closeSticky: noop, refreshSticky: noop });
  ads.showPreloader = ad("preloader");
  ads.showFullscreen = ad("fullscreen");
  ads.showRewardedVideo = ad("rewarded");
  ads.showSticky = ad("sticky");

  var player = mod("player", withEvents({
    id: 0, name: "", avatar: "", score: 0, isLoggedIn: false, isStub: true, hasAnyCredentials: false,
    fields: [], stats: {}, ready: Promise.resolve(),
    get: function (k) { return k in store ? store[k] : 0; },
    set: function (k, v) { store[k] = v; save(); },
    add: function (k, v) { store[k] = (Number(store[k]) || 0) + Number(v); save(); },
    toggle: function (k) { store[k] = !store[k]; save(); },
    has: function (k) { return !!store[k]; },
    remove: function (k) { delete store[k]; save(); },
    reset: function () { store = {}; save(); },
    getField: function (k) { return { key: k, name: k, type: "stats", default: 0, important: false, variants: [], limits: null, intervalIncrement: null }; },
    getFieldName: function (k) { return k; },
    getFieldVariantName: function () { return ""; },
    getMaxValue: function () { return 0; },
    getMinValue: function () { return 0; },
    sync: done, load: done, login: done, logout: done, fetchFields: done,
    enableAutoSync: noop, disableAutoSync: noop,
  }));

  var gp = mod("gp", withEvents({
    isDev: false, isMobile: false, isPaused: false, isPortrait: false, isAllowedOrigin: true,
    language: "en", avatarGenerator: "dicebear_retro", serverTime: new Date(),
    player: player,
    ads: mod("ads", ads),
    platform: mod("platform", { type: "NONE", tag: "", getNativeSDK: noop }),
    app: mod("app", withEvents({ title: "", description: "", image: "", url: "", requestReview: done, addShortcut: done })),
    analytics: mod("analytics", { hit: noop, goal: noop }),
    logger: mod("logger", { log: noop, info: noop, warn: noop, error: noop }),
    fullscreen: mod("fullscreen", withEvents({ open: noop, close: noop, toggle: noop })),
    leaderboard: mod("leaderboard", withEvents({})),
    achievements: mod("achievements", withEvents({ list: [], unlockedList: [] })),
    payments: mod("payments", withEvents({
      products: [], purchases: [],
      fetchProducts: function () { return Promise.resolve({ products: [], playerPurchases: [] }); },
    })),
    variables: mod("variables", withEvents({ list: [] })),
    storage: mod("storage", withEvents({})),
    socials: mod("socials", withEvents({ communityLink: "" })),
    channels: mod("channels", withEvents({ mainChatId: 0 })),
    gameStart: noop, gameplayStart: noop, gameplayStop: noop, pause: noop, resume: noop,
    changeLanguage: done, changeAvatarGenerator: noop, loadOverlay: done,
  }));
  ["documents", "events", "experiments", "files", "gamesCollections", "images", "players", "rewards",
    "schedulers", "segments", "triggers", "uniques"].forEach(function (k) {
    gp[k] = mod(k, withEvents({ list: [], activeList: [], givenList: [], activatedList: [] }));
  });

  function startStub() {
    if (started || !realInit) return;
    started = true;
    console.warn("GamePush unreachable - starting offline");
    realInit(gp);
  }

  // The game's framework assigns window.onGPInit / onGPError; wrap them so whichever
  // starts first (real SDK or stub) wins and the other is ignored.
  Object.defineProperty(window, "onGPInit", {
    configurable: true,
    get: function () { return realInit && function (g) { if (!started) { started = true; realInit(g); } }; },
    set: function (f) { realInit = f; setTimeout(startStub, WAIT_MS); },
  });
  Object.defineProperty(window, "onGPError", {
    configurable: true,
    get: function () { return function () { startStub(); }; },
    set: noop,
  });
})();
