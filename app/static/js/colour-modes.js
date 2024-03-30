/*!
 * Color mode toggler for Bootstrap's docs (https://getbootstrap.com/)
 * Copyright 2011-2023 The Bootstrap Authors
 * Licensed under the Creative Commons Attribution 3.0 Unported License.
 */

(() => {
  'use strict';

  const themeButtonIcon = document.querySelector('#bd-theme .theme-icon-active'); // Selector for the icon on the toggle button

  const getStoredTheme = () => localStorage.getItem('theme');
  const setStoredTheme = theme => localStorage.setItem('theme', theme);

  const getPreferredTheme = () => {
    const storedTheme = getStoredTheme();
    if (storedTheme) {
      return storedTheme;
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  };

  const setTheme = theme => {
    if (theme === 'auto') {
      document.documentElement.setAttribute('data-bs-theme', (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
    } else {
      document.documentElement.setAttribute('data-bs-theme', theme);
    }
    updateThemeButtonIcon(theme); // Update the theme icon on the button
  };

  const updateThemeButtonIcon = (theme) => {
    switch (theme) {
      case 'light':
        themeButtonIcon.className = 'bi bi-sun-fill my-1 theme-icon-active';
        break;
      case 'dark':
        themeButtonIcon.className = 'bi bi-moon-stars-fill my-1 theme-icon-active';
        break;
      case 'auto':
        themeButtonIcon.className = 'bi bi-circle-half my-1 theme-icon-active';
        break;
      default:
        themeButtonIcon.className = 'bi bi-circle-half my-1 theme-icon-active'; // Default to auto icon if unsure
    }
  };

  setTheme(getPreferredTheme());

  const showActiveTheme = (theme, focus = false) => {
    const themeSwitcher = document.querySelector('#bd-theme');
    if (!themeSwitcher) {
      return;
    }

    document.querySelectorAll('[data-bs-theme-value]').forEach(element => {
      element.classList.remove('active');
      element.setAttribute('aria-pressed', 'false');
    });

    const btnToActive = document.querySelector(`[data-bs-theme-value="${theme}"]`);
    btnToActive.classList.add('active');
    btnToActive.setAttribute('aria-pressed', 'true');

    if (focus) {
      themeSwitcher.focus();
    }
  };

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const storedTheme = getStoredTheme();
    if (storedTheme !== 'light' && storedTheme !== 'dark') {
      setTheme(getPreferredTheme());
    }
  });

  window.addEventListener('DOMContentLoaded', () => {
    showActiveTheme(getPreferredTheme());

    document.querySelectorAll('[data-bs-theme-value]')
      .forEach(toggle => {
        toggle.addEventListener('click', (event) => {
          const theme = toggle.getAttribute('data-bs-theme-value');
          setStoredTheme(theme);
          setTheme(theme);
          showActiveTheme(theme, true);
          event.preventDefault(); // Prevent the dropdown from showing automatically
        });
      });
  });
})();
