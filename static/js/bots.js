document.addEventListener('DOMContentLoaded', function() {

    //удал
    const deleteButtons = document.querySelectorAll('.delete-bot');
    const deleteModal = document.getElementById('deleteModal');
    const deleteForm = document.getElementById('deleteForm');
    const deleteBotName = document.getElementById('deleteBotName');
    const closeModal = document.querySelectorAll('.close-modal');

    if (deleteButtons.length) {
        deleteButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const botId = this.dataset.botId;
                const botName = this.dataset.botName;

                if (deleteForm) {
                    deleteForm.action = `/bot/${botId}/delete`;
                }
                if (deleteBotName) {
                    deleteBotName.textContent = `"${botName}"`;
                }
                if (deleteModal) {
                    deleteModal.style.display = 'block';
                }
            });
        });
    }

    //закрытие модалки
    closeModal.forEach(btn => {
        btn.addEventListener('click', function() {
            if (deleteModal) {
                deleteModal.style.display = 'none';
            }
        });
    });

    //закрытие по клику вне модалки
    window.addEventListener('click', function(e) {
        if (e.target === deleteModal) {
            deleteModal.style.display = 'none';
        }
    });

    //перезап бот
    document.querySelectorAll('.restart-bot').forEach(btn => {
        btn.addEventListener('click', function() {
            const botId = this.dataset.botId;

            if (confirm('Перезапустить бота?')) {
                fetch(`/bot/${botId}/restart`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showNotification('Бот перезапущен', 'success');
                        // Обновляем статус
                        const statusBadge = document.querySelector(`.bot-card[data-bot-id="${botId}"] .bot-status`);
                        if (statusBadge) {
                            statusBadge.className = 'bot-status status-running';
                            statusBadge.textContent = 'running';
                        }
                    } else {
                        showNotification('Ошибка при перезапуске', 'error');
                    }
                })
                .catch(() => {
                    showNotification('Ошибка соединения', 'error');
                });
            }
        });
    });

    //копи токен
    document.querySelectorAll('.copy-token').forEach(btn => {
        btn.addEventListener('click', function() {
            const token = this.dataset.token;

            navigator.clipboard.writeText(token).then(() => {
                showNotification('Токен скопирован', 'success');
            }).catch(() => {
                showNotification('Ошибка при копировании', 'error');
            });
        });
    });

    //фильтр
    const filterInput = document.getElementById('botFilter');
    const platformFilter = document.getElementById('platformFilter');
    const typeFilter = document.getElementById('typeFilter');

    function filterBots() {
        const searchText = filterInput?.value.toLowerCase() || '';
        const platform = platformFilter?.value || 'all';
        const type = typeFilter?.value || 'all';

        document.querySelectorAll('.bot-card').forEach(card => {
            const name = card.querySelector('h3').textContent.toLowerCase();
            const cardPlatform = card.dataset.platform;
            const cardType = card.dataset.type;

            const matchesSearch = name.includes(searchText);
            const matchesPlatform = platform === 'all' || cardPlatform === platform;
            const matchesType = type === 'all' || cardType === type;

            if (matchesSearch && matchesPlatform && matchesType) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }

    if (filterInput) filterInput.addEventListener('input', filterBots);
    if (platformFilter) platformFilter.addEventListener('change', filterBots);
    if (typeFilter) typeFilter.addEventListener('change', filterBots);

    //увед
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button class="notification-close">&times;</button>
        `;

        document.body.appendChild(notification);

        //крытие через 3 секунды
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);

        //закрытие по кнопке
        notification.querySelector('.notification-close').addEventListener('click', function() {
            notification.remove();
        });
    }
});