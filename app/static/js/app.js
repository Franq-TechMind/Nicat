console.log('NICAT School Management System ready.');

// Mobile menu toggle
const menuToggle = document.getElementById('menu-toggle');
const navMenu = document.querySelector('.nav-menu');

if (menuToggle && navMenu) {
  menuToggle.addEventListener('click', () => {
    navMenu.classList.toggle('mobile-open');
  });

  // Close menu when clicking outside
  document.addEventListener('click', (e) => {
    if (!menuToggle.contains(e.target) && !navMenu.contains(e.target)) {
      navMenu.classList.remove('mobile-open');
    }
  });
}

document.querySelectorAll('form').forEach((form) => {
  form.setAttribute('autocomplete', 'on');
});

document.addEventListener('click', (event) => {
  const button = event.target.closest('.toggle-detail-btn');
  if (!button) return;
  const targetId = button.getAttribute('data-target');
  const row = document.getElementById(targetId);
  if (!row) return;
  row.style.display = row.style.display === 'table-row' ? 'none' : 'table-row';
});

// Floating Action Menu Toggle
const fabToggle = document.getElementById('fab-toggle');
const fabOptions = document.getElementById('fab-options');

if (fabToggle && fabOptions) {
  fabToggle.addEventListener('click', () => {
    fabToggle.classList.toggle('active');
    fabOptions.classList.toggle('active');
  });

  // Close FAB menu when clicking outside
  document.addEventListener('click', (e) => {
    if (!fabToggle.contains(e.target) && !fabOptions.contains(e.target)) {
      fabToggle.classList.remove('active');
      fabOptions.classList.remove('active');
    }
  });
}

function gradeFromScore(score) {
  if (score >= 70) return 'A';
  if (score >= 60) return 'B';
  if (score >= 50) return 'C';
  if (score >= 40) return 'D';
  return 'E';
}

function parseScore(value) {
  const n = parseFloat(value);
  return Number.isFinite(n) ? n : 0;
}

function updateModulePreviews() {
  const moduleCards = document.querySelectorAll('.module-card');
  let convertedSum = 0;
  let count = 0;

  moduleCards.forEach((card) => {
    const cat = parseScore(card.querySelector('.js-cat')?.value);
    const group = parseScore(card.querySelector('.js-group')?.value);
    const finalExam = parseScore(card.querySelector('.js-final')?.value);
    const raw = cat + group + finalExam;
    const converted = ((raw / 110) * 100);
    card.querySelector('.js-raw-total').textContent = `${raw.toFixed(2)} / 110`;
    card.querySelector('.js-converted-total').textContent = `${converted.toFixed(2)} / 100`;
    card.querySelector('.js-grade').textContent = gradeFromScore(converted);
    convertedSum += converted;
    count += 1;
  });

  const overall = count ? (convertedSum / count) : 0;
  const overallMark = document.getElementById('overall-mark');
  const overallGrade = document.getElementById('overall-grade');
  if (overallMark) overallMark.textContent = overall.toFixed(2);
  if (overallGrade) overallGrade.textContent = gradeFromScore(overall);
}

['input', 'change'].forEach((eventName) => {
  document.addEventListener(eventName, (event) => {
    if (event.target.matches('.js-cat, .js-group, .js-final')) {
      updateModulePreviews();
    }
  });
});

updateModulePreviews();

document.addEventListener('submit', (event) => {
  if (event.target && event.target.id === 'module-results-form') {
    const btn = document.getElementById('save-module-results-btn');
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Saving...';
    }
  }
});
