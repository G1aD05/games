// Construct 2 offline client stub
(function() {
  window["OfflineClientInfo"] = {
    SetMessageCallback: function(cb) {
      // no-op stub: offline/SW messaging not needed
    }
  };
})();
