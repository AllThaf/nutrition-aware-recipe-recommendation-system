// UI Helpers and Animations

// Toast notifier
export function showToast(message, type = 'success') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  // Icon based on type
  const icon = type === 'success' ? 'check-circle' : 'warning-circle';
  toast.innerHTML = `
    <i class="ph-bold ph-${icon}"></i>
    <span>${message}</span>
  `;
  
  container.appendChild(toast);
  
  // Trigger entry animation
  setTimeout(() => {
    toast.classList.add('show');
  }, 10);

  // Remove toast after duration
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => {
      toast.remove();
    }, 300);
  }, 3000);
}

// Fade in animation using IntersectionObserver
const fadeObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const el = entry.target;
      const delay = el.dataset.delay || 0;
      setTimeout(() => {
        el.style.opacity = 1;
        el.style.transform = 'translateY(0)';
      }, delay);
      fadeObserver.unobserve(el);
    }
  });
}, { threshold: 0.05 });

export function observeFadeIn(element, delayMs = 0) {
  element.style.opacity = 0;
  element.style.transform = 'translateY(12px)';
  element.style.transition = 'opacity 600ms cubic-bezier(0.16, 1, 0.3, 1), transform 600ms cubic-bezier(0.16, 1, 0.3, 1)';
  element.dataset.delay = delayMs;
  fadeObserver.observe(element);
}

// Stagger entry animation for child components
export function animateStagger(parentSelector, childSelector, baseDelay = 40) {
  const parent = document.querySelector(parentSelector);
  if (!parent) return;
  
  const children = parent.querySelectorAll(childSelector);
  children.forEach((child, index) => {
    observeFadeIn(child, index * baseDelay);
  });
}

// Nutrition score colour coding and progress bar renderer
export function getNutritionBarHtml(score) {
  let fillClass = 'fill-low';
  if (score >= 75) {
    fillClass = 'fill-high';
  } else if (score >= 50) {
    fillClass = 'fill-medium';
  }
  
  return `
    <div class="nutrition-track">
      <div class="nutrition-fill ${fillClass}" style="width: ${score}%"></div>
    </div>
  `;
}

// Render signal badge depending on CF/CBF/Nutrition
export function getSignalBadgeHtml(signal) {
  let badgeClass = 'badge-cf';
  let label = signal;
  
  if (signal === 'CF') {
    badgeClass = 'badge-cf';
    label = 'Collaborative Filtering';
  } else if (signal === 'CBF') {
    badgeClass = 'badge-cbf';
    label = 'Content-Based Filtering';
  } else if (signal === 'Nutrition') {
    badgeClass = 'badge-nutrition';
    label = 'Nutrition Score';
  } else if (signal === 'Cold Start') {
    badgeClass = 'badge-cold';
    label = 'Popularity Base';
  }
  
  return `<span class="badge ${badgeClass}">${label}</span>`;
}

export const ui = {
  toast: showToast,
  observeFadeIn,
  animateStagger,
  getNutritionBarHtml,
  getSignalBadgeHtml
};

