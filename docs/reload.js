const REFRESH_INTERVAL = 60000; // 60 seconds
let CONSTANTS;

// Global variable for storing the last GitHub metadata timestamp
let lastGithubTimestamp = null;

// Global variables for ticking last update
let lastUpdateInterval = null;
let currentMetadataTimestamp = null;

async function fetchConstants() {
  try {
    const response = await fetch(
      "https://raw.githubusercontent.com/Lars147/muenchen-buergerbuero-termine/refs/heads/main/constants.json"
    );
    if (!response.ok) {
      throw new Error("Failed to load constants");
    }
    const constants = await response.json();
    return constants;
  } catch (error) {
    console.error("Error loading constants:", error);
    return null;
  }
}

async function fetchAppointmentMetadata() {
  try {
    const response = await fetch(
      'https://api.github.com/repos/Lars147/muenchen-buergerbuero-termine/commits?path=appointments.json&page=1&per_page=1'
    );
    if (!response.ok) {
      throw new Error('Failed to load commit metadata');
    }
    const commits = await response.json();
    if (commits.length > 0) {
      return commits[0].commit.author.date;
    } else {
      return null;
    }
  } catch (error) {
    console.error('Error loading commit metadata:', error);
    return null;
  }
}

function showReloadNotification(newTimestamp) {
  let notificationDiv = document.getElementById('reloadNotification');
  const formattedDate = new Date(newTimestamp).toLocaleString();
  if (!notificationDiv) {
    notificationDiv = document.createElement('div');
    notificationDiv.id = 'reloadNotification';
    notificationDiv.style.padding = '10px';
    notificationDiv.style.margin = '10px 0';
    notificationDiv.style.backgroundColor = '#e6ffe6';
    notificationDiv.style.border = '1px solid #4caf50';
    notificationDiv.style.borderRadius = '5px';
    notificationDiv.innerHTML = `New data available from GitHub (Last updated: ${formattedDate}). <button onclick="location.reload()">Reload Page</button>`;
    document.body.insertBefore(notificationDiv, document.body.firstChild);
  } else {
    notificationDiv.innerHTML = `New data available from GitHub (Last updated: ${formattedDate}). <button onclick="location.reload()">Reload Page</button>`;
  }
}

async function loadAppointments() {
  console.log("Loading appointments...");
  try {
    const response = await fetch(
      "https://raw.githubusercontent.com/Lars147/muenchen-buergerbuero-termine/refs/heads/main/appointments.json"
    );
    if (!response.ok) {
      throw new Error("Failed to load appointment data");
    }
    const data = await response.json();

    const metadataTimestamp = await fetchAppointmentMetadata();
    lastGithubTimestamp = metadataTimestamp;

    displayAppointments(data, metadataTimestamp);
    // Removed autorefresh countdown since auto-refresh is disabled
  } catch (error) {
    const loadingDiv = document.getElementById("loading");
    loadingDiv.style.display = "block";
    loadingDiv.innerHTML = `
      <div class="error">
        Error loading appointment data: ${error.message}
      </div>
    `;
  }
}

// Helper function to format relative time
function getRelativeTime(timestamp) {
  const now = new Date();
  const then = new Date(timestamp);
  const diffMs = now - then;
  const seconds = Math.floor(diffMs / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  if (days > 0) return days + ' day(s) ago';
  if (hours > 0) return hours + ' hour(s) ago';
  if (minutes > 0) return minutes + ' minute(s) ago';
  return seconds + ' second(s) ago';
}

function displayAppointments(data, metadataTimestamp) {
  const contentDiv = document.getElementById("content");
  const loadingDiv = document.getElementById("loading");
  const lastUpdateElement = document.getElementById("lastUpdate");
  const tocList = document.querySelector("#tableOfContents ul");

  // Store the current metadata timestamp globally for ticker updates
  currentMetadataTimestamp = metadataTimestamp;

  if (metadataTimestamp) {
    const absoluteTime = new Date(metadataTimestamp).toLocaleString();
    lastUpdateElement.textContent = `Last updated: ${absoluteTime} (${getRelativeTime(metadataTimestamp)})`;
  } else {
    const now = new Date();
    lastUpdateElement.textContent = `Last updated: ${now.toLocaleString()} (just now)`;
  }

  // Clear any existing ticker
  if (lastUpdateInterval) {
    clearInterval(lastUpdateInterval);
  }
  // Start a ticker to update the relative time every second
  lastUpdateInterval = setInterval(() => {
    if (currentMetadataTimestamp) {
      const absoluteTime = new Date(currentMetadataTimestamp).toLocaleString();
      lastUpdateElement.textContent = `Last updated: ${absoluteTime} (${getRelativeTime(currentMetadataTimestamp)})`;
    }
  }, 1000);

  loadingDiv.style.display = "none";
  contentDiv.innerHTML = "";
  tocList.innerHTML = "";

  Object.entries(data).forEach(([serviceName, officeData]) => {
    const serviceId = serviceName.toLowerCase().replace(/\s+/g, "-");
    const totalAppointments = Object.values(officeData).reduce((total, office) => {
      return (
        total + Object.values(office).reduce((officeTotal, dateData) => {
          if (dateData.appointmentTimestamps) {
            return officeTotal + dateData.appointmentTimestamps.length;
          }
          return officeTotal;
        }, 0)
      );
    }, 0);

    tocList.innerHTML += `
      <li>
        <a href="#${serviceId}" class="${totalAppointments > 0 ? "has-appointments" : ""}">
          ${serviceName}
          <span class="toc-count ${totalAppointments === 0 ? "empty" : ""}">${totalAppointments}</span>
        </a>
      </li>
    `;

    const serviceSection = document.createElement("div");
    serviceSection.className = "service-section";
    serviceSection.id = serviceId;
    serviceSection.innerHTML = `<h2>${serviceName}</h2>`;

    Object.entries(officeData).forEach(([officeName, dateData]) => {
      const officeSection = document.createElement("div");
      officeSection.className = "office-section";

      const availableDates = Object.keys(dateData);
      const appointmentCount = Object.values(dateData).reduce((sum, dateObj) => sum + (dateObj.appointmentTimestamps?.length || 0), 0);

      officeSection.innerHTML = `
        <div class="office-header" onclick="toggleOffice(this)">
          <span class="toggle-icon">▶</span>
          <h3 style="margin: 0">${officeName}</h3>
          <span class="appointment-count ${appointmentCount === 0 ? "empty" : ""}">${appointmentCount}</span>
        </div>
        <div class="office-content">
          ${appointmentCount > 0 ? `<div class="date-list">
                ${availableDates.map((date) => `
                    <div class="date-item">
                      <div class="date-header" onclick="toggleDay(this)">
                        <span class="toggle-icon">▶</span>
                        ${new Date(date).toLocaleDateString()}
                      </div>
                      <div class="times-list">
                        ${(dateData[date].appointmentTimestamps || []).map((time) => {
                          const appointmentTime = new Date(time * 1000);
                          return `<div class="time-item"><a target="blank_" href="https://stadt.muenchen.de/buergerservice/terminvereinbarung.html#/services/${CONSTANTS.services[serviceName]}/">${appointmentTime.toLocaleTimeString()}</a></div>`;
                        }).join("")}
                      </div>
                    </div>
                `).join("")}
              </div>` : "<p>No appointments available</p>"}
        </div>
      `;

      serviceSection.appendChild(officeSection);
    });

    contentDiv.appendChild(serviceSection);
  });
}

function toggleOffice(header) {
  const content = header.nextElementSibling;
  const icon = header.querySelector(".toggle-icon");
  content.classList.toggle("expanded");
  icon.textContent = content.classList.contains("expanded") ? "▼" : "▶";
}

function toggleDay(header) {
  const timesList = header.nextElementSibling;
  const icon = header.querySelector(".toggle-icon");
  timesList.classList.toggle("expanded");
  icon.textContent = timesList.classList.contains("expanded") ? "▼" : "▶";
}

// New function to periodically check for updates without auto-refreshing the UI
async function checkForUpdates() {
  console.log("Checking for updates...");
  try {
    const metadataTimestamp = await fetchAppointmentMetadata();
    // If new data is available, show notification (do not update the UI automatically)
    if (lastGithubTimestamp && metadataTimestamp && (metadataTimestamp !== lastGithubTimestamp)) {
      console.log("Update available from GitHub!");
      showReloadNotification(metadataTimestamp);
    }
    console.log("No updates found.");
  } catch (error) {
    console.error('Error checking for updates:', error);
  }
}

// Initial load of appointments and periodic checking for new data (without auto-refreshing the UI)
document.addEventListener("DOMContentLoaded", async () => {
  CONSTANTS = await fetchConstants();
  await loadAppointments();
  // Periodically check for updates every REFRESH_INTERVAL milliseconds
  setInterval(checkForUpdates, REFRESH_INTERVAL);
});
