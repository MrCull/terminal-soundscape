const REVIEWER_KEY = "terminal-soundscape-reviewer-v1";
const list = document.querySelector("#recordings");
const summary = document.querySelector("#summary");
const errorBox = document.querySelector("#error");
const searchBox = document.querySelector("#search");
const collectionBox = document.querySelector("#collection");
const reviewerBox = document.querySelector("#reviewer");
const queueTab = document.querySelector("#tab-queue");
const savedTab = document.querySelector("#tab-saved");
const queueCount = document.querySelector("#queue-count");
const savedCount = document.querySelector("#saved-count");

let recordings = [];
let reviews = {};
let activeTab = "queue";
reviewerBox.value = localStorage.getItem(REVIEWER_KEY) || "";
reviewerBox.addEventListener("input", () => localStorage.setItem(REVIEWER_KEY, reviewerBox.value));

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
    const [currentResponse, firstResponse, previewResponse, tagsResponse, reviewsResponse] = await Promise.all([
      fetch("/manifest.json"),
      fetch("/first-collection/manifest.json"),
      fetch("/first-collection/browser-previews/preview-manifest.json"),
      fetch("/docs/generated/audio-event-tags.json"),
      fetch("/api/reviews")
    ]);
    if (![currentResponse, firstResponse, previewResponse, reviewsResponse].every(response => response.ok)) {
      throw new Error("Could not read the repository files. Start the audition server from the repository root.");
    }
    const [current, first, firstPreviews, tagReport, savedReviews] = await Promise.all([
      currentResponse.json(), firstResponse.json(), previewResponse.json(),
      tagsResponse.ok ? tagsResponse.json() : Promise.resolve({ assets: [] }),
      reviewsResponse.json()
    ]);
    reviews = Object.fromEntries((savedReviews.reviews || []).map(review => [
      `${review.collection === "first-collection" ? "first" : "current"}:${review.id}`,
      review
    ]));
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
  player.preload = "none";
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
    const setPosition = () => {
      const duration = Number.isFinite(player.duration) ? player.duration : item.durationSeconds;
      player.currentTime = Math.max(0, Math.min(duration || 0, seconds));
    };
    if (player.readyState === 0) {
      player.addEventListener("loadedmetadata", setPosition, { once: true });
      player.preload = "metadata";
      player.load();
    } else {
      setPosition();
    }
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
      seek.addEventListener("click", () => seekTo(window.start_seconds));
      windows.append(seek);
    }
    card.append(windows);
  }

  const fields = node("div", undefined, "fields");
  let rating = Number(saved.rating) || 0;
  const ratingField = node("div", undefined, "review-input");
  ratingField.append(node("span", "Quick rating"));
  const stars = node("div", undefined, "stars");
  const starButtons = [];
  const showRating = () => starButtons.forEach((button, index) => {
    button.classList.toggle("selected", index < rating);
    button.setAttribute("aria-pressed", String(index + 1 === rating));
  });
  for (let value = 1; value <= 5; value++) {
    const button = node("button", "★");
    button.type = "button";
    button.setAttribute("aria-label", `${value} out of 5 stars`);
    button.addEventListener("click", () => { rating = value; showRating(); });
    starButtons.push(button);
    stars.append(button);
  }
  ratingField.append(stars);
  showRating();
  fields.append(ratingField);

  const availableTags = ["crane", "container handling", "vehicle", "engine", "ship", "alarm / whistle", "water / waves", "birds", "speech", "machinery", "ambience", "useful event", "loop candidate", "poor quality"];
  const selectedTags = new Set(saved.tags || []);
  const tagField = node("fieldset", undefined, "tag-field");
  tagField.append(node("legend", "Tags (optional)"));
  const tagOptions = node("div", undefined, "tag-options");
  for (const tag of availableTags) {
    const label = node("label", undefined, "tag-option");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = tag;
    checkbox.checked = selectedTags.has(tag);
    checkbox.addEventListener("change", () => checkbox.checked ? selectedTags.add(tag) : selectedTags.delete(tag));
    label.append(checkbox, node("span", tag));
    tagOptions.append(label);
  }
  tagField.append(tagOptions);
  fields.append(tagField);

  let startMarker = saved.start_seconds ?? null;
  let endMarker = saved.end_seconds ?? null;
  const markerField = node("div", undefined, "marker-field wide");
  markerField.append(node("span", "Cut / loop reference markers"));
  const markerControls = node("div", undefined, "marker-controls");
  const startButton = node("button", "Mark start at playhead");
  startButton.type = "button";
  const endButton = node("button", "Mark end at playhead");
  endButton.type = "button";
  const clearMarkers = node("button", "Clear markers");
  clearMarkers.type = "button";
  const markerReadout = node("span", "No markers set", "marker-readout");
  const showMarkers = () => {
    markerReadout.textContent = `Start: ${startMarker === null ? "—" : `${startMarker.toFixed(1)}s`} · End: ${endMarker === null ? "—" : `${endMarker.toFixed(1)}s`}`;
  };
  startButton.addEventListener("click", () => { startMarker = Number((player.currentTime || 0).toFixed(1)); showMarkers(); });
  endButton.addEventListener("click", () => { endMarker = Number((player.currentTime || 0).toFixed(1)); showMarkers(); });
  clearMarkers.addEventListener("click", () => { startMarker = null; endMarker = null; showMarkers(); });
  markerControls.append(startButton, endButton, clearMarkers, markerReadout);
  markerField.append(markerControls);
  fields.append(markerField);
  showMarkers();

  const notes = makeField("Optional note", "textarea", saved.notes, "wide");
  fields.append(notes.label);
  card.append(fields);

  const footer = node("div", undefined, "card-footer");
  const save = node("button", saved.saved_at ? "Update saved review" : "Save to repo");
  save.type = "button";
  const savedLabel = node("span", saved.saved_at ? `Saved to repo ${saved.saved_at}` : "Not saved", "saved");
  save.addEventListener("click", async () => {
    if (!rating) {
      savedLabel.textContent = "Choose a star rating first.";
      return;
    }
    if (startMarker !== null && endMarker !== null && endMarker <= startMarker) {
      savedLabel.textContent = "End marker must come after the start marker.";
      return;
    }
    const review = {
      id: item.id,
      collection: item.collection === "first" ? "first-collection" : "current",
      source_file: item.source,
      rating,
      tags: [...selectedTags],
      start_seconds: startMarker,
      end_seconds: endMarker,
      notes: notes.control.value.trim(),
      reviewer: reviewerBox.value.trim()
    };
    save.disabled = true;
    savedLabel.textContent = "Saving to docs/listening-reviews.json…";
    try {
      const response = await fetch("/api/reviews", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ review })
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Save failed");
      reviews[item.key] = result.review;
      savedLabel.textContent = `Saved to repo ${result.review.saved_at}`;
      save.textContent = "Update saved review";
      activeTab = "saved";
      updateTabs();
      applyFilters();
    } catch (error) {
      savedLabel.textContent = `Not saved: ${error.message}`;
    } finally {
      save.disabled = false;
    }
  });
  footer.append(save, savedLabel);
  card.append(footer);
  return card;
}

function render() {
  list.replaceChildren(...recordings.map(buildCard));
  updateTabs();
  applyFilters();
}

function updateTabs() {
  const saved = recordings.filter(item => reviews[item.key]?.saved_at).length;
  queueCount.textContent = recordings.length - saved;
  savedCount.textContent = saved;
  queueTab.setAttribute("aria-selected", String(activeTab === "queue"));
  savedTab.setAttribute("aria-selected", String(activeTab === "saved"));
}

function applyFilters() {
  const query = searchBox.value.trim().toLowerCase();
  const collection = collectionBox.value;
  let shown = 0;
  for (const card of list.children) {
    const item = recordings.find(entry => entry.key === card.dataset.key);
    const text = `${item.title} ${item.id} ${item.category} ${item.description} ${item.source}`.toLowerCase();
    const isSaved = Boolean(reviews[item.key]?.saved_at);
    const visible = (!query || text.includes(query)) &&
      (collection === "all" || collection === item.collection) &&
      (activeTab === "saved" ? isSaved : !isSaved);
    card.hidden = !visible;
    if (visible) shown++;
  }
  const saved = recordings.filter(item => reviews[item.key]?.saved_at).length;
  summary.textContent = `${shown} shown · ${recordings.length - saved} to review · ${saved} saved in the repo`;
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
queueTab.addEventListener("click", () => { activeTab = "queue"; updateTabs(); applyFilters(); });
savedTab.addEventListener("click", () => { activeTab = "saved"; updateTabs(); applyFilters(); });
load();
