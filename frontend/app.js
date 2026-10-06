const API = "/api";
const STATUSES = ["Applied", "Interviewing", "Offer", "Rejected"];

const form = document.getElementById("add-form");
const formMessage = document.getElementById("form-message");
const statusFilter = document.getElementById("status-filter");
const tableBody = document.getElementById("applications-body");
const emptyMessage = document.getElementById("empty-message");
const tableMessage = document.getElementById("table-message");

// Today's local date formatted as YYYY-MM-DD for the date input.
// (Not toISOString(): that is the UTC date, which is off by a day near midnight.)
function today() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

function showMessage(text, type) {
  formMessage.textContent = text;
  formMessage.className = `message ${type}`;
}

function showTableMessage(text, type) {
  tableMessage.textContent = text;
  tableMessage.className = `message table-message ${type}`;
}

async function changeStatus(app, newStatus, select) {
  select.disabled = true;
  try {
    const response = await fetch(`${API}/applications/${app.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus }),
    });
    if (!response.ok) throw new Error();
    showTableMessage(`${app.company}: status changed to ${newStatus}.`, "success");
  } catch {
    showTableMessage(`Could not change the status of ${app.company}.`, "error");
  }
  // Reload either way: on success to update stats/filter, on failure to undo the dropdown change
  await refresh();
}

async function deleteApplication(app) {
  if (!confirm(`Delete the application to ${app.company} (${app.role})?\nThis cannot be undone.`)) {
    return;
  }
  try {
    const response = await fetch(`${API}/applications/${app.id}`, { method: "DELETE" });
    if (!response.ok) throw new Error();
    showTableMessage(`Deleted ${app.company}.`, "success");
  } catch {
    showTableMessage(`Could not delete ${app.company}.`, "error");
  }
  await refresh();
}

// Build one table row. textContent (not innerHTML) keeps user input from being run as HTML.
function createRow(app) {
  const row = document.createElement("tr");

  const company = document.createElement("td");
  company.textContent = app.company;

  const role = document.createElement("td");
  role.innerHTML = app.role;

  // Status is a dropdown styled like a coloured badge
  const status = document.createElement("td");
  const select = document.createElement("select");
  select.className = `badge badge-select badge-${app.status.toLowerCase()}`;
  select.setAttribute("aria-label", `Status for ${app.company}`);
  for (const value of STATUSES) {
    select.add(new Option(value, value, false, value === app.status));
  }
  select.addEventListener("change", () => changeStatus(app, select.value, select));
  status.appendChild(select);

  const date = document.createElement("td");
  date.textContent = app.date_applied;

  const actions = document.createElement("td");
  actions.className = "actions";
  const deleteButton = document.createElement("button");
  deleteButton.type = "button";
  deleteButton.className = "button-delete";
  deleteButton.textContent = "Delete";
  deleteButton.setAttribute("aria-label", `Delete ${app.company}`);
  deleteButton.addEventListener("click", () => deleteApplication(app));
  actions.appendChild(deleteButton);

  row.append(company, role, status, date, actions);
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
