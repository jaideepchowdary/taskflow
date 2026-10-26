/**
 * TaskFlow - Project & Task Management Dashboard
 * File: script.js
 * Description: Handles task CRUD operations, filters, search, metrics, and localStorage persistence.
 */

// ==========================================
// 1. Initial State & Sample Data
// ==========================================
const STORAGE_KEY = 'taskflow_tasks_v1';

// Starter tasks loaded if user has no saved tasks in localStorage yet
const INITIAL_TASKS = [
  {
    id: '1',
    name: 'Design MVP landing page mockup in Figma',
    project: 'Website Launch',
    priority: 'High',
    dueDate: '2026-10-30',
    status: 'In Progress'
  },
  {
    id: '2',
    name: 'Setup user authentication & secure session tokens',
    project: 'Backend API',
    priority: 'High',
    dueDate: '2026-11-02',
    status: 'Pending'
  },
  {
    id: '3',
    name: 'Draft seed fundraising pitch deck',
    project: 'Fundraising',
    priority: 'Medium',
    dueDate: '2026-11-10',
    status: 'Pending'
  },
  {
    id: '4',
    name: 'Conduct user interviews with 5 beta testers',
    project: 'Customer Discovery',
    priority: 'Medium',
    dueDate: '2026-10-28',
    status: 'Completed'
  },
  {
    id: '5',
    name: 'Configure production SSL & domain DNS settings',
    project: 'DevOps',
    priority: 'Low',
    dueDate: '2026-10-25',
    status: 'Completed'
  }
];

let tasks = [];

// ==========================================
// 2. DOM Element Selectors
// ==========================================
const tasksTableBody = document.getElementById('tasksTableBody');
const emptyState = document.getElementById('emptyState');
const visibleTasksCountBadge = document.getElementById('visibleTasksCountBadge');

// Metric counts
const totalProjectsCount = document.getElementById('totalProjectsCount');
const totalTasksCount = document.getElementById('totalTasksCount');
const pendingTasksCount = document.getElementById('pendingTasksCount');
const completedTasksCount = document.getElementById('completedTasksCount');
const currentDateText = document.getElementById('currentDateText');

// Controls & Filters
const searchInput = document.getElementById('searchInput');
const statusFilter = document.getElementById('statusFilter');
const priorityFilter = document.getElementById('priorityFilter');
const resetFiltersBtn = document.getElementById('resetFiltersBtn');

// Modal Elements
const taskModal = document.getElementById('taskModal');
const taskForm = document.getElementById('taskForm');
const modalTitle = document.getElementById('modalTitle');
const taskIdInput = document.getElementById('taskId');
const taskNameInput = document.getElementById('taskName');
const taskProjectInput = document.getElementById('taskProject');
const taskDueDateInput = document.getElementById('taskDueDate');
const taskPriorityInput = document.getElementById('taskPriority');
const taskStatusInput = document.getElementById('taskStatus');
const openAddTaskModalBtn = document.getElementById('openAddTaskModalBtn');
const closeModalBtn = document.getElementById('closeModalBtn');
const cancelModalBtn = document.getElementById('cancelModalBtn');
const emptyStateAddBtn = document.getElementById('emptyStateAddBtn');

// Sidebar & Navigation
const sidebar = document.getElementById('sidebar');
const sidebarOverlay = document.getElementById('sidebarOverlay');
const openSidebarBtn = document.getElementById('openSidebarBtn');
const closeSidebarBtn = document.getElementById('closeSidebarBtn');
const navLinks = document.querySelectorAll('.nav-link');
const contentViews = document.querySelectorAll('.content-view');
const pageTitle = document.getElementById('pageTitle');
const projectsGrid = document.getElementById('projectsGrid');

// Settings Elements
const loadSampleDataBtn = document.getElementById('loadSampleDataBtn');
const clearAllDataBtn = document.getElementById('clearAllDataBtn');

// Toast Notification
const toastNotification = document.getElementById('toastNotification');
const toastMessage = document.getElementById('toastMessage');

// ==========================================
// 3. Application Initialization
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
  displayFormattedDate();
  setDefaultDueDate();
  loadTasksFromStorage();
  renderDashboard();
  setupEventListeners();
});

// Set current date in top header
function displayFormattedDate() {
  const options = { weekday: 'long', year: 'numeric', month: 'short', day: 'numeric' };
  const today = new Date().toLocaleDateString('en-US', options);
  currentDateText.textContent = `Today is ${today} • Startup sprint in progress`;
}

// Prefill default date to tomorrow in the Add Task form using local time
function setDefaultDueDate() {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const yyyy = tomorrow.getFullYear();
  const mm = String(tomorrow.getMonth() + 1).padStart(2, '0');
  const dd = String(tomorrow.getDate()).padStart(2, '0');
  taskDueDateInput.value = `${yyyy}-${mm}-${dd}`;
}

// ==========================================
// 4. LocalStorage Helpers
// ==========================================
function loadTasksFromStorage() {
  const storedData = localStorage.getItem(STORAGE_KEY);
  if (storedData) {
    try {
      tasks = JSON.parse(storedData);
    } catch (error) {
      console.error('Error parsing stored tasks. Resetting to defaults.', error);
      tasks = [...INITIAL_TASKS];
      saveTasksToStorage();
    }
  } else {
    // First time visitor: seed default demo tasks
    tasks = [...INITIAL_TASKS];
    saveTasksToStorage();
  }
}

function saveTasksToStorage() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
}

// ==========================================
// 5. Render Functions
// ==========================================
function renderDashboard() {
  updateMetrics();
  renderTasksTable();
  renderProjectsGrid();
}

// Calculate and render top metric counters
function updateMetrics() {
  // Count unique project names (defaults to 'General' to match table & projects tab)
  const uniqueProjects = new Set(
    tasks
      .map(t => (t.project || 'General').trim())
      .filter(p => p.length > 0)
  );

  const total = tasks.length;
  const pending = tasks.filter(t => t.status === 'Pending').length;
  const completed = tasks.filter(t => t.status === 'Completed').length;

  totalProjectsCount.textContent = uniqueProjects.size;
  totalTasksCount.textContent = total;
  pendingTasksCount.textContent = pending;
  completedTasksCount.textContent = completed;
}

// Filter and render the task table rows
function renderTasksTable() {
  const searchQuery = searchInput.value.trim().toLowerCase();
  const selectedStatus = statusFilter.value;
  const selectedPriority = priorityFilter.value;

  // Filter tasks based on search text and select dropdowns
  const filteredTasks = tasks.filter(task => {
    const matchesSearch =
      task.name.toLowerCase().includes(searchQuery) ||
      (task.project && task.project.toLowerCase().includes(searchQuery));

    const matchesStatus =
      selectedStatus === 'all' || task.status === selectedStatus;

    const matchesPriority =
      selectedPriority === 'all' || task.priority === selectedPriority;

    return matchesSearch && matchesStatus && matchesPriority;
  });

  // Update badge counter
  visibleTasksCountBadge.textContent = `${filteredTasks.length} of ${tasks.length} tasks`;

  // Handle empty state display
  if (filteredTasks.length === 0) {
    tasksTableBody.innerHTML = '';
    emptyState.style.display = 'block';
    return;
  }

  emptyState.style.display = 'none';

  // Build table HTML
  tasksTableBody.innerHTML = filteredTasks
    .map(task => {
      const priorityClass = getPriorityBadgeClass(task.priority);
      const statusClass = getStatusBadgeClass(task.status);
      const formattedDate = formatDate(task.dueDate);

      return `
        <tr data-id="${task.id}">
          <td class="task-name-cell">${escapeHtml(task.name)}</td>
          <td>
            <span class="project-tag">${escapeHtml(task.project || 'General')}</span>
          </td>
          <td>
            <span class="badge ${priorityClass}">${escapeHtml(task.priority)}</span>
          </td>
          <td>${formattedDate}</td>
          <td>
            <span class="badge ${statusClass}">
              <span class="status-dot"></span>
              ${escapeHtml(task.status)}
            </span>
          </td>
          <td class="text-right">
            <div class="table-actions">
              <button 
                class="action-btn edit-task-btn" 
                data-id="${task.id}" 
                title="Edit Task"
                aria-label="Edit task"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                </svg>
              </button>
              <button 
                class="action-btn delete-btn delete-task-btn" 
                data-id="${task.id}" 
                title="Delete Task"
                aria-label="Delete task"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
              </button>
            </div>
          </td>
        </tr>
      `;
    })
    .join('');
}

// Render project overview grid in the "Projects" tab
function renderProjectsGrid() {
  if (!projectsGrid) return;

  const projectMap = {};
  tasks.forEach(task => {
    const proj = task.project || 'General';
    if (!projectMap[proj]) {
      projectMap[proj] = { total: 0, completed: 0, pending: 0, inProgress: 0 };
    }
    projectMap[proj].total++;
    if (task.status === 'Completed') projectMap[proj].completed++;
    else if (task.status === 'In Progress') projectMap[proj].inProgress++;
    else projectMap[proj].pending++;
  });

  const projectNames = Object.keys(projectMap);

  if (projectNames.length === 0) {
    projectsGrid.innerHTML = `<p class="text-muted">No projects currently tracked.</p>`;
    return;
  }

  projectsGrid.innerHTML = projectNames
    .map(name => {
      const stats = projectMap[name];
      const progressPercent = Math.round((stats.completed / stats.total) * 100);

      return `
        <div class="project-box">
          <div class="project-box-header">
            <span class="project-box-title">${escapeHtml(name)}</span>
            <span class="badge badge-neutral">${stats.total} Tasks</span>
          </div>
          <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 8px;">
            Completed: ${stats.completed} &bull; Active: ${stats.inProgress + stats.pending}
          </div>
          <div style="background: #e2e8f0; height: 6px; border-radius: 999px; overflow: hidden;">
            <div style="background: var(--primary); height: 100%; width: ${progressPercent}%;"></div>
          </div>
          <div style="text-align: right; font-size: 11px; color: var(--text-muted); margin-top: 4px;">
            ${progressPercent}% Done
          </div>
        </div>
      `;
    })
    .join('');
}

// ==========================================
// 6. CRUD Actions (Create, Read, Update, Delete)
// ==========================================
function openAddModal() {
  modalTitle.textContent = 'Add New Task';
  taskForm.reset();
  taskIdInput.value = '';
  setDefaultDueDate();
  taskPriorityInput.value = 'Medium';
  taskStatusInput.value = 'Pending';
  taskProjectInput.value = 'Core Startup';
  
  openModal();
  taskNameInput.focus();
}

function openEditModal(taskId) {
  const taskToEdit = tasks.find(t => t.id === taskId);
  if (!taskToEdit) return;

  modalTitle.textContent = 'Edit Task';
  taskIdInput.value = taskToEdit.id;
  taskNameInput.value = taskToEdit.name;
  taskProjectInput.value = taskToEdit.project || '';
  taskDueDateInput.value = taskToEdit.dueDate || '';
  taskPriorityInput.value = taskToEdit.priority || 'Medium';
  taskStatusInput.value = taskToEdit.status || 'Pending';

  openModal();
  taskNameInput.focus();
}

function handleTaskFormSubmit(e) {
  e.preventDefault();

  const id = taskIdInput.value;
  const name = taskNameInput.value.trim();
  const project = taskProjectInput.value.trim() || 'General';
  const dueDate = taskDueDateInput.value;
  const priority = taskPriorityInput.value;
  const status = taskStatusInput.value;

  if (!name) {
    showToast('Please enter a task name!');
    taskNameInput.focus();
    return;
  }

  if (!dueDate) {
    showToast('Please select a due date.');
    taskDueDateInput.focus();
    return;
  }

  if (id) {
    // Updating existing task
    const taskIndex = tasks.findIndex(t => t.id === id);
    if (taskIndex !== -1) {
      tasks[taskIndex] = {
        ...tasks[taskIndex],
        name,
        project,
        dueDate,
        priority,
        status
      };
      showToast('Task updated successfully!');
    }
  } else {
    // Creating new task
    const newTask = {
      id: Date.now().toString(),
      name,
      project,
      dueDate,
      priority,
      status
    };
    tasks.unshift(newTask); // Add to top of list
    showToast(`Task "${name}" created successfully!`);
  }

  saveTasksToStorage();
  renderDashboard();
  closeModal();
}

function deleteTask(taskId) {
  const task = tasks.find(t => t.id === taskId);
  const taskName = task ? task.name : 'this task';

  const confirmDelete = confirm(`Are you sure you want to delete "${taskName}"?`);
  if (!confirmDelete) return;

  tasks = tasks.filter(t => t.id !== taskId);
  saveTasksToStorage();
  renderDashboard();
  showToast('Task deleted successfully.');
}

// ==========================================
// 7. Modal & Toast Utilities
// ==========================================
function openModal() {
  taskModal.classList.add('open');
  taskModal.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden'; // Prevent background scrolling
}

function closeModal() {
  taskModal.classList.remove('open');
  taskModal.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
}

let toastTimeout;
function showToast(message) {
  toastMessage.textContent = message;
  toastNotification.classList.add('show');

  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => {
    toastNotification.classList.remove('show');
  }, 3000);
}

// Helper: Badge classes
function getPriorityBadgeClass(priority) {
  switch (priority) {
    case 'High': return 'priority-high';
    case 'Medium': return 'priority-medium';
    case 'Low': return 'priority-low';
    default: return 'priority-medium';
  }
}

function getStatusBadgeClass(status) {
  switch (status) {
    case 'Completed': return 'status-complete';
    case 'In Progress': return 'status-progress';
    case 'Pending': return 'status-pending';
    default: return 'status-pending';
  }
}

// Format YYYY-MM-DD to readable format
function formatDate(dateStr) {
  if (!dateStr) return 'No due date';
  const parts = dateStr.split('-');
  if (parts.length !== 3) return dateStr;
  
  const dateObj = new Date(parts[0], parts[1] - 1, parts[2]);
  return dateObj.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
}

// Prevent HTML injection from user input
function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ==========================================
// 8. Event Listeners Setup
// ==========================================
function setupEventListeners() {
  // Add task buttons
  openAddTaskModalBtn.addEventListener('click', openAddModal);
  emptyStateAddBtn.addEventListener('click', openAddModal);

  // Close modal buttons
  closeModalBtn.addEventListener('click', closeModal);
  cancelModalBtn.addEventListener('click', closeModal);

  // Close modal on click outside content
  taskModal.addEventListener('click', (e) => {
    if (e.target === taskModal) {
      closeModal();
    }
  });

  // Close modal on ESC key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && taskModal.classList.contains('open')) {
      closeModal();
    }
  });

  // Task form submission
  taskForm.addEventListener('submit', handleTaskFormSubmit);

  // Single delegated listener for task action buttons (Edit & Delete)
  tasksTableBody.addEventListener('click', (e) => {
    const editBtn = e.target.closest('.edit-task-btn');
    if (editBtn) {
      openEditModal(editBtn.getAttribute('data-id'));
      return;
    }

    const deleteBtn = e.target.closest('.delete-task-btn');
    if (deleteBtn) {
      deleteTask(deleteBtn.getAttribute('data-id'));
      return;
    }
  });

  // Live search & filters
  searchInput.addEventListener('input', () => {
    renderTasksTable();
  });

  statusFilter.addEventListener('change', () => {
    renderTasksTable();
  });

  priorityFilter.addEventListener('change', () => {
    renderTasksTable();
  });

  resetFiltersBtn.addEventListener('click', () => {
    searchInput.value = '';
    statusFilter.value = 'all';
    priorityFilter.value = 'all';
    renderTasksTable();
    showToast('Filters cleared');
  });

  // Mobile sidebar drawer
  openSidebarBtn.addEventListener('click', () => {
    sidebar.classList.add('open');
    sidebarOverlay.classList.add('open');
  });

  function closeMobileSidebar() {
    sidebar.classList.remove('open');
    sidebarOverlay.classList.remove('open');
  }

  closeSidebarBtn.addEventListener('click', closeMobileSidebar);
  sidebarOverlay.addEventListener('click', closeMobileSidebar);

  // Sidebar navigation switching
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      const targetView = link.getAttribute('data-view');
      switchView(targetView);

      // On mobile, close drawer after clicking link
      closeMobileSidebar();
    });
  });

  // Settings Actions
  if (loadSampleDataBtn) {
    loadSampleDataBtn.addEventListener('click', () => {
      tasks = [...INITIAL_TASKS];
      saveTasksToStorage();
      renderDashboard();
      showToast('Loaded demo startup tasks!');
      switchView('dashboard');
    });
  }

  if (clearAllDataBtn) {
    clearAllDataBtn.addEventListener('click', () => {
      const confirmClear = confirm('Are you sure you want to erase ALL tasks? This cannot be undone.');
      if (confirmClear) {
        tasks = [];
        saveTasksToStorage();
        renderDashboard();
        showToast('All tasks cleared.');
      }
    });
  }
}

// Switch view between Dashboard, Projects, Tasks, and Settings
function switchView(viewName) {
  // Update nav link active state
  navLinks.forEach(link => {
    link.classList.toggle('active', link.getAttribute('data-view') === viewName);
  });

  // Update page title
  switch (viewName) {
    case 'dashboard':
    case 'tasks':
      pageTitle.textContent = viewName === 'tasks' ? 'Tasks Backlog' : 'Startup Dashboard';
      break;
    case 'projects':
      pageTitle.textContent = 'Projects & Initiatives';
      break;
    case 'settings':
      pageTitle.textContent = 'Settings & Workspace';
      break;
  }

  // Display target view section
  const targetViewId = viewName === 'tasks' ? 'dashboardView' : `${viewName}View`;
  contentViews.forEach(view => {
    view.classList.toggle('active', view.id === targetViewId);
  });

  // Smooth navigation scroll
  if (viewName === 'tasks') {
    const tasksCard = document.querySelector('.tasks-card');
    if (tasksCard) {
      tasksCard.scrollIntoView({ behavior: 'smooth' });
      return;
    }
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
