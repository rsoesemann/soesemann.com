# Website

Open [index.html](index.html) directly from disk. No server or API is needed.
The page shows all matching works, newest first. Content-type and topic filters
narrow the results; publisher and show names are plain labels on each card.

The activity wave shows busy and quiet periods. Its colors blend the topics of
nearby contributions. Hover for previews; click a year to scroll to its cards.
The wave never filters out other years. Open a card for saved text, slides and
recordings; media plays only after pressing Play.

`assets/` contains styles, JavaScript, publisher logos, previews and thumbnails.
`data/timeline-data.js` is generated from the library catalogue and includes private
notes. File links point to the sibling `library/` folder: keep the three product
folders together. This is not a public deployment bundle.

From the repository root, rebuild after changing library records:

```sh
uv run --project library/tooling python library/tooling/collect.py export
node --check website/assets/timeline.js
```

Check desktop and phone layouts through `file://`, filtering, previews, details
and local file links. Use an isolated temporary copy for tests; do not create real
review decisions or play sound. Keep document scrolling disabled and scroll the
inner page container so Safari can display the page reliably.
