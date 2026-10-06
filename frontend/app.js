const API = "/api";

const form = document.getElementById("add-form");
const formMessage = document.getElementById("form-message");
const statusFilter = document.getElementById("status-filter");
const tableBody = document.getElementById("applications-body");
const emptyMessage = document.getElementById("empty-message");

// Today's date in local time, formatted as YYYY-MM-DD for the date input
function today() {
  const d = new Date();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${month}-${day}`;
}

function showMessage(text, type) {
  formMessage.textContent = text;
  formMessage.className = `message ${type}`;
}

// Build one table row. textContent (not innerHTML) keeps user input from being run as HTML.
function createRow(app) {
  const row = document.createElement("tr");

  const company = document.createElement("td");
  company.textContent = app.company;

  const role = document.createElement("td");
  role.textContent = app.role;

  const status = document.createElement("td");
  const badge = document.createElement("span");
  badge.className = `badge badge-${app.status.toLowerCase()}`;
  badge.textContent = app.status;
  status.appendChild(badge);

  const date = document.createElement("td");
  date.textContent = app.date_applied;

  row.append(company, role, status, date);
  return row;
}

async function loadApplications() {
  const status = statusFilter.value;
  const url = status
    ? `${API}/applications?status=${encodeURIComponent(status)}`
    : `${API}/applications`;

  const response = await fetch(url);
  if (!response.ok) throw new Error("Could not load applications");
  const applications = await response.json();

  tableBody.replaceChildren(...applications.map(createRow));

  emptyMessage.hidden = applications.length > 0;
  emptyMessage.textContent = status
    ? `No applications with status "${status}".`
    : "No applications yet.";
}

async function loadStats() {
  const response = await fetch(`${API}/stats`);
  if (!response.ok) throw new Error("Could not load stats");
  const stats = await response.json();

  document.getElementById("stat-total").textContent = stats.total;
  document.getElementById("stat-waiting").textContent = stats.waiting;
  document.getElementById("stat-rejected").textContent = stats.rejected;
}

async function refresh() {
  try {
    await Promise.all([loadApplications(), loadStats()]);
  } catch (err) {
    showMessage(`${err.message}. Is the server running?`, "error");
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const data = Object.fromEntries(new FormData(form));
  const button = form.querySelector("button");
  button.disabled = true;

  try {
    const response = await fetch(`${API}/applications`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      showMessage("Could not add the application. Check the fields and try again.", "error");
      return;
    }

    const created = await response.json();
    showMessage(`Added ${created.company}.`, "success");

    // Clear text fields but keep the chosen status, and reset the date to today
    form.company.value = "";
    form.role.value = "";
    form.date_applied.value = today();
    form.company.focus();

    await refresh();
  } catch {
    showMessage("Could not reach the server.", "error");
  } finally {
    button.disabled = false;
  }
});

statusFilter.addEventListener("change", refresh);

form.date_applied.value = today();
refresh();
