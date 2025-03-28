import smtplib
import ssl
from email.message import EmailMessage

from app.settings.settings import NotificationsSettings

settings = NotificationsSettings()
SLL_DEFAULT_CONTEXT = ssl.create_default_context()


def load_file(file_path):
    with open("./assets/" + file_path, "r", encoding="utf-8") as file:
        return file.read()


def load_html(file_path):
    return load_file("email-templates/" + file_path)


def get_body_template():
    styles = load_html("styles.html")
    header = load_html("header.html")
    logo = load_file("logo.svg")
    header = header.replace("{{ logo }}", logo)

    footer = load_html("footer.html")
    body_template = load_html("body-template.html")

    body_filled = body_template.replace("{{ styles }}", styles)
    body_filled = body_filled.replace("{{ header }}", header)
    body_filled = body_filled.replace("{{ footer }}", footer)
    return body_filled


BODY_TEMPLATE = get_body_template()


class NotificationsService:
    def _send_email(self, message: EmailMessage):
        if not settings.ENABLE_SEND_EMAILS:
            print("not setting send emails")
            return
        message["From"] = settings.EMAIL
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", settings.SMTPS_PORT, context=SLL_DEFAULT_CONTEXT) as server:
                server.login(settings.EMAIL, settings.EMAIL_PASSWORD)
                server.send_message(message)
            return True
        except Exception as e:
            print(f"There was an error: {str(e)} " f"sending an email: {message.as_string()}.")
            return False

    def _add_subject(self, message: EmailMessage, subject: str):
        message["Subject"] = f"[EvenTITO] {subject}"
        return message

    def _add_body(self, message: EmailMessage, body, extra_params):
        if message.get_content_type() != "text/html":
            message.set_type("text/html")

        end_text = "<br><br>Este mensaje fue enviado desde " f"<a href='{settings.FRONTEND_URL}'>EvenTITO</a>"
        body = f"{body}\n\n{end_text}"

        message.set_payload(body)
        return message

    def _add_body_extra(self, message: EmailMessage, body):
        body_filled = BODY_TEMPLATE.replace("{{ body }}", body)
        message.set_content("This is a HTML email. If you see this text, your client does not support HTML.")
        message.add_alternative(body_filled, subtype="html")

    def _replace_params(self, params, body):
        for i in range(0, len(params)):
            body = body.replace(f"[${i+1}]", params[i])
        return body
