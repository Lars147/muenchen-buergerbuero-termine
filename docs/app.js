// Add these variables at the top of the file
let refreshInterval;
let countdownInterval;
const REFRESH_INTERVAL = 30000; // 30 seconds
let CONSTANTS;


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


async function loadAppointments() {
  try {
    const response = await fetch(
      "https://raw.githubusercontent.com/Lars147/muenchen-buergerbuero-termine/refs/heads/main/appointments.json"
    );
    if (!response.ok) {
      throw new Error("Failed to load appointment data");
    }
    const data = await response.json();
    displayAppointments(data);
    updateCountdown(REFRESH_INTERVAL / 1000); // Start countdown from 30
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

// Add this new function to handle the countdown
function updateCountdown(seconds) {
  const lastUpdateElement = document.getElementById("lastUpdate");

  // Clear existing countdown interval if any
  if (countdownInterval) {
    clearInterval(countdownInterval);
  }

  countdownInterval = setInterval(() => {
    seconds--;
    if (!lastUpdateElement.dataset.lastUpdate) {
      lastUpdateElement.dataset.lastUpdate = new Date().toLocaleString();
    }
    lastUpdateElement.textContent = `Last updated: ${lastUpdateElement.dataset.lastUpdate} (refreshing in ${seconds}s)`;

    if (seconds <= 0) {
      clearInterval(countdownInterval);
    }
  }, 1000);
}

function displayAppointments(data) {
  const contentDiv = document.getElementById("content");
  const loadingDiv = document.getElementById("loading");
  const lastUpdateElement = document.getElementById("lastUpdate");
  const tocList = document.querySelector("#tableOfContents ul");

  // Update timestamp
  lastUpdateElement.dataset.lastUpdate = new Date().toLocaleString();

  // Clear loading message and content
  loadingDiv.style.display = "none";
  contentDiv.innerHTML = "";
  tocList.innerHTML = "";

  // Generate table of contents and content for each service
  Object.entries(data).forEach(([serviceName, officeData]) => {
    // Create service ID for linking
    const serviceId = serviceName.toLowerCase().replace(/\s+/g, "-");

    // Calculate total appointments for this service
    const totalAppointments = Object.values(officeData).reduce(
      (total, office) => {
        return (
          total +
          Object.values(office).reduce((officeTotal, dateData) => {
            if (dateData.appointmentTimestamps) {
              return officeTotal + dateData.appointmentTimestamps.length;
            }
            return officeTotal;
          }, 0)
        );
      },
      0
    );

    // Add to table of contents
    tocList.innerHTML += `
      <li>
        <a href="#${serviceId}" class="${
      totalAppointments > 0 ? "has-appointments" : ""
    }">
          ${serviceName}
          <span class="toc-count ${
            totalAppointments === 0 ? "empty" : ""
          }">${totalAppointments}</span>
        </a>
      </li>
    `;

    // Create service section with ID
    const serviceSection = document.createElement("div");
    serviceSection.className = "service-section";
    serviceSection.id = serviceId;

    serviceSection.innerHTML = `<h2>${serviceName}</h2>`;

    // Generate content for each office
    Object.entries(officeData).forEach(([officeName, dateData]) => {
      const officeSection = document.createElement("div");
      officeSection.className = "office-section";

      const availableDates = Object.keys(dateData);
      const appointmentCount = Object.values(dateData).reduce(
        (sum, dateObj) => sum + (dateObj.appointmentTimestamps?.length || 0),
        0
      );

      officeSection.innerHTML = `
        <div class="office-header" onclick="toggleOffice(this)">
          <span class="toggle-icon">▶</span>
          <h3 style="margin: 0">${officeName}</h3>
          <span class="appointment-count ${
            appointmentCount === 0 ? "empty" : ""
          }">${appointmentCount}</span>
        </div>
        <div class="office-content">
          ${
            appointmentCount > 0
              ? `<div class="date-list">
                ${availableDates
                  .map(
                    (date) => `
                    <div class="date-item">
                      <div class="date-header" onclick="toggleDay(this)">
                        <span class="toggle-icon">▶</span>
                        ${new Date(date).toLocaleDateString()}
                      </div>
                      <div class="times-list">
                        ${(dateData[date].appointmentTimestamps || [])
                          .map((time) => {
                            const appointmentTime = new Date(time * 1000);
                            
                            return `<div class="time-item"><a target="blank_" href="https://stadt.muenchen.de/buergerservice/terminvereinbarung.html#/services/${
                              CONSTANTS.services[serviceName]
                            }/">${appointmentTime.toLocaleTimeString()}</a></div>`;
                          })
                          .join("")}
                      </div>
                    </div>
                `
                  )
                  .join("")}
              </div>`
              : "<p>No appointments available</p>"
          }
        </div>
      `;

      serviceSection.appendChild(officeSection);
    });

    contentDiv.appendChild(serviceSection);
  });
}

// Add this new function to handle toggling
function toggleOffice(header) {
  const content = header.nextElementSibling;
  const icon = header.querySelector(".toggle-icon");

  content.classList.toggle("expanded");
  icon.textContent = content.classList.contains("expanded") ? "▼" : "▶";
}

// Add this new function to handle toggling days
function toggleDay(header) {
  const timesList = header.nextElementSibling;
  const icon = header.querySelector(".toggle-icon");
  timesList.classList.toggle("expanded");
  icon.textContent = timesList.classList.contains("expanded") ? "▼" : "▶";
}

// Update the DOMContentLoaded event listener
document.addEventListener("DOMContentLoaded", async () => {
  CONSTANTS = await fetchConstants();
  loadAppointments();

  // Clear existing interval if any
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }

  // Set up auto-refresh
  refreshInterval = setInterval(loadAppointments, REFRESH_INTERVAL);
});
