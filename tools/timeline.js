const $ = (id) => document.getElementById(id);
const formats = ["All", "Interviews", "Courses", "Videos", "Text", "Slides", "Conferences", "Podcasts"];
let all = [], eras = [], selectedFormat = "All", selectedTopic = "All", selectedPlatform = "All", selectedYear = null;
function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function external(url, label) {
  try {
    const parsed = new URL(url);
    if (!["http:", "https:"].includes(parsed.protocol)) return null;
    const link = element("a", "", label);
    link.href = parsed.href; link.target = "_blank"; link.rel = "noopener noreferrer";
    return link;
  } catch { return null; }
}
function asset(item, field) { return new URL(item.assets[field].path, location.href).href; }

function dateValue(item) {
  const context = item.context || {};
  // A stated event date takes priority over an upload or page date.
  return context.event_date || context.when || context.published_at || item.date || "";
}
function interval(value) {
  const match = String(value || "").match(/^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?(?=$|[^\d])/);
  if (!match) return null;
  const year = +match[1], month = match[2] ? +match[2] : null, day = match[3] ? +match[3] : null;
  return {start: `${year}-${String(month || 1).padStart(2,"0")}-${String(day || 1).padStart(2,"0")}`,
    end: `${year}-${String(month || 12).padStart(2,"0")}-${String(day || (month ? new Date(year,month,0).getDate() : 31)).padStart(2,"0")}`,
    year: String(year), precision: day ? "day" : month ? "month" : "year"};
}
function when(item) {
  const context = item.context || {}, value = dateValue(item);
  if (!value || /^(unknown|not established)$/i.test(value)) return "Date not established";
  let label = value;
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) label = new Date(value + "T12:00:00Z").toLocaleDateString("en-GB", {day:"numeric",month:"short",year:"numeric",timeZone:"UTC"});
  return `${context.event_date ? "Event" : context.date_label || "Page date"}: ${label}`;
}
function categories(item) {
  const sources = item.sources || [];
  const value = `${item.kind} ${item.context?.format || ""}`.toLowerCase(), result = [];
  if (item.role === "interview" || /interview|transcript/.test(value)) result.push("Interviews");
  if (/course/.test(value)) result.push("Courses");
  if (!/slides/.test(value) && /video|recorded|presentation/.test(value)) result.push("Videos");
  if (/article|text|profile|translation|book/.test(value)) result.push("Text");
  if (/slides/.test(value)) result.push("Slides");
  if (/\bconference\b|\bdreamforce\b|\w*dreamin\b|\bsforce\b|\btdx\b|\btrailblazer\b/.test(value + " " + (item.context?.where || "").toLowerCase())) result.push("Conferences");
  if (/podcast|audio/.test(value)) result.push("Podcasts");
  for (const source of sources) for (const category of categories({...source, sources: []})) if (!result.includes(category)) result.push(category);
  if (Object.values(item.assets || {}).some(info => info.slide !== undefined) && !result.includes("Slides")) result.push("Slides");
  return result;
}
function people(item) { const who = item.context?.with_whom; return Array.isArray(who) ? who.join(", ") : who || "Not identified"; }
function place(item) { return item.context?.where || new URL(item.url).hostname; }
function sources(item) { return item.sources?.length ? item.sources : [item]; }
function assetSource(item, info) { return sources(item).find(source => source.id === info.source_id || Object.values(source.assets || {}).some(a => a.path === info.path)) || item; }
function mediaEntry(item) { return Object.entries(item.assets).find(([,a]) => /^(video|audio)\//.test(a.type)); }
function slides(item) { return Object.entries(item.assets).filter(([,info]) => info.slide !== undefined && info.type.startsWith("image/")); }
function mediaLabel(item, info) {
  const source = assetSource(item, info), description = `${source.title} ${source.context?.format || ""} ${info.label || ""}`;
  return /trailer|preview/i.test(description) ? "Course trailer" : info.type.startsWith("audio/") ? "Audio recording" : "Video recording";
}
function byline(item) {
  return item.role === "coauthored" ? "Robert Sösemann · coauthored" : item.role === "authored" ? "By Robert Sösemann" : `From ${place(item)}`;
}
function excerpt(item) {
  const lines = (item.text || "").split(/\n+/).map(line => line.trim()).filter(line => line.length > 65 && line !== item.title && !/^(cookie|privacy|subscribe|sign up)/i.test(line));
  const text = lines[0] || item.abstract || "";
  return text.length > 250 ? text.slice(0, 247).trimEnd() + "…" : text;
}
function addLinks(container, item) {
  const source = external(item.url, "Original ↗"); if (source) container.append(source);
  const textAsset = Object.entries(item.assets).find(([field,info]) => info.type.startsWith("text/") || /(?:^|[/:_])text_path$/.test(field) || /\.(txt|md)$/.test(info.path));
  if (textAsset) { const link = element("a", "", "Download text ↓"); link.href = asset(item,textAsset[0]); container.append(link); }
  for (const related of [...(item.context?.related_links || []), ...(item.context?.links || [])]) { const link = external(related.url, related.label || "Related source ↗"); if (link) container.append(link); }
}
function sourceDetails(item) {
  const container = $("reader-sources"); container.replaceChildren();
  container.append(element("h3", "", `Sources for this work · ${sources(item).length}`));
  for (const source of sources(item)) {
    const details = element("details", "source-detail"), summary = element("summary", "", `${source.context?.format || source.kind} · ${source.title}`);
    const attribution = element("p", "source-attribution", `${place(source)} · ${byline(source)} · ${when(source)}`);
    const link = external(source.url, "Open this source ↗");
    details.append(summary,attribution); if (link) details.append(link);
    for (const related of [...(source.context?.related_links || []), ...(source.context?.links || [])]) { const relatedLink=external(related.url,related.label || "Related source ↗"); if(relatedLink) details.append(relatedLink); }
    if (source.context?.access) details.append(element("p", "source-attribution", source.context.access));
    if (source.media_error || source.warning) details.append(element("p", "source-attribution", source.media_error || source.warning));
    if (sources(item).length > 1) details.append(element("pre", "", source.text || "No text saved from this source."));
    container.append(details);
  }
  const notes = item.source_reviews || [];
  for (const note of notes.filter(note => note.note)) {
    const block = element("div", "source-note"); block.append(element("strong", "", `Your note · ${note.title || note.source_id} · ${note.decision}`), element("p", "", note.note)); container.append(block);
  }
}
function openItem(item) {
  $("reader-title").textContent = item.title;
  $("reader-format").textContent = `${item.context?.format || item.kind} · ${sources(item).length} ${sources(item).length === 1 ? "source" : "sources"}`;
  $("reader-context").textContent = `${place(item)} · ${when(item)} · With: ${people(item)}`;
  const summary = item.context?.summary || item.abstract || "";
  $("reader-abstract").hidden = !summary; $("reader-abstract").textContent = summary;
  $("reader-media").replaceChildren();
  if (item.recording?.summary) $("reader-media").append(element("p", "source-attribution", [item.recording.summary, item.recording.reason].filter(Boolean).join(" · ")));
  const recordings = Object.entries(item.assets).filter(([,info]) => /^(video|audio)\//.test(info.type));
  const videoSources = new Set(recordings.filter(([,info]) => info.type.startsWith("video/")).map(([,info]) => info.source_id));
  for (const [field, info] of recordings.filter(([,info]) => info.type.startsWith("video/") || !videoSources.has(info.source_id))) {
    const section = element("section", "recording"); section.append(element("h3", "", mediaLabel(item,info)));
    const player = element(info.type.startsWith("video/") ? "video" : "audio"); player.controls = true; player.preload = "none"; player.src = asset(item,field);
    if (item.assets.thumbnail_path && info.type.startsWith("video/")) player.poster = asset(item,"thumbnail_path");
    section.append(player);
    const source = assetSource(item,info);
    if (source.id !== item.id) section.append(element("p","source-attribution",source.title));
    $("reader-media").append(section);
  }
  if (slides(item).length) {
    const deck = element("details", "slide-deck"), summary = element("summary", "", `Presentation slides · ${slides(item).length} saved`); deck.append(summary);
    for (const [field, info] of slides(item)) {
      const figure = element("figure", "slide"), image = element("img"); image.src = asset(item,field); image.alt = `Slide ${info.slide}`; image.loading = "lazy";
      const download = element("a", "", `Slide ${info.slide} ↓`); download.href = asset(item,field); download.download = `slide-${info.slide}`; figure.append(image,download); deck.append(figure);
    }
    deck.open = !mediaEntry(item); $("reader-media").append(deck);
  }
  $("reader-links").replaceChildren(); addLinks($("reader-links"),item);
  for (const [field, info] of recordings.filter(([,info]) => info.type.startsWith("audio/") && videoSources.has(info.source_id))) {
    const link = element("a", "", "Audio file ↓"); link.href = asset(item,field); link.download = info.path.split("/").at(-1); $("reader-links").append(link);
  }
  $("reader-text").hidden = sources(item).length > 1;
  $("reader-text").textContent = sources(item).length === 1 ? item.text || item.context?.access || "No saved text yet." : "";
  sourceDetails(item);
  $("reader").showModal(); $("reader").querySelector(".reader-scroll").scrollTop = 0;
}
function workCard(item) {
  const card = element("article", "work"), context = item.context || {};
  const recording = mediaEntry(item);
  const open = () => openItem(item);
  if (/^#[0-9a-f]{3,8}$/i.test(item.brand?.color || "")) card.style.setProperty("--publisher-color", item.brand.color);
  if (item.assets.thumbnail_path) {
    const cover = element("button", "cover"); cover.type = "button";
    cover.setAttribute("aria-label", `Open ${item.title}`); cover.onclick = open;
    const image = element("img"); image.src = asset(item,"thumbnail_path"); image.alt = ""; image.loading = "lazy";
    cover.append(image);
    if (recording) cover.append(element("span","play-badge","▶"));
    card.append(cover);
  } else card.classList.add("work-text");
  const body = element("div","work-body"), brand = element("div","publisher");
  if (item.assets.brand_logo) { const logo = element("img"); logo.src = asset(item,"brand_logo"); logo.alt = ""; brand.append(logo); }
  brand.append(element("span","",item.brand?.name || place(item))); body.append(brand);
  const heading = element("h3"), title = element("button","work-title",item.title);
  title.type = "button"; title.onclick = open; heading.append(title); body.append(heading);
  body.append(element("p","work-meta",`${context.format || item.kind} · ${when(item)}`));
  const summary = context.summary || (item.kind === "article" && !recording ? excerpt(item) : "");
  if (summary) body.append(element("p","work-summary",summary));
  if (item.recording?.missing) body.append(element("p","recording-status",item.recording.summary));
  const links = element("div","card-links");
  let label = recording ? (recording[1].type.startsWith("audio/") ? "Listen" : "Watch") : slides(item).length ? "View slides" : item.text ? "Read" : "Open";
  if (recording && mediaLabel(item,recording[1]) === "Course trailer") label = "Watch trailer";
  const action = element("button","open-work",label + " →"); action.type = "button"; action.onclick = open; links.append(action);
  const original = external(item.url,"Original ↗"); if (original) links.append(original);
  body.append(links); card.append(body); return card;
}
function matchesEra(item, era) {
  const employer = item.context?.employer;
  if (employer) {
    const known = (Array.isArray(employer) ? employer : [employer]).map(name => String(name).toLowerCase());
    if (!known.some(name => name === era.name.toLowerCase() || name.startsWith(era.name.toLowerCase() + " "))) return false;
  }
  const date = interval(dateValue(item)), start = interval(era.start), end = interval(era.end);
  return !!(date && start && date.end >= start.start && (!end || date.start <= end.end));
}
function showYear(year, groups) {
  selectedYear = year;
  for (const button of $("years").children) button.setAttribute("aria-pressed", String(button.dataset.year === year));
  const records = [...(groups.get(year) || [])].sort((a, b) => (interval(dateValue(a))?.start || "").localeCompare(interval(dateValue(b))?.start || ""));
  const section = element("section", "year-group");
  const heading = element("div", "year-heading");
  heading.append(element("h2", "", year), element("span", "", `${records.length} ${records.length === 1 ? "work" : "works"}`));
  const cards = element("div", "cards");
  for (const item of records) cards.append(workCard(item));
  section.append(heading, cards);
  $("timeline").replaceChildren(section);
  $("results").textContent = `${year}: ${records.length} archived ${records.length === 1 ? "work" : "works"}`;
  $("empty").hidden = !!records.length;
  $("empty").textContent = year === "Undated" ? "No undated work matches these filters." : `No archived work matches ${year}.`;
}
function render() {
  const query = $("search").value.trim().toLowerCase().replace(/\s+/g, " ");
  const visible = all.filter(item => item.review.decision !== "ignore" &&
    (selectedFormat === "All" || categories(item).includes(selectedFormat)) &&
    (selectedTopic === "All" || (item.context?.topics || []).includes(selectedTopic)) &&
    (selectedPlatform === "All" || item.context?.platform === selectedPlatform) &&
    `${item.title} ${item.text} ${item.abstract || ""} ${item.context?.summary || ""} ${(item.context?.topics || []).join(" ")} ${item.context?.platform || ""} ${sources(item).map(source => source.text || "").join(" ")} ${place(item)} ${people(item)} ${item.context?.format || ""}`.toLowerCase().replace(/\s+/g, " ").includes(query));
  const groups = new Map();
  for (const item of visible) {
    const year = interval(dateValue(item))?.year || "Undated";
    if (!groups.has(year)) groups.set(year, []);
    groups.get(year).push(item);
  }
  // Keep the full archive's year range while filtering, including years with no work.
  const datedYears = all.map(item => Number(interval(dateValue(item))?.year)).filter(Number.isFinite);
  const years = [];
  if (datedYears.length) for (let year = Math.min(...datedYears); year <= Math.max(...datedYears); year++) years.push(String(year));
  if (all.some(item => !interval(dateValue(item)))) years.push("Undated");
  if (!years.includes(selectedYear) || !groups.has(selectedYear)) {
    const populatedYears = years.filter(year => groups.has(year));
    selectedYear = populatedYears.filter(year => year !== "Undated").at(-1) || populatedYears.at(-1) || years.at(-1);
  }
  const monthly = new Map();
  for (const year of years) {
    const bins = Array(12).fill(0);
    for (const item of groups.get(year) || []) {
      const date = interval(dateValue(item));
      if (date && date.precision !== "year") bins[Number(date.start.slice(5,7)) - 1]++;
    }
    monthly.set(year, bins);
  }
  const maximum = Math.max(1, ...[...monthly.values()].flat());
  $("years").replaceChildren();
  for (const year of years) {
    const count = groups.get(year)?.length || 0;
    const button = element("button", "year-button");
    button.type = "button";
    button.dataset.year = year;
    button.setAttribute("aria-label", `${year}: ${count} archived ${count === 1 ? "work" : "works"}`);
    button.setAttribute("aria-controls", "timeline");
    const bins = monthly.get(year), unplaced = count - bins.reduce((total, value) => total + value, 0);
    const chart = element("span", "year-chart");
    chart.setAttribute("aria-hidden", "true");
    const months = element("span", "month-bins");
    bins.forEach((amount, index) => {
      const bar = element("span", "month-bar");
      bar.style.height = `${amount / maximum * 64}px`;
      bar.title = `${new Date(2000,index,1).toLocaleDateString("en-GB",{month:"short"})} ${year}: ${amount} ${amount === 1 ? "work" : "works"}`;
      months.append(bar);
    });
    chart.append(element("span", "year-count", String(count)), months);
    if (unplaced) button.setAttribute("aria-label", `${year}: ${count} archived works; ${unplaced} without a known month`);
    button.append(chart, element("span", "year-label", year));
    const select = () => { if (selectedYear !== year) showYear(year, groups); };
    button.onpointerenter = event => { if (event.pointerType === "mouse") select(); };
    button.onfocus = select;
    button.onclick = select;
    button.onkeydown = event => {
      const buttons = [...$("years").children], index = buttons.indexOf(button);
      const target = event.key === "ArrowRight" ? Math.min(index + 1, buttons.length - 1) : event.key === "ArrowLeft" ? Math.max(index - 1, 0) : event.key === "Home" ? 0 : event.key === "End" ? buttons.length - 1 : null;
      if (target !== null) { event.preventDefault(); buttons[target].focus(); }
    };
    $("years").append(button);
  }
  const minimumWidth = `${years.length * 68}px`;
  $("years").style.minWidth = minimumWidth;
  $("career-bands").style.minWidth = minimumWidth;
  employerBands(datedYears.length ? Math.min(...datedYears) : null, years.length, datedYears.length ? Math.max(...datedYears) : null);
  showYear(selectedYear || "Undated", groups);
  // On narrow screens start with the selected year visible; the strip still reads left to right.
  const selected = [...$("years").children].find(button => button.dataset.year === selectedYear);
  const axis = $("years").parentElement;
  if (selected) axis.scrollLeft = Math.max(0, selected.offsetLeft - $("years").offsetLeft - axis.clientWidth + selected.offsetWidth);
}
function career(data) {
  eras = (Array.isArray(data) ? data : data.eras || []).filter(era => all.some(item => matchesEra(item,era)));
}
function employerBands(firstYear, columns, lastYear) {
  const container = $("career-bands"); container.replaceChildren();
  if (firstYear === null) { container.hidden = true; return; }
  container.hidden = false;
  const totalMonths = columns * 12, axisEnd = (lastYear - firstYear + 1) * 12;
  const monthIndex = value => (Number(value.slice(0,4)) - firstYear) * 12 + Number(value.slice(5,7)) - 1;
  // Robert confirmed these consecutive periods; each new job ends the previous band.
  const periods = [
    {name:"Up2Go", className:"up2go", start:0},
    {name:"Copado", className:"copado", start:monthIndex("2020-11")},
    {name:"Aquiva", className:"aquiva", start:monthIndex("2022-03")},
  ];
  periods.forEach((period,index) => {
    const left = Math.max(0,period.start), right = Math.min(axisEnd,periods[index + 1]?.start ?? axisEnd);
    if (right <= left) return;
    const band = element("div", `employer-band ${period.className}`, period.name);
    band.style.left = `${left / totalMonths * 100}%`;
    band.style.width = `${(right-left) / totalMonths * 100}%`;
    container.append(band);
  });
  container.style.height = "26px";
}
function pills(id, labels, select) {
  const container = $(id);
  container.replaceChildren();
  for (const label of labels) {
    const button = element("button", "filter", label);
    const topicColors = {PMD:"violet", Craftsmanship:"amber", Agentforce:"blue", AI:"teal", DevOps:"rose"};
    const platformColors = {Aquiva:"violet", "Salesforce Ben":"blue", SalesforceWay:"teal", Conferences:"amber", Pluralsight:"rose", Hutte:"violet"};
    button.dataset.tone = id === "topic-filters" ? topicColors[label] || "blue" : id === "platform-filters" ? platformColors[label] || "blue" : "blue";
    if (id === "platform-filters" && label !== "All" && label !== "Conferences") {
      const normalize = name => String(name || "").toLowerCase().replace(/[^a-z0-9]/g, "");
      const publisher = all.find(item => item.context?.platform === label && item.assets.brand_logo &&
        (normalize(item.brand?.name) === normalize(label) || normalize((item.brand?.domain || "").replace(/^www\./, "").split(".")[0]) === normalize(label)));
      if (publisher) { const logo = element("img", "pill-logo"); logo.src = asset(publisher,"brand_logo"); logo.alt = ""; button.prepend(logo); }
    }
    button.type = "button";
    button.setAttribute("aria-pressed", String(label === "All"));
    button.onclick = () => {
      select(label);
      for (const pill of container.children) pill.setAttribute("aria-pressed", String(pill === button));
      render();
    };
    container.append(button);
  }
}
function contentFilters() {
  const topics = [...new Set(all.flatMap(item => item.context?.topics || []))].filter(topic => typeof topic === "string" && topic);
  const preferred = ["PMD", "Craftsmanship", "Agentforce", "AI", "DevOps"];
  topics.sort((a, b) => {
    const first = preferred.includes(a) ? preferred.indexOf(a) : preferred.length;
    const second = preferred.includes(b) ? preferred.indexOf(b) : preferred.length;
    return first - second || a.localeCompare(b);
  });
  const platforms = [...new Set(all.map(item => item.context?.platform))].filter(platform => typeof platform === "string" && platform).sort((a, b) => a.localeCompare(b));
  pills("filters", formats, label => { selectedFormat = label; });
  pills("topic-filters", ["All", ...topics], label => { selectedTopic = label; });
  pills("platform-filters", ["All", ...platforms], label => { selectedPlatform = label; });
}
async function load() {
  try {
    if (!window.PERSONA_DATA) throw new Error("Offline catalogue missing. Run the archive export to rebuild it.");
    all = window.PERSONA_DATA.items; career(window.PERSONA_DATA.career);
    contentFilters();
    render();
    const linkedId = new URLSearchParams(location.search).get("id");
    const linkedWork = all.find(item => item.id === linkedId || sources(item).some(source => source.id === linkedId));
    if (linkedWork) openItem(linkedWork);
  } catch(error) { $("error").textContent=error.message; $("error").hidden=false; }
}
$("search").oninput=render;
$("close-reader").onclick=()=>$("reader").close();
$("reader").addEventListener("close",()=>{ for(const media of $("reader-media").querySelectorAll("video,audio"))media.pause(); });
load();
