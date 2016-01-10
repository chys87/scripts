// ==UserScript==
// @name Lofter
// @namespace http://chys.info
// @version 20160110
// @grant none
// @include http://*.lofter.com/*
// @include http://lofter.com/*
// ==/UserScript==

if (window.top == window.self) {

	let handler = function() {
		let nodes = document.querySelectorAll('a.rphlink.xtag');
		for (let i = 0; i < nodes.length; ++i) {
			let node = nodes[i];

			if (node.href && !node.href.endsWith('#')) {
				if (node.style.display == 'none') {
					node.style.display = '';
				}
			}

			let img = node.parentNode.querySelector('img');
			let url = img && img.src;
			if (url && url != node.href) {
				console.log('Converting a link to ' + url);
				node.href = url;
				if (node.style.display == 'none') {
					node.style.display = '';
				}
			}

		}
	};

	let observer = new MutationObserver(handler);

	observer.observe(document.querySelector('body'), {
		subtree: true,
		childList: true,
		attributes: true
	});

	// Handle existing links
	handler();
}