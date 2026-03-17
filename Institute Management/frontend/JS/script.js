function goToLogin() {
    window.location.href = "/login";
}

// BACKGROUND PARTICLES ANIMATION
document.addEventListener("DOMContentLoaded", function () {
    const welcomeSection = document.querySelector('.welcome');

    // Create floating particles
    for (let i = 0; i < 30; i++) {
        let particle = document.createElement('div');
        particle.className = 'bg-particle';

        // Random Position
        let x = Math.random() * 100;
        let y = Math.random() * 100;

        // Random Size
        let size = Math.random() * 15 + 5;

        // Random Duration
        let duration = Math.random() * 10 + 10;

        // Random Delay
        let delay = Math.random() * 5;

        particle.style.left = x + '%';
        particle.style.top = y + '%';
        particle.style.width = size + 'px';
        particle.style.height = size + 'px';
        particle.style.animationDuration = duration + 's';
        particle.style.animationDelay = delay + 's';

        welcomeSection.appendChild(particle);
    }
});
