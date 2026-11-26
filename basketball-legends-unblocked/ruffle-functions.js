async function embedSWF(url, containerId) {
  const container = document.getElementById(containerId);
  const status = document.getElementById('status');
  const message = document.getElementById('status-message');
  const retry = document.getElementById('retry');

  status.hidden = false;
  retry.hidden = true;
  message.textContent = 'Loading Basketball Legends…';
  container.replaceChildren();

  try {
    if (typeof window.RufflePlayer?.newest !== 'function') {
      throw new Error('The local Ruffle runtime did not load.');
    }
    const player = window.RufflePlayer.newest().createPlayer();
    container.appendChild(player);
    const api = typeof player.ruffle === 'function' ? player.ruffle() : player;
    status.hidden = true;
    console.log('[Basketball Legends] Starting Ruffle player...');
    await api.load({ url });
    console.log('[Basketball Legends] Ruffle load completed.');
    player.focus();
  } catch (error) {
    console.error('Basketball Legends failed to load:', error);
    container.replaceChildren();
    message.textContent = 'The game could not load. Please try again.';
    retry.hidden = false;
  }
}

window.addEventListener('DOMContentLoaded', () => {
  const start = () => embedSWF('./basketball_legends.swf', 'root');
  document.getElementById('retry').addEventListener('click', start);
  start();
});
