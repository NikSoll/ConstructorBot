document.addEventListener('DOMContentLoaded', function() {

    //вкладки
    const tabLinks = document.querySelectorAll('.profile-menu a[data-tab]');
    const tabs = document.querySelectorAll('.tab-content');

    if (tabLinks.length) {
        tabLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();

                //убираем активный класс у всех ссылок
                tabLinks.forEach(l => l.classList.remove('active'));
                this.classList.add('active');

                //скрываем все табы
                tabs.forEach(tab => tab.classList.remove('active'));

                //показываем нужный таб
                const tabId = this.dataset.tab + '-tab';
                document.getElementById(tabId).classList.add('active');

                //обновляем URL без перезагрузки
                history.pushState(null, '', '#' + this.dataset.tab);
            });
        });

        //hash in URL
        if (window.location.hash) {
            const hash = window.location.hash.substring(1);
            const link = document.querySelector(`.profile-menu a[data-tab="${hash}"]`);
            if (link) link.click();
        }
    }

    //валид форм
    const registerForm = document.getElementById('registerForm');

    if (registerForm) {
        const password = document.getElementById('password');
        const password2 = document.getElementById('password2');
        const submitBtn = document.getElementById('submitBtn');
        const lengthReq = document.getElementById('lengthReq');
        const numberReq = document.getElementById('numberReq');
        const letterReq = document.getElementById('letterReq');
        const matchError = document.getElementById('matchError');

        function checkPasswordStrength() {
            const pwd = password.value;
            let valid = true;

            //лина
            if (pwd.length >= 6) {
                lengthReq.innerHTML = 'Минимум 6 символов';
                lengthReq.classList.add('valid');
                lengthReq.classList.remove('invalid');
            } else {
                lengthReq.innerHTML = 'Минимум 6 символов';
                lengthReq.classList.add('invalid');
                lengthReq.classList.remove('valid');
                valid = false;
            }

            //цфры
            if (/\d/.test(pwd)) {
                numberReq.innerHTML = 'Хотя бы одна цифра';
                numberReq.classList.add('valid');
                numberReq.classList.remove('invalid');
            } else {
                numberReq.innerHTML = 'Хотя бы одна цифра';
                numberReq.classList.add('invalid');
                numberReq.classList.remove('valid');
                valid = false;
            }

            //буквы
            if (/[a-zA-Zа-яА-Я]/.test(pwd)) {
                letterReq.innerHTML = 'Хотя бы одна буква';
                letterReq.classList.add('valid');
                letterReq.classList.remove('invalid');
            } else {
                letterReq.innerHTML = 'Хотя бы одна буква';
                letterReq.classList.add('invalid');
                letterReq.classList.remove('valid');
                valid = false;
            }

            return valid;
        }

        function checkPasswordMatch() {
            if (!password2.value) {
                matchError.textContent = '';
                return true;
            }

            if (password.value !== password2.value) {
                matchError.textContent = 'Пароли не совпадают';
                return false;
            } else {
                matchError.textContent = '';
                return true;
            }
        }

        function validateForm() {
            const strengthValid = checkPasswordStrength();
            const matchValid = checkPasswordMatch();

            const username = document.getElementById('username')?.value;
            const email = document.getElementById('email')?.value;

            const fieldsFilled = username && email && password.value && password2.value;

            submitBtn.disabled = !(strengthValid && matchValid && fieldsFilled);
        }

        password.addEventListener('input', validateForm);
        password2.addEventListener('input', validateForm);
        document.getElementById('username')?.addEventListener('input', validateForm);
        document.getElementById('email')?.addEventListener('input', validateForm);
    }

    //валид форм
    const loginForm = document.getElementById('loginForm');

    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            const email = document.getElementById('email');
            const password = document.getElementById('password');
            const emailError = document.getElementById('emailError');
            const passwordError = document.getElementById('passwordError');

            let isValid = true;

            //валид email
            if (!email.value.includes('@') || !email.value.includes('.')) {
                emailError.textContent = 'Введите корректный email';
                email.classList.add('is-invalid');
                isValid = false;
            } else {
                emailError.textContent = '';
                email.classList.remove('is-invalid');
            }

            // Проверка пароля
            if (password.value.length < 6) {
                passwordError.textContent = 'Пароль должен быть минимум 6 символов';
                password.classList.add('is-invalid');
                isValid = false;
            } else {
                passwordError.textContent = '';
                password.classList.remove('is-invalid');
            }

            if (!isValid) {
                e.preventDefault();
            }
        });
    }

    //форма проф
    const profileForm = document.getElementById('profileForm');

    if (profileForm) {
        const newPassword = document.getElementById('newPassword');
        const confirmPassword = document.getElementById('confirmPassword');
        const matchError = document.getElementById('matchError');

        if (newPassword && confirmPassword) {
            function checkPasswords() {
                if (newPassword.value || confirmPassword.value) {
                    if (newPassword.value !== confirmPassword.value) {
                        matchError.textContent = 'Пароли не совпадают';
                        return false;
                    } else {
                        matchError.textContent = '';
                        return true;
                    }
                }
                return true;
            }

            newPassword.addEventListener('input', checkPasswords);
            confirmPassword.addEventListener('input', checkPasswords);
        }
    }

    //удал акк
    const deleteBtn = document.getElementById('deleteAccountBtn');
    const deleteModal = document.getElementById('deleteModal');
    const closeModal = document.querySelectorAll('.close-modal');

    if (deleteBtn && deleteModal) {
        deleteBtn.addEventListener('click', function() {
            deleteModal.style.display = 'block';
        });

        closeModal.forEach(btn => {
            btn.addEventListener('click', function() {
                deleteModal.style.display = 'none';
            });
        });

        window.addEventListener('click', function(e) {
            if (e.target === deleteModal) {
                deleteModal.style.display = 'none';
            }
        });
    }

    //сейв настрой
    const saveSettings = document.getElementById('saveSettings');

    if (saveSettings) {
        saveSettings.addEventListener('click', function() {
            // сюда AJAX для сейва
            const emailNotif = document.getElementById('emailNotifications').checked;
            const botNotif = document.getElementById('botNotifications').checked;
            const language = document.getElementById('language').value;

            //увед показ
            showNotification('Настройки сохранены', 'success');
        });
    }

    //увед
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button class="notification-close">&times;</button>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);

        notification.querySelector('.notification-close').addEventListener('click', function() {
            notification.remove();
        });
    }
});