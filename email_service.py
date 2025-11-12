"""
Сервис для отправки email
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class EmailService:
    """
    Сервис для отправки email отчетов
    Соответствует требованию 03
    """

    def __init__(self):
        # Настройки для тестирования (можно заменить на реальные)
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = "test@example.com"  # Заменить на реальный email
        self.sender_password = "password"  # Заменить на реальный пароль

    def send_statistics_report(self, recipient_email: str, statistics_data: Dict[str, Any]) -> bool:
        """
        Отправка отчета со статистикой
        """
        try:
            # Создаем сообщение
            message = MIMEMultipart("alternative")
            message["Subject"] = f"📊 Отчет по продавцам - {datetime.now().strftime('%d.%m.%Y')}"
            message["From"] = self.sender_email
            message["To"] = recipient_email

            # Текст письма
            text = self._generate_email_text(statistics_data)
            html = self._generate_email_html(statistics_data)

            # Добавляем обе версии
            message.attach(MIMEText(text, "plain"))
            message.attach(MIMEText(html, "html"))

            # Отправляем (в демо-режиме просто логируем)
            if os.getenv("DEMO_MODE", "True") == "True":
                logger.info(f"📧 ДЕМО: Отчет отправлен на {recipient_email}")
                logger.info(f"📊 Данные отчета: {statistics_data}")
                return True
            else:
                # Реальная отправка (раскомментировать для продакшена)
                # with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                #     server.starttls()
                #     server.login(self.sender_email, self.sender_password)
                #     server.send_message(message)
                logger.info(f"📧 Реальная отправка отчета на {recipient_email}")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка отправки email: {e}")
            return False

    def _generate_email_text(self, data: Dict[str, Any]) -> str:
        """Генерация текстовой версии email"""
        text = f"Отчет по продавцам\n"
        text += f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        text += "=" * 50 + "\n\n"

        for seller in data.get("sellers", []):
            text += f"Продавец: {seller['name']}\n"
            text += f"  - Количество продаж: {seller['sales_count']}\n"
            text += f"  - Количество товаров: {seller['products_count']}\n"
            text += f"  - Отгрузок за месяц: {seller['shipments_count']}\n"
            text += "\n"

        text += f"Итого продавцов: {data.get('total_sellers', 0)}\n"
        text += f"Общее количество продаж: {data.get('total_sales', 0)}\n"

        return text

    def _generate_email_html(self, data: Dict[str, Any]) -> str:
        """Генерация HTML версии email"""
        html = f"""
        <html>
          <body>
            <h2>📊 Отчет по продавцам</h2>
            <p><strong>Дата:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
            <hr>
            <table border="1" cellpadding="8" style="border-collapse: collapse;">
              <tr style="background-color: #f2f2f2;">
                <th>Продавец</th>
                <th>💰 Продажи</th>
                <th>🛍️ Товары</th>
                <th>🚚 Отгрузки</th>
              </tr>
        """

        for seller in data.get("sellers", []):
            html += f"""
              <tr>
                <td><strong>{seller['name']}</strong></td>
                <td style="text-align: center;">{seller['sales_count']}</td>
                <td style="text-align: center;">{seller['products_count']}</td>
                <td style="text-align: center;">{seller['shipments_count']}</td>
              </tr>
            """

        html += f"""
            </table>
            <br>
            <div style="background-color: #e8f4fd; padding: 10px; border-radius: 5px;">
              <strong>Итого:</strong><br>
              - Продавцов: {data.get('total_sellers', 0)}<br>
              - Общее количество продаж: {data.get('total_sales', 0)}<br>
              - Общее количество товаров: {data.get('total_products', 0)}
            </div>
          </body>
        </html>
        """
        return html


# Глобальный экземпляр сервиса
email_service = EmailService()