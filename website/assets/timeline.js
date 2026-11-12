const $ = (id) => document.getElementById(id);
const formats = ["All", "Conference talks", "Interviews", "Webinars", "Podcasts", "Blog & articles", "Courses", "Books", "Student work"];
const topicColors = {PMD:"violet", Craftsmanship:"amber", Agentforce:"blue", AI:"teal", DevOps:"rose"};
const waveColors = {PMD:[151,113,195], Craftsmanship:[213,159,78], AI:[64,164,139], DevOps:[196,113,148], Other:[151,165,183]};
let all = [], eras = [], lifeStages = [], selectedFormat = "All", selectedTopic = "All";
let previewTimer, previewKey = "";
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
function asset(item, field) { return new URL((window.PERSONA_DATA.asset_base ?? "../") + item.assets[field].path, location.href).href; }
function contentLink(item, label) {
  if (item.content_link) {
    const link = element("a", "", label || item.content_link.label + " ↗");
    link.href = item.content_link.url; link.target = "_blank"; link.rel = "noopener noreferrer";
    return link;
  }
  const onlineRecording = sources(item).find(source => source.kind === "video" || source.kind === "audio");
  if (onlineRecording) {
    const action = onlineRecording.context?.format === "Course trailer" ? "Watch trailer" : onlineRecording.kind === "audio" ? "Listen" : "Watch";
    return external(onlineRecording.url, label || action + " ↗");
  }
  if (item.kind === "course") return external(item.url, label || "View course ↗");
  const recording = mediaEntry(item);
  const presentation = Object.entries(item.assets).find(([, info]) => info.label === "View slides");
  const documentEntry = Object.entries(item.assets).find(([key, info]) =>
    key === "raw" && /\.pdf$/i.test(info.path) || info.label === "Original PDF");
  const flash = Object.entries(item.assets).find(([, info]) => /\.swf$/i.test(info.path));
  const local = recording || presentation || documentEntry || flash || (item.kind === "document" && item.assets.raw ? ["raw", item.assets.raw] : null);
  const online = sources(item).find(source => source.kind === "video" || source.kind === "audio" || new URL(source.url).hostname.endsWith(".goldcast.io")) || item;
  const action = recording ? (recording[1].type.startsWith("audio/") ? "Listen" : "Watch") : presentation ? "View slides" : documentEntry ? "Open PDF" : flash ? "Download Flash" : online.kind === "video" || new URL(online.url).hostname.endsWith(".goldcast.io") ? "Watch" : "Read";
  const link = external(online.url, label || action + " ↗");
  if (local) link.href = asset(item, local[0]);
  if (local === flash && flash) link.download = flash[1].path.split("/").at(-1);
  return link;
}

function dateValue(item) {
  const context = item.context || {};
  // A stated event date takes priority over an upload or page date.
  return context.event_date || context.when || context.published_at || item.date || "";
}
function isEarlyWork(item) { return Number(interval(dateValue(item))?.year) < 2004; }
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
function contentType(item) {
  const context = item.context || {}, format = `${item.kind} ${context.format || ""}`.toLowerCase();
  if (isEarlyWork(item)) return "Student work";
  if (item.kind === "book") return "Books";
  // Classify the work, not its attached slides, transcript or video file.
  if (/course/.test(format)) return "Courses";
  if (context.platform === "Conferences" || /conference/.test(format)) return "Conference talks";
  if (/podcast/.test(format) || ["SalesforceWay", "MVP Talk"].includes(context.platform)) return "Podcasts";
  if (/webinar|live coding|recorded presentation/.test(format)) return "Webinars";
  if (item.role === "interview" || /interview|transcript/.test(format)) return "Interviews";
  return "Blog & articles";
}
function typeLabel(item) {
  return {"Conference talks":"Conference talk", Interviews:"Interview", Webinars:"Webinar", Podcasts:"Podcast", "Blog & articles":"Article", Courses:"Course", Books:"Book", "Student work":"Student work"}[contentType(item)];
}
function publisher(item) {
  const platform = item.context?.platform;
  return platform && !["Conferences", "YouTube"].includes(platform) ? platform : item.brand?.name || place(item);
}
function people(item) { const who = item.context?.with_whom; return Array.isArray(who) ? who.join(", ") : who || "Not identified"; }
function place(item) { return item.context?.where || new URL(item.url).hostname; }
function sources(item) { return item.sources?.length ? item.sources : [item]; }
function mediaEntry(item) { return Object.entries(item.assets).find(([,a]) => /^(video|audio)\//.test(a.type)); }
function excerpt(item) {
  const lines = (item.text || "").split(/\n+/).map(line => line.trim()).filter(line => line.length > 65 && line !== item.title && !/^(cookie|privacy|subscribe|sign up)/i.test(line));
  const text = lines[0] || item.abstract || "";
  return text;
}
function workCard(item) {
  const card = element("article", "work"), context = item.context || {};
  card.id = `work-${item.id}`;
  const recording = mediaEntry(item);
  if (/^#[0-9a-f]{3,8}$/i.test(item.brand?.color || "")) card.style.setProperty("--publisher-color", item.brand.color);
  if (item.assets.thumbnail_path) {
    const cover = contentLink(item, ""); cover.className = "cover"; cover.textContent = "";
    cover.setAttribute("aria-label", `Open ${item.title}`);
    const image = element("img"); image.src = asset(item,"thumbnail_path"); image.alt = ""; image.loading = "lazy";
    cover.append(image);
    if (recording || sources(item).some(source => source.kind === "video")) cover.append(element("span","play-badge","▶"));
    card.append(cover);
  } else card.classList.add("work-text");
  const body = element("div","work-body"), brand = element("div","publisher");
  if (item.assets.brand_logo) { const logo = element("img"); logo.src = asset(item,"brand_logo"); logo.alt = ""; brand.append(logo); }
  brand.append(element("span","",item.card_label || publisher(item))); body.append(brand);
  const heading = element("h3"), title = contentLink(item, item.title);
  title.className = "work-title"; heading.append(title); body.append(heading);
  body.append(element("p","work-meta", interval(dateValue(item))?.year || "Undated"));
  const summary = context.summary || (item.kind === "article" && !recording ? excerpt(item) : "");
  if (summary) {
    const abstract = element("button", "work-summary", summary);
    abstract.type = "button";
    abstract.title = "Show full summary";
    let pinned = false;
    const expand = open => abstract.setAttribute("aria-expanded", String(open));
    expand(false);
    abstract.onpointerenter = event => { if (event.pointerType === "mouse") expand(true); };
    abstract.onpointerleave = () => expand(pinned);
    abstract.onclick = () => { pinned = !pinned; expand(pinned); };
    abstract.onkeydown = event => { if (event.key === "Escape") { pinned = false; expand(false); } };
    body.append(abstract);
  }
  const links = element("div","card-links");
  const action = contentLink(item); action.className = "open-work"; links.append(action);
  const page = sources(item).find(source => !["video", "audio"].includes(source.kind) && source.url !== action.href);
  if (page) links.append(external(page.url, page.kind === "course" ? "View course ↗" : "Original ↗"));
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
function yearSection(year, records) {
  records = [...records].sort((a, b) => (interval(dateValue(b))?.start || "").localeCompare(interval(dateValue(a))?.start || ""));
  const section = element("section", "year-group");
  section.id = `year-${year}`;
  const heading = element("div", "year-heading");
  const title = element("h2", "", year); title.tabIndex = -1;
  heading.append(title, element("span", "", `${records.length} ${records.length === 1 ? "work" : "works"}`));
  const cards = element("div", "cards");
  for (const item of records) cards.append(workCard(item));
  section.append(heading, cards);
  return section;
}
function jumpToYear(year) {
  hidePreview();
  const section = $(`year-${year}`), scroller = $("page-scroll");
  if (!section) return;
  section.querySelector("h2").focus({preventScroll:true});
  scroller.scrollTo({top: scroller.scrollTop + section.getBoundingClientRect().top - scroller.getBoundingClientRect().top - 16,
    behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth"});
}
function waveTopic(item) {
  const topics = item.context?.topics || [];
  // Specific subjects take precedence over the broader Craftsmanship tag.
  if (topics.includes("PMD")) return "PMD";
  if (topics.some(topic => ["AI", "Agentforce"].includes(topic))) return "AI";
  return ["Craftsmanship", "DevOps"].find(topic => topics.includes(topic)) || "Other";
}
function render() {
  hidePreview();
  const query = $("search").value.trim().toLowerCase().replace(/\s+/g, " ");
  const included = all.filter(item => item.review?.decision !== "ignore" && ($("early-years").checked || !isEarlyWork(item)));
  const visible = included.filter(item =>
    (selectedFormat === "All" || contentType(item) === selectedFormat) &&
    (selectedTopic === "All" || (item.context?.topics || []).includes(selectedTopic)) &&
    `${item.title} ${item.text} ${item.abstract || ""} ${item.context?.summary || ""} ${(item.context?.topics || []).join(" ")} ${item.context?.platform || ""} ${sources(item).map(source => source.text || "").join(" ")} ${place(item)} ${people(item)} ${item.context?.format || ""}`.toLowerCase().replace(/\s+/g, " ").includes(query));
  const groups = new Map();
  for (const item of visible) {
    const year = interval(dateValue(item))?.year || "Undated";
    if (!groups.has(year)) groups.set(year, []);
    groups.get(year).push(item);
  }
  // Early years controls the range; topic and text filters keep that range stable.
  const datedYears = included.map(item => Number(interval(dateValue(item))?.year)).filter(Number.isFinite);
  const years = [];
  if (datedYears.length) for (let year = Math.min(...datedYears); year <= Math.max(...datedYears); year++) years.push(String(year));
  if (included.some(item => !interval(dateValue(item)))) years.push("Undated");
  const monthly = new Map();
  for (const year of years) {
    const bins = Array.from({length:12}, () => ({count:0, topics:{}}));
    for (const item of groups.get(year) || []) {
      const date = interval(dateValue(item));
      if (!date) continue;
      const topic = waveTopic(item), weight = date.precision === "year" ? 1 / 12 : 1;
      const targets = date.precision === "year" ? bins : [bins[Number(date.start.slice(5,7)) - 1]];
      // Year-only dates contribute across the year, without inventing a month.
      for (const bin of targets) { bin.count += weight; bin.topics[topic] = (bin.topics[topic] || 0) + weight; }
    }
    monthly.set(year, bins);
  }
  $("years").replaceChildren(activityWave([...monthly.values()].flat()));
  $("wave-legend").replaceChildren();
  for (const [topic, color] of Object.entries(waveColors)) {
    if (!visible.some(item => waveTopic(item) === topic)) continue;
    const label = element("span", "wave-topic", topic === "AI" ? "AI / Agentforce" : topic === "Other" ? "Other topics" : topic);
    label.style.setProperty("--topic-color", `rgb(${color.join(",")})`); $("wave-legend").append(label);
  }
  for (const year of years) {
    const count = groups.get(year)?.length || 0;
    const button = element("button", "year-button");
    button.type = "button";
    button.dataset.year = year;
    button.setAttribute("aria-label", `${year}: ${count} saved ${count === 1 ? "work" : "works"}`);
    if (count) button.setAttribute("aria-controls", `year-${year}`);
    button.setAttribute("aria-disabled", String(!count));
    button.setAttribute("aria-expanded", "false");
    button.append(element("span", "year-label", year));
    const records = groups.get(year) || [];
    button.onpointermove = event => {
      if (event.pointerType !== "mouse") return;
      const rect = button.getBoundingClientRect();
      const month = Math.min(11, Math.max(0, Math.floor((event.clientX - rect.left) / rect.width * 12)));
      showPreview(year, records, button, month);
    };
    button.onpointerleave = delayPreviewClose;
    button.onfocus = () => showPreview(year, records, button);
    button.onclick = () => jumpToYear(year);
    button.onkeydown = event => {
      if (event.key === "ArrowDown") {
        event.preventDefault(); showPreview(year, records, button);
        $("year-preview").querySelector("a, button")?.focus({preventScroll:true});
      }
      const buttons = [...$("years").querySelectorAll(".year-button")], index = buttons.indexOf(button);
      const target = event.key === "ArrowRight" ? Math.min(index + 1, buttons.length - 1) : event.key === "ArrowLeft" ? Math.max(index - 1, 0) : event.key === "Home" ? 0 : event.key === "End" ? buttons.length - 1 : null;
      if (target !== null) { event.preventDefault(); buttons[target].focus(); }
    };
    $("years").append(button);
  }
  const minimumWidth = `${years.length * 68}px`;
  $("years").style.minWidth = minimumWidth;
  $("career-bands").style.minWidth = minimumWidth;
  employerBands(datedYears.length ? Math.min(...datedYears) : null, years.length, datedYears.length ? Math.max(...datedYears) : null);
  const populated = years.filter(year => groups.has(year) && year !== "Undated").reverse();
  if (groups.has("Undated")) populated.push("Undated");
  $("timeline").replaceChildren(...populated.map(year => yearSection(year, groups.get(year))));
  $("results").textContent = `${visible.length} ${visible.length === 1 ? "work" : "works"} · all years`;
  $("empty").hidden = !!visible.length;
}
function activityWave(months) {
  const width = months.length * 10, baseline = 80;
  // A broad density curve conveys activity without discrete bars.
  const density = Array.from({length: months.length * 4 + 1}, (_, step) =>
    months.reduce((sum, bin, month) => sum + bin.count * Math.exp(-.5 * ((step / 4 - month - .5) / 1.4) ** 2), 0));
  const maximum = Math.max(1, ...density);
  const line = density.map((value, index) => `${index ? "L" : "M"}${index * 2.5},${(baseline - value / maximum * 66).toFixed(2)}`).join(" ");
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("class", "activity-wave"); svg.setAttribute("viewBox", `0 0 ${width} 84`);
  svg.setAttribute("preserveAspectRatio", "none"); svg.setAttribute("aria-hidden", "true");
  const stops = months.map((_, position) => {
    const rgb = [0,0,0]; let total = 0;
    months.forEach((bin, month) => {
      const nearby = Math.exp(-.5 * ((position - month) / 5) ** 2);
      for (const [topic, amount] of Object.entries(bin.topics)) {
        const weight = amount * nearby; total += weight;
        waveColors[topic].forEach((channel, index) => { rgb[index] += channel * weight; });
      }
    });
    const color = total ? rgb.map(channel => Math.round(channel / total)) : waveColors.Other;
    return `<stop offset="${position / Math.max(1, months.length - 1)}" stop-color="rgb(${color.join(",")})"/>`;
  }).join("");
  svg.innerHTML = `<defs><linearGradient id="wave-topics">${stops}</linearGradient></defs>
    <path d="${line} L${width},84 L0,84 Z" fill="url(#wave-topics)" fill-opacity=".3"/>
    <path d="${line}" fill="none" stroke="url(#wave-topics)" stroke-width="1.6" vector-effect="non-scaling-stroke"/>`;
  return svg;
}
function hidePreview() {
  clearTimeout(previewTimer); previewKey = "";
  $("year-preview").hidden = true;
  for (const button of $("years").querySelectorAll(".year-button")) button.setAttribute("aria-expanded", "false");
}
function delayPreviewClose() { previewTimer = setTimeout(hidePreview, 250); }
function showPreview(year, records, anchor, month = null) {
  clearTimeout(previewTimer);
  const inMonth = month === null ? [] : records.filter(item => {
    const date = interval(dateValue(item));
    return date && date.precision !== "year" && Number(date.start.slice(5,7)) === month + 1;
  });
  const key = `${year}-${inMonth.length ? month : "all"}`;
  if (previewKey === key) return;
  hidePreview(); previewKey = key;
  const preview = $("year-preview"), shown = inMonth.length ? inMonth : records;
  const label = inMonth.length ? `${new Date(2000, month, 1).toLocaleDateString("en-GB", {month:"long"})} ${year}` : year;
  const heading = element("div", "preview-heading");
  heading.append(element("strong", "", label), element("span", "", `${shown.length} ${shown.length === 1 ? "work" : "works"}`));
  preview.replaceChildren(heading);
  for (const item of shown.slice(0, 4)) {
    const card = contentLink(item, ""); card.className = "mini-work"; card.textContent = "";
    const field = item.assets.thumbnail_path ? "thumbnail_path" : item.assets.brand_logo ? "brand_logo" : null;
    if (field) {
      const image = element("img", field === "brand_logo" ? "mini-logo" : "");
      image.src = asset(item, field); image.alt = ""; card.append(image);
    } else card.append(element("span", "mini-placeholder", typeLabel(item)));
    const text = element("span", "mini-copy");
    text.append(element("span", "mini-publisher", publisher(item)), element("strong", "", item.title), element("span", "mini-date", when(item)));
    card.append(text); preview.append(card);
  }
  if (!shown.length) preview.append(element("p", "preview-empty", "No saved work for this year with these filters."));
  if (records.length) {
    const browse = element("button", "preview-browse", `Jump to ${year} →`);
    browse.type = "button"; browse.onclick = () => jumpToYear(year); preview.append(browse);
  }
  preview.hidden = false;
  preview.setAttribute("aria-label", `${label}: work previews`); anchor.setAttribute("aria-expanded", "true");
  const rect = anchor.getBoundingClientRect(), section = anchor.closest(".timeline-section").getBoundingClientRect();
  preview.style.left = `${Math.max(12, Math.min(rect.left + rect.width / 2 - preview.offsetWidth / 2, innerWidth - preview.offsetWidth - 12))}px`;
  preview.style.top = `${Math.max(12, Math.min(section.bottom + 8, innerHeight - preview.offsetHeight - 12))}px`;
}
function career(data) {
  eras = (Array.isArray(data) ? data : data.eras || []).filter(era => all.some(item => matchesEra(item,era)));
  lifeStages = data.life_stages || [];
}
function employerBands(firstYear, columns, lastYear) {
  const container = $("career-bands"); container.replaceChildren();
  if (firstYear === null) { container.hidden = true; return; }
  container.hidden = false;
  const totalMonths = columns * 12, axisEnd = (lastYear - firstYear + 1) * 12;
  const monthIndex = value => (Number(value.slice(0,4)) - firstYear) * 12 + Number(value.slice(5,7) || 1) - 1;
  // Robert confirmed these consecutive periods; each new job ends the previous band.
  const periods = [
    ...lifeStages.map(stage => ({
      name:stage.name, className:stage.kind, start:stage.start ? monthIndex(stage.start) : 0, end:monthIndex(stage.end)})),
    {name:"Up2Go", className:"up2go", start:monthIndex((eras.find(era => era.name.startsWith("Up2Go"))?.start || "2012") + "-01")},
    {name:"Copado", className:"copado", start:monthIndex("2020-11")},
    {name:"Aquiva", className:"aquiva", start:monthIndex("2022-03")},
  ];
  periods.forEach((period,index) => {
    const left = Math.max(0,period.start), right = Math.min(axisEnd,period.end ?? periods[index + 1]?.start ?? axisEnd);
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
    button.dataset.tone = id === "topic-filters" ? topicColors[label] || "blue" : "blue";
    button.dataset.value = label;
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
  const included = all.filter(item => item.review?.decision !== "ignore" && ($("early-years").checked || !isEarlyWork(item)));
  const topics = [...new Set(included.flatMap(item => item.context?.topics || []))].filter(topic => typeof topic === "string" && topic);
  const preferred = ["PMD", "Craftsmanship", "Agentforce", "AI", "DevOps"];
  topics.sort((a, b) => {
    const first = preferred.includes(a) ? preferred.indexOf(a) : preferred.length;
    const second = preferred.includes(b) ? preferred.indexOf(b) : preferred.length;
    return first - second || a.localeCompare(b);
  });
  pills("filters", formats.filter(label => label === "All" || included.some(item => contentType(item) === label)), label => { selectedFormat = label; });
  pills("topic-filters", ["All", ...topics], label => { selectedTopic = label; });
}
async function load() {
  try {
    if (!window.PERSONA_DATA) throw new Error("Offline catalogue missing. Run the library export to rebuild it.");
    all = window.PERSONA_DATA.items; career(window.PERSONA_DATA.career);
    $("early-years-count").textContent = `${all.filter(isEarlyWork).length} works`;
    $("early-years").checked = new URLSearchParams(location.search).get("early") === "1";
    contentFilters();
    render();
    const linkedId = new URLSearchParams(location.search).get("id");
    const linkedWork = all.find(item => item.id === linkedId || sources(item).some(source => source.id === linkedId));
    if (linkedWork) {
      if (isEarlyWork(linkedWork)) { $("early-years").checked = true; contentFilters(); render(); }
      const link = $(`work-${linkedWork.id}`)?.querySelector(".work-title");
      link?.scrollIntoView({block:"center"}); link?.focus({preventScroll:true});
    }
  } catch(error) { $("error").textContent=error.message; $("error").hidden=false; }
}
$("search").oninput=render;
$("early-years").onchange=()=>{ selectedFormat = "All"; selectedTopic = "All"; contentFilters(); render(); };
$("year-preview").onpointerenter = () => clearTimeout(previewTimer);
$("year-preview").onpointerleave = delayPreviewClose;
document.addEventListener("keydown", event => {
  if (event.key !== "Escape") return;
  if ($("year-preview").contains(document.activeElement)) $("years").querySelector('[aria-expanded="true"]')?.focus({preventScroll:true});
  hidePreview();
});
document.addEventListener("focusin", event => { if (!event.target.closest("#years, #year-preview")) hidePreview(); });
document.addEventListener("pointerdown", event => { if (!event.target.closest("#years, #year-preview")) hidePreview(); });
$("page-scroll").addEventListener("scroll", hidePreview, {passive:true});
$("years").parentElement.addEventListener("scroll", hidePreview, {passive:true});
window.addEventListener("resize", hidePreview);
load();
