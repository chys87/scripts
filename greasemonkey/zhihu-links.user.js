// ==UserScript==
// @name        Zhihu links
// @namespace   http://chys.info
// @description Misc zhihu improvements
// @include     http*://*.zhihu.com/*
// @include     http*://zhihu.com/*
// @version     1
// @grant       none
// ==/UserScript==

// Remove link.zhihu.com
{
  function handler() {
    let nodes = document.querySelectorAll('a[href*="link.zhihu.com"]');
    for (let node of nodes) {
      let href = node.href;
      if (/link\.zhihu\.com/.test(href)) {
        var new_href = decodeURIComponent(href.replace(/.*target=/, ''));
        console.log('Rewriting hyperlink:', href, new_href);
        node.href = new_href;
      }
    }
  };

  let observer = new MutationObserver(handler);
  observer.observe(document.body, {
    subtree: true,
    childList: true,
    attributes: true
  });

  handler();
}
