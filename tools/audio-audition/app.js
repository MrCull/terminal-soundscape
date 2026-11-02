const STORAGE_KEY = "terminal-soundscape-audio-review-v1";
const list = document.querySelector("#recordings");
const summary = document.querySelector("#summary");
const errorBox = document.querySelector("#error");
const searchBox = document.querySelector("#search");
const collectionBox = document.querySelector("#collection");
const stateBox = document.querySelector("#state");

let recordings = [];
let reviews = readReviews();

function readReviews() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}"); }
  catch { return {}; }
}

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}

function option(value, label) {
  const item = document.createElement("option");
  item.value = value;
  item.textContent = label;
  return item;
}

function formatTime(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
  const total = Math.floor(seconds);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const remainder = total % 60;
  return hours ? `${hours}:${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`
    : `${minutes}:${String(remainder).padStart(2, "0")}`;
}

async function load() {
  try {
    const [currentResponse, firstResponse, previewResponse, tagsResponse] = await Promise.all([
      fetch("/manifest.json"),
      fetch("/first-collection/manifest.json"),
      fetch("/first-collection/browser-previews/preview-manifest.json"),
      fetch("/docs/generated/audio-event-tags.json")
    ]);
    if (![currentResponse, firstResponse, previewResponse].every(response => response.ok)) {
      throw new Error("Could not read the repository manifests. Start the server from the repository root.");
    }
    const [current, first, firstPreviews, tagReport] = await Promise.all([
      currentResponse.json(), firstResponse.json(), previewResponse.json(),
      tagsResponse.ok ? tagsResponse.json() : Promise.resolve({ assets: [] })
    ]);
    const firstPreviewById = new Map(firstPreviews.assets.map(item => [item.asset_id, item.file]));
    const tagsByFile = new Map(tagReport.assets.map(item => [item.file, item.analysis]));
    recordings = [
      ...current.assets.map(asset => ({
        key: `current:${asset.id}`,
        id: asset.id,
        collection: "current",
        collectionLabel: "Current collection",
        title: asset.title || asset.id,
        description: asset.event_guidance || "No source description is recorded.",
        category: asset.category || "uncategorized",
        durationSeconds: Number(asset.duration_seconds) || 0,
        source: asset.file,
        previews: (asset.derivatives || []).map(item => item.file),
        analysis: tagsByFile.get(asset.file),
        license: asset.license || "unknown"
      })),
      ...first.assets.map(asset => ({
        key: `first:${asset.id}`,
        id: asset.id,
        collection: "first",
        collectionLabel: "First collection",
        title: asset.description || asset.id,
        description: asset.playback_guidance || "No additional playback guidance is recorded.",
        category: asset.priority_category || asset.event || "uncategorized",
        durationSeconds: Number(asset.audio?.duration_seconds) || 0,
        source: `first-collection/${asset.path}`,
        previews: firstPreviewById.has(asset.id) ? [firstPreviewById.get(asset.id)] : [],
        analysis: tagsByFile.get(`first-collection/${asset.path}`),
        license: asset.license || "unknown"
      }))
    ];
    render();
  } catch (error) {
    summary.textContent = "Could not load the audio inventory.";
    errorBox.textContent = `${error.message} Run ` +
      "python tools/audio-audition/serve.py from the repository root, then open " +
      "http://localhost:8000/tools/audio-audition/.";
  }
}

function makeField(labelText, type, value, className, choices) {
  const label = node("label", undefined, `field-label ${className || ""}`.trim());
  label.append(node("span", labelText));
  let control;
  if (type === "select") {
    control = document.createElement("select");
    for (const [choiceValue, choiceLabel] of choices) control.append(option(choiceValue, choiceLabel));
    control.value = value || choices[0][0];
  } else if (type === "textarea") {
    control = document.createElement("textarea");
    control.value = value || "";
    control.placeholder = "Add what you heard; keep source metadata separate from your listening notes.";
  } else {
    control = document.createElement("input");
    control.type = type;
    control.value = value || "";
    if (type === "number") { control.min = "0"; control.step = "0.1"; }
  }
  label.append(control);
  return { label, control };
}

function buildCard(item) {
  const saved = reviews[item.key] || {};
  const card = node("article", undefined, "card");
  card.dataset.key = item.key;
  card.dataset.collection = item.collection;

  card.append(node("h2", item.title));
  card.append(node("div", `${item.collectionLabel} · ${item.id} · ${item.category} · ${item.license}`, "meta"));
  card.append(node("p", item.description, "description"));

  const playerRow = node("div", undefined, "player");
  const player = document.createElement("audio");
  player.controls = true;
  player.preload = "metadata";
  player.src = `/${item.source}`;
  playerRow.append(player);
  if (item.previews.length) {
    const select = document.createElement("select");
    select.setAttribute("aria-label", `Audio version for ${item.id}`);
    select.append(option(item.source, "Master recording"));
    for (const file of item.previews) select.append(option(file, `Preview: ${file.split("/").pop()}`));
    select.addEventListener("change", () => {
      player.src = `/${select.value}`;
      player.load();
    });
    playerRow.append(select);
  }
  card.append(playerRow);

  const timeline = node("div", undefined, "timeline");
  const back = node("button", "−10s");
  back.type = "button";
  back.setAttribute("aria-label", "Rewind 10 seconds");
  const range = document.createElement("input");
  range.type = "range";
  range.min = "0";
  range.max = String(item.durationSeconds || 0);
  range.step = "0.1";
  range.value = "0";
  range.disabled = !item.durationSeconds;
  range.setAttribute("aria-label", "Seek through the full recording");
  const forward = node("button", "+10s");
  forward.type = "button";
  forward.setAttribute("aria-label", "Forward 10 seconds");
  const time = node("span", `0:00 / ${formatTime(item.durationSeconds)}`, "time-readout");
  const seekTo = seconds => {
    const duration = Number.isFinite(player.duration) ? player.duration : item.durationSeconds;
    player.currentTime = Math.max(0, Math.min(duration || 0, seconds));
  };
  back.addEventListener("click", () => seekTo((player.currentTime || 0) - 10));
  forward.addEventListener("click", () => seekTo((player.currentTime || 0) + 10));
  range.addEventListener("input", () => {
    time.textContent = `${formatTime(Number(range.value))} / ${formatTime(item.durationSeconds)}`;
  });
  range.addEventListener("change", () => seekTo(Number(range.value)));
  const updateTimeline = () => {
    const duration = Number.isFinite(player.duration) ? player.duration : item.durationSeconds;
    if (duration) {
      range.max = String(duration);
      range.disabled = false;
    }
    if (document.activeElement !== range) range.value = String(player.currentTime || 0);
    time.textContent = `${formatTime(player.currentTime || 0)} / ${formatTime(duration)}`;
  };
  player.addEventListener("timeupdate", updateTimeline);
  player.addEventListener("loadedmetadata", updateTimeline);
  player.addEventListener("durationchange", updateTimeline);
  timeline.append(back, range, forward, time);
  card.append(timeline);

  if (item.analysis) {
    const tags = item.analysis.top_tags_by_mean_score.slice(0, 5)
      .map(tag => `${tag.label} ${tag.score.toFixed(2)}`).join(" · ");
    card.append(node("p", `Automated YAMNet suggestions (unverified): ${tags}`, "model-hint"));
    const windows = node("div", undefined, "windows");
    for (const window of item.analysis.highest_scoring_windows.slice(0, 5)) {
      const seek = node("button", `${window.start_seconds.toFixed(0)}s · ${window.label} ${window.score.toFixed(2)}`);
      seek.type = "button";
      seek.title = "Seek the player to this classifier-highlighted time; it will not start playback.";
      seek.addEventListener("click", () => {
        const setPosition = () => { player.currentTime = window.start_seconds; };
        if (player.readyState === 0) player.addEventListener("loadedmetadata", setPosition, { once: true });
        else setPosition();
      });
      windows.append(seek);
    }
    card.append(windows);
  }

  const fields = node("div", undefined, "fields");
  const disposition = makeField("Your assessment", "select", saved.disposition, "", [
    ["undecided", "Undecided"],
    ["usable_authentic", "Potentially usable, authentic"],
    ["usable_substitute", "Potentially usable, substitute"],
    ["needs_edit", "Potentially useful segment; edit needed"],
    ["not_suitable", "Not suitable"],
    ["unusable", "Unusable or corrupt"]
  ]);
  fields.append(disposition.label);
  const loop = makeField("Loop boundary", "select", saved.loop_boundary, "", [
    ["not_reviewed", "Not checked"],
    ["not_applicable", "Not intended as a loop"],
    ["good", "Boundary sounds suitable"],
    ["bad", "Boundary needs an edit"]
  ]);
  fields.append(loop.label);
  const start = makeField("Useful segment start (seconds)", "number", saved.segment_start_seconds, "");
  fields.append(start.label);
  const end = makeField("Useful segment end (seconds)", "number", saved.segment_end_seconds, "");
  fields.append(end.label);
  const content = makeField("What you hear", "textarea", saved.content_notes, "wide");
  fields.append(content.label);
  const quality = makeField("Noise, clipping, or other quality issues", "textarea", saved.quality_notes, "wide");
  fields.append(quality.label);
  const additional = makeField("Other notes", "textarea", saved.additional_notes, "wide");
  fields.append(additional.label);
  const reviewer = makeField("Reviewer name", "text", saved.reviewer, "");
  fields.append(reviewer.label);
  card.append(fields);

  const footer = node("div", undefined, "card-footer");
  const save = node("button", "Save notes");
  save.type = "button";
  const savedLabel = node("span", saved.reviewed_at ? `Saved ${saved.reviewed_at}` : "Not saved", "saved");
  save.addEventListener("click", () => {
    const note = {
      id: item.id,
      collection: item.collection,
      source_file: item.source,
      disposition: disposition.control.value,
      loop_boundary: loop.control.value,
      segment_start_seconds: start.control.value === "" ? null : Number(start.control.value),
      segment_end_seconds: end.control.value === "" ? null : Number(end.control.value),
      content_notes: content.control.value.trim(),
      quality_notes: quality.control.value.trim(),
      additional_notes: additional.control.value.trim(),
      reviewer: reviewer.control.value.trim(),
      reviewed_at: new Date().toISOString()
    };
    reviews[item.key] = note;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(reviews));
    savedLabel.textContent = `Saved ${note.reviewed_at}`;
    applyFilters();
  });
  footer.append(save, savedLabel);
  card.append(footer);
  return card;
}

function render() {
  list.replaceChildren(...recordings.map(buildCard));
  applyFilters();
}

function applyFilters() {
  const query = searchBox.value.trim().toLowerCase();
  const collection = collectionBox.value;
  const state = stateBox.value;
  let shown = 0;
  for (const card of list.children) {
    const item = recordings.find(entry => entry.key === card.dataset.key);
    const text = `${item.title} ${item.id} ${item.category} ${item.description} ${item.source}`.toLowerCase();
    const isReviewed = Boolean(reviews[item.key]?.reviewed_at);
    const visible = (!query || text.includes(query)) &&
      (collection === "all" || collection === item.collection) &&
      (state === "all" || (state === "notes") === isReviewed);
    card.hidden = !visible;
    if (visible) shown++;
  }
  const reviewed = recordings.filter(item => reviews[item.key]?.reviewed_at).length;
  summary.textContent = `${shown} shown · ${recordings.length} recordings · ${reviewed} have saved notes in this browser`;
}

document.querySelector("#export").addEventListener("click", () => {
  const payload = {
    schema_version: 1,
    note: "Human listening notes only; this file does not update the collection manifests or establish release readiness.",
    exported_at: new Date().toISOString(),
    reviews: Object.values(reviews)
  };
  const blob = new Blob([JSON.stringify(payload, null, 2) + "\n"], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "terminal-soundscape-listening-notes.json";
  link.click();
  URL.revokeObjectURL(url);
});

searchBox.addEventListener("input", applyFilters);
collectionBox.addEventListener("change", applyFilters);
stateBox.addEventListener("change", applyFilters);
load();
