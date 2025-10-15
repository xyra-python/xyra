// Menu Toggle Functionality
const menuBtn = document.getElementById('menuBtn');
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('overlay');

function toggleMenu() {
  menuBtn.classList.toggle('active');
  sidebar.classList.toggle('active');
  overlay.classList.toggle('active');
  document.body.style.overflow = sidebar.classList.contains('active') ? 'hidden' : '';
}

if (menuBtn) {
  menuBtn.addEventListener('click', toggleMenu);
}
if (overlay) {
  overlay.addEventListener('click', toggleMenu);
}

// Close menu when clicking nav links on mobile
document.querySelectorAll('.nav-link').forEach(link => {
  link.addEventListener('click', () => {
    if (window.innerWidth < 1024) {
      toggleMenu();
    }
  });
});

// Active Navigation Link
document.addEventListener('DOMContentLoaded', function () {
  const currentPath = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });
});

// Copy Code Functionality
function copyCode(button) {
  const codeContainer = button.closest('.code-container');
  const codeBlock = codeContainer.querySelector('code');
  const text = codeBlock.textContent;

  navigator.clipboard.writeText(text).then(() => {
    // Change button text and style
    const originalHTML = button.innerHTML;
    button.innerHTML = `
      <svg fill="currentColor" viewBox="0 0 24 24">
        <path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127-.075l-4.5-6a.75.75 0 011.302-.825l3.8 5.05L16.56 4.296a.75.75 0 011.145-.143z" clip-rule="evenodd"/>
      </svg>
      Copied!
    `;
    button.classList.add('copied');

    // Reset after 2 seconds
    setTimeout(() => {
      button.innerHTML = originalHTML;
      button.classList.remove('copied');
    }, 2000);
  }).catch(err => {
    console.error('Failed to copy code:', err);
    alert('Failed to copy code');
  });
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});