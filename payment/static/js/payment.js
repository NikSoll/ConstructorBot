document.addEventListener('DOMContentLoaded', function() {

    //форма оплат
    const paymentForm = document.getElementById('paymentForm');
    const payButton = document.getElementById('payButton');

    if (paymentForm) {
        paymentForm.addEventListener('submit', function(e) {
            //блок кнопку при отправке
            payButton.disabled = true;
            payButton.textContent = 'Перенаправление...';

            //увед
            showPaymentNotification('🔄 Перенаправляем на страницу оплаты...', 'info');
        });
    }

    //способ оплаты
    const paymentMethods = document.querySelectorAll('.payment-method-radio');

    paymentMethods.forEach(method => {
        method.addEventListener('change', function() {
            document.querySelectorAll('.payment-method-card').forEach(card => {
                card.style.borderColor = 'var(--border-color)';
                card.style.background = 'white';
            });

            //выдел карточк
            const parentCard = this.closest('.payment-method-card');
            if (parentCard) {
                parentCard.style.borderColor = 'var(--primary-color)';
                parentCard.style.background = '#f8fafc';
            }
        });
    });

    //увед
    function showPaymentNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `payment-notification ${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button class="notification-close">&times;</button>
        `;

        document.body.appendChild(notification);

        //анимация
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateY(0)';
        }, 10);

        //скрытие через 5 секунд
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);

        //закрытие по кнопке
        notification.querySelector('.notification-close').addEventListener('click', function() {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                notification.remove();
            }, 300);
        });
    }

    //история
    const checkPaymentStatus = async (paymentId) => {
        try {
            const response = await fetch(`/payment/status/${paymentId}`);
            const data = await response.json();

            if (data.status === 'paid') {
                // Обновляем отображение статуса
                const statusBadge = document.querySelector(`#payment-${paymentId} .status-badge`);
                if (statusBadge) {
                    statusBadge.className = 'status-badge status-paid';
                    statusBadge.textContent = '✅ Оплачено';
                }

                showPaymentNotification('✅ Платеж подтвержден!', 'success');
            }
        } catch (error) {
            console.error('Error checking payment status:', error);
        }
    };

    //увед
    const style = document.createElement('style');
    style.textContent = `
        .payment-notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            background: white;
            border-radius: 10px;
            box-shadow: var(--shadow-lg);
            display: flex;
            align-items: center;
            gap: 15px;
            z-index: 1000;
            opacity: 0;
            transform: translateY(-20px);
            transition: all 0.3s ease;
            border-left: 4px solid var(--primary-color);
            max-width: 350px;
        }
        
        .payment-notification.success {
            border-left-color: var(--success-color);
        }
        
        .payment-notification.error {
            border-left-color: var(--danger-color);
        }
        
        .payment-notification.info {
            border-left-color: var(--primary-color);
        }
        
        .notification-close {
            background: none;
            border: none;
            font-size: 1.2rem;
            cursor: pointer;
            color: var(--text-light);
            padding: 0 5px;
        }
        
        .notification-close:hover {
            color: var(--danger-color);
        }
    `;
    document.head.appendChild(style);
});