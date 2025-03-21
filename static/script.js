const toggleButton = document.getElementById('theme-toggle');
const body = document.body;

toggleButton.addEventListener('click', () => {
    body.dataset.theme = body.dataset.theme === 'light' ? 'dark' : 'light';
});