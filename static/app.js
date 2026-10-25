const form = document.querySelector("#student-form");
const notice = document.querySelector("#notice");
const rows = document.querySelector("#student-rows");
const loading = document.querySelector("#loading");
const empty = document.querySelector("#empty");
const count = document.querySelector("#count");
const searchInput = document.querySelector("#search");
const courseFilter = document.querySelector("#course-filter");
const cancelEdit = document.querySelector("#cancel-edit");
const formTitle = document.querySelector("#form-title");
const submitButton = document.querySelector("#submit-button");
let noticeTimer;

function showNotice(message, type = "success") {
  notice.textContent = message;
  notice.className = `notice ${type}`;
  clearTimeout(noticeTimer);
  noticeTimer = setTimeout(() => notice.classList.add("hidden"), 4500);
}

async function request(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : null;
  if (!response.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map(item => `${item.loc?.slice(-1)[0] || "Field"}: ${item.msg}`).join("; ")
      : (detail || `Request failed (${response.status})`);
    throw new Error(message);
  }
  return data;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  })[char]);
}

function prettyDate(value) {
  if (!value) return "—";
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? escapeHtml(value) :
    date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

async function loadStudents() {
  loading.classList.remove("hidden");
  empty.classList.add("hidden");
  try {
    const params = new URLSearchParams();
    if (searchInput.value.trim()) params.set("search", searchInput.value.trim());
    if (courseFilter.value.trim()) params.set("course", courseFilter.value.trim());
    const students = await request(`/students?${params.toString()}`);
    count.textContent = students.length;
    rows.innerHTML = students.map(student => `
      <tr>
        <td><span class="student-name">${escapeHtml(student.name)}</span><span class="student-id">ID #${student.id}</span></td>
        <td><span class="pill">${escapeHtml(student.course || "Not specified")}</span></td>
        <td>${prettyDate(student.date_of_birth)}</td>
        <td>${escapeHtml(student.phone || "—")}<span class="contact-email">${escapeHtml(student.email)}</span></td>
        <td><div class="actions">
          <button class="action-btn" data-action="edit" data-id="${student.id}" type="button">Edit</button>
          <button class="action-btn action-delete" data-action="delete" data-id="${student.id}" data-name="${escapeHtml(student.name)}" type="button">Delete</button>
        </div></td>
      </tr>`).join("");
    empty.classList.toggle("hidden", students.length > 0);
  } catch (error) {
    rows.innerHTML = "";
    empty.textContent = `Could not load records: ${error.message}. Check that the API is running.`;
    empty.classList.remove("hidden");
    count.textContent = "0";
  } finally {
    loading.classList.add("hidden");
  }
}

function resetForm() {
  form.reset();
  document.querySelector("#student-id").value = "";
  formTitle.textContent = "Add a student";
  submitButton.textContent = "Add student";
  cancelEdit.classList.add("hidden");
}

function fillForm(student) {
  document.querySelector("#student-id").value = student.id;
  for (const key of ["name", "date_of_birth", "enrollment_date", "email", "phone", "course", "address"]) {
    document.querySelector(`#${key}`).value = student[key] || "";
  }
  formTitle.textContent = `Edit student #${student.id}`;
  submitButton.textContent = "Save changes";
  cancelEdit.classList.remove("hidden");
  document.querySelector("#name").focus();
  document.querySelector(".form-panel").scrollIntoView({ behavior: "smooth", block: "start" });
}

form.addEventListener("submit", async event => {
  event.preventDefault();
  const id = document.querySelector("#student-id").value;
  const payload = {};
  for (const key of ["name", "date_of_birth", "email", "phone", "course", "address", "enrollment_date"]) {
    const value = document.querySelector(`#${key}`).value.trim();
    if (value) payload[key] = value;
  }
  try {
    if (id) {
      await request(`/students/${id}`, { method: "PUT", body: JSON.stringify(payload) });
      showNotice("Student details updated successfully.");
    } else {
      await request("/students", { method: "POST", body: JSON.stringify(payload) });
      showNotice("Student added successfully.");
    }
    resetForm();
    await loadStudents();
  } catch (error) {
    showNotice(error.message, "error");
  }
});

rows.addEventListener("click", async event => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const id = button.dataset.id;
  if (button.dataset.action === "edit") {
    try {
      const student = await request(`/students/${id}`);
      fillForm(student);
    } catch (error) {
      showNotice(error.message, "error");
    }
  } else if (button.dataset.action === "delete") {
    const name = button.dataset.name;
    if (!confirm(`Delete ${name}'s record? This cannot be undone.`)) return;
    try {
      await request(`/students/${id}`, { method: "DELETE" });
      if (document.querySelector("#student-id").value === id) resetForm();
      showNotice("Student deleted successfully.");
      await loadStudents();
    } catch (error) {
      showNotice(error.message, "error");
    }
  }
});

cancelEdit.addEventListener("click", resetForm);
document.querySelector("#refresh").addEventListener("click", loadStudents);
let searchTimer;
searchInput.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadStudents, 250);
});
courseFilter.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadStudents, 250);
});

loadStudents();
