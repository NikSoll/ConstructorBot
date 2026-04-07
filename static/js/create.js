document.addEventListener('DOMContentLoaded', function() {
    console.log(' Create.js загружен');

    const platform = document.body.dataset.platform || 'tg';
    const botType = document.body.dataset.botType || '';

    function setupAddButton(btnId, containerId, templateId, callback) {
        const btn = document.getElementById(btnId);
        if (btn) {
            btn.addEventListener('click', function() {
                const container = document.getElementById(containerId);
                const template = document.getElementById(templateId);

                if (container && template) {
                    const clone = template.content.cloneNode(true);
                    container.appendChild(clone);

                    if (callback) callback(container.lastElementChild);
                }
            });
        }
    }

    //удал элем
    document.addEventListener('click', function(e) {
    if (e.target.classList.contains('remove-item')) {
        const item = e.target.closest('.array-item, .master-item, .service-item, .product-item, .category-item, .question-item, .result-item, .group-item');
        if (item) {
            item.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                item.remove();
            }, 250);
        }
    }
});

    //запись
    if (botType === 'make') {
        setupAddButton('add-master', 'masters-container', 'master-template', function(item) {
            console.log('Мастер добавлен');
        });

        setupAddButton('add-service', 'services-container', 'service-template', function(item) {
            console.log('Услуга добавлена');
        });

        //примеры если пусто
        setTimeout(() => {
            const mastersContainer = document.getElementById('masters-container');
            if (mastersContainer && mastersContainer.children.length === 0) {
                for (let i = 0; i < 3; i++) {
                    document.getElementById('add-master')?.click();
                }
            }

            const servicesContainer = document.getElementById('services-container');
            if (servicesContainer && servicesContainer.children.length === 0) {
                for (let i = 0; i < 3; i++) {
                    document.getElementById('add-service')?.click();
                }
            }
        }, 100);
    }

    //магазин
    if (botType === 'shop') {
        setupAddButton('add-category', 'categories-container', 'category-template');
        setupAddButton('add-product', 'products-container', 'product-template');

        //+ примеры
        setTimeout(() => {
            const catsContainer = document.getElementById('categories-container');
            if (catsContainer && catsContainer.children.length === 0) {
                const catBtn = document.getElementById('add-category');
                if (catBtn) {
                    catBtn.click();
                    catBtn.click();
                }
            }

            const prodsContainer = document.getElementById('products-container');
            if (prodsContainer && prodsContainer.children.length === 0) {
                const prodBtn = document.getElementById('add-product');
                if (prodBtn) {
                    prodBtn.click();
                    prodBtn.click();
                    prodBtn.click();
                }
            }
        }, 100);
    }

    //квиз
    if (botType === 'quiz') {
        setupAddButton('add-question', 'questions-container', 'question-template');
        setupAddButton('add-result', 'results-container', 'result-template');
    }

    //опросник
    if (botType === 'survey') {
        setupAddButton('add-question', 'questions-container', 'question-template');

        //логика зависимости от типа вопроса
        document.addEventListener('change', function(e) {
            if (e.target.name === 'question_type[]') {
                const item = e.target.closest('.question-item');
                if (!item) return;

                const optionsField = item.querySelector('.options-field');
                const scaleFields = item.querySelector('.scale-fields');

                if (optionsField) {
                    optionsField.style.display =
                        (e.target.value === 'single' || e.target.value === 'multiple') ? 'block' : 'none';
                }
                if (scaleFields) {
                    scaleFields.style.display =
                        e.target.value === 'scale' ? 'block' : 'none';
                }
            }
        });
    }

    //рассльщик
    if (botType === 'mailer') {
        setupAddButton('add-group', 'groups-container', 'group-template');
    }

    //гугл щит
    const useSheets = document.getElementById('useSheets');
    const sheetsSettings = document.getElementById('sheets-settings');

    if (useSheets && sheetsSettings) {
        useSheets.addEventListener('change', function() {
            sheetsSettings.style.display = this.checked ? 'block' : 'none';
        });
    }

    //валид форм
    const botForm = document.getElementById('botForm');

    if (botForm) {
        botForm.addEventListener('submit', function(e) {
            const requiredFields = botForm.querySelectorAll('[required]');
            let valid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('error');
                    valid = false;

                    //прокрутка к первой ошибке
                    if (valid === false) {
                        field.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                } else {
                    field.classList.remove('error');
                }
            });

            if (!valid) {
                e.preventDefault();
                showNotification('Заполните все обязательные поля', 'error');
            }
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

    //анимац
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideOut {
            from {
                opacity: 1;
                transform: translateX(0);
            }
            to {
                opacity: 0;
                transform: translateX(100%);
            }
        }
        
        @keyframes slideOutRight {
            from {
                opacity: 1;
                transform: translateX(0);
            }
            to {
                opacity: 0;
                transform: translateX(100%);
            }
        }
    `;
    document.head.appendChild(style);
});