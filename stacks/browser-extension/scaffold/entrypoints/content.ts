// Content script. Use `ctx` for lifecycle-safe timers/listeners so they are torn
// down on invalidation (SPA navigation, extension reload). See patterns/content-scripts.md
export default defineContentScript({
  // Narrow this to the sites you actually need — see patterns/permissions.md
  matches: ['<all_urls>'],
  runAt: 'document_idle',
  main(ctx) {
    console.log('Content script loaded on', location.href);

    // ctx-bound listeners are cleaned up automatically when the script is invalidated.
    ctx.addEventListener(window, 'wxt:locationchange', ({ newUrl }) => {
      console.log('SPA navigation to', newUrl.href);
    });
  },
});
