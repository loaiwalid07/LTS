/**
 * SaasWeb — Main JavaScript
 * Lightweight interactions for the luxury experience.
 */

document.addEventListener('DOMContentLoaded', () => {
  // ─── Mobile menu ──────────────────────────────────────
  const menuBtn = document.getElementById('mobile-menu-btn');
  const mobileMenu = document.getElementById('mobile-menu');

  if (menuBtn && mobileMenu) {
    menuBtn.addEventListener('click', () => {
      mobileMenu.classList.toggle('hidden');
    });

    // Close menu on link click
    mobileMenu.querySelectorAll('a, button').forEach((el) => {
      el.addEventListener('click', () => {
        mobileMenu.classList.add('hidden');
      });
    });
  }

  // ─── Auto-dismiss messages ────────────────────────────
  const messages = document.querySelectorAll('[role="alert"]');
  messages.forEach((msg) => {
    setTimeout(() => {
      msg.style.transition = 'opacity 0.4s ease';
      msg.style.opacity = '0';
      setTimeout(() => msg.remove(), 400);
    }, 5000);
  });
});
