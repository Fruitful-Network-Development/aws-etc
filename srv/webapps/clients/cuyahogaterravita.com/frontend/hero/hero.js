// hero/hero.js
// Hero-specific initialization logic

document.addEventListener('componentsLoaded', () => {
  const learnMoreBtn = document.getElementById('learn-more-btn');
  const csaSignupBtn = document.querySelector('.hero-button[type="secondary"]:not(#learn-more-btn)');

  if (learnMoreBtn) {
    learnMoreBtn.addEventListener('click', () => {
      console.log('Learn More clicked');
      // TODO: scroll or navigate to more info section
    });
  }

  if (csaSignupBtn) {
    csaSignupBtn.addEventListener('click', () => {
      console.log('CSA Sign-Up clicked (hero)');
      // TODO: open CSA sign-up form / modal
    });
  }
});
