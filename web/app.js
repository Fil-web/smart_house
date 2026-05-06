const devicesEl = document.querySelector("#devices");
const scenesEl = document.querySelector("#scenes");
const eventsEl = document.querySelector("#events");
const refreshButton = document.querySelector("#refresh");

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

function formatState(state) {
  return Object.entries(state)
    .map(([key, value]) => `${key}: ${value}`)
    .join(", ");
}

async function toggleDevice(device) {
  const nextPower = !Boolean(device.state.power);
  await api(`/api/devices/${device.id}`, {
    method: "PATCH",
    body: JSON.stringify({ state: { power: nextPower } }),
  });
  await load();
}

async function runScene(sceneId) {
  await api(`/api/scenes/${sceneId}/run`, { method: "POST" });
  await load();
}

function renderDevices(devices) {
  devicesEl.replaceChildren(
    ...devices.map((device) => {
      const card = document.createElement("article");
      card.className = "device";
      const hasPower = Object.prototype.hasOwnProperty.call(device.state, "power");
      card.innerHTML = `
        <div class="device-top">
          <div>
            <p class="device-name">${device.name}</p>
            <p class="room">${device.room} · ${device.type}</p>
          </div>
        </div>
        <p class="state">${formatState(device.state)}</p>
      `;
      if (hasPower) {
        const button = document.createElement("button");
        button.className = device.state.power ? "secondary" : "";
        button.textContent = device.state.power ? "Выключить" : "Включить";
        button.addEventListener("click", () => toggleDevice(device));
        card.querySelector(".device-top").append(button);
      }
      return card;
    }),
  );
}

function renderScenes(scenes) {
  scenesEl.replaceChildren(
    ...scenes.map((scene) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = scene.name;
      button.addEventListener("click", () => runScene(scene.id));
      return button;
    }),
  );
}

function renderEvents(events) {
  eventsEl.replaceChildren(
    ...events.map((event) => {
      const row = document.createElement("div");
      row.className = "event";
      row.innerHTML = `
        <span>${event.created_at}</span>
        <strong>${event.kind}</strong>
        <code>${JSON.stringify(event.payload)}</code>
      `;
      return row;
    }),
  );
}

async function load() {
  const [{ devices }, { scenes }, { events }] = await Promise.all([
    api("/api/devices"),
    api("/api/scenes"),
    api("/api/events"),
  ]);
  renderDevices(devices);
  renderScenes(scenes);
  renderEvents(events);
}

refreshButton.addEventListener("click", load);
load().catch((error) => {
  devicesEl.textContent = error.message;
});
