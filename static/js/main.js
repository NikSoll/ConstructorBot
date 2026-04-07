document.addEventListener('DOMContentLoaded', function() {

    //навиг дроп
    const navUser = document.querySelector('.nav-user');
    const dropdown = document.querySelector('.dropdown-content');

    if (navUser && dropdown) {
        navUser.addEventListener('click', function(e) {
            e.preventDefault();
            dropdown.classList.toggle('show');
        });

        //нажатие мимо закрытие
        window.addEventListener('click', function(e) {
            if (!e.target.matches('.nav-user')) {
                if (dropdown.classList.contains('show')) {
                    dropdown.classList.remove('show');
                }
            }
        });
    }

    //скрытие флэш
    const flashMessages = document.querySelectorAll('.flash-message');

    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            message.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });

    //копи
    document.querySelectorAll('[data-copy]').forEach(btn => {
        btn.addEventListener('click', function() {
            const text = this.dataset.copy;
            navigator.clipboard.writeText(text).then(() => {
                showTooltip(this, 'Скопировано!');
            });
        });
    });

    function showTooltip(element, message) {
        const tooltip = document.createElement('span');
        tooltip.className = 'tooltip';
        tooltip.textContent = message;

        element.style.position = 'relative';
        element.appendChild(tooltip);

        setTimeout(() => {
            tooltip.remove();
        }, 2000);
    }

    //анимац скрол
    const animatedElements = document.querySelectorAll('.animate-on-scroll');

    function checkScroll() {
        animatedElements.forEach(el => {
            const rect = el.getBoundingClientRect();
            const windowHeight = window.innerHeight;

            if (rect.top < windowHeight - 100) {
                el.classList.add('animated');
            }
        });
    }

    window.addEventListener('scroll', checkScroll);
    checkScroll(); //валид при загрузке
});


// выпад окно в навигац
document.addEventListener('DOMContentLoaded', function() {

    //закрыть при клик вне
    const dropdowns = document.querySelectorAll('.nav-dropdown');

    document.addEventListener('click', function(e) {
        dropdowns.forEach(dropdown => {
            if (!dropdown.contains(e.target)) {
                const content = dropdown.querySelector('.nav-dropdown-content');
                if (content) {
                }
            }
        });
    });

    const flashMessages = document.querySelectorAll('.flash-message');

    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            message.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });
});