from email.message import EmailMessage

from pydantic import EmailStr

from app.config import settings


def create_booking_confirmation_template(
        booking: dict,
        email_to: EmailStr,
):
    email = EmailMessage()

    email["Subject"] = "Подтверждение бронирования"
    email["From"] = settings.SMTP_USER
    email["To"] = email_to
    email.set_content(
        f"""
        <h1>Подтверждение бронирования</h1>
        Вы забронировали отель с {booking["date_from"]} по {booking["date_to"]}
        <p>Ваше бронирование подтверждено.</p>
        """,
        subtype="html"
    )
    return email

