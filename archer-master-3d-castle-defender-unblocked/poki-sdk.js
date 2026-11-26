(function () {
  const resolved = value => Promise.resolve(value);

  const methods = {
    init: () => resolved(),
    initWithVideoHB: () => resolved(),

    commercialBreak: () => resolved(),
    rewardedBreak: () => resolved(false),

    displayAd: () => resolved(),
    destroyAd: () => {},

    customEvent: () => resolved(),

    gameplayStart: () => {},
    gameplayStop: () => {},

    gameLoadingStart: () => {},
    gameLoadingProgress: () => {},
    gameLoadingFinished: () => {},

    happyTime: () => {},

    setDebug: () => {},
    setLogging: () => {},
    setPlayerAge: () => {},
    getPlayerAge: () => null,

    getURLParam: () => null,
    getGameConfig: () => ({}),
    isAdBlocked: () => false
  };

  window.PokiSDK = new Proxy(methods, {
    get(target, property) {
      if (property in target) {
        return target[property];
      }

      return function () {
        console.log("PokiSDK stub:", String(property));
        return resolved();
      };
    }
  });

  window.PokiSDK_OK = true;
  window.dispatchEvent(new Event("poki-sdk-ready"));
})();
