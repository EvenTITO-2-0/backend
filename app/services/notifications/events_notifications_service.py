from __future__ import annotations

import re
from email.message import EmailMessage

from fastapi import BackgroundTasks

from app.database.models.work import WorkStates
from app.repository.events_repository import EventsRepository
from app.repository.organizers_repository import OrganizerRepository
from app.repository.users_repository import UsersRepository
from app.schemas.members.reviewer_schema import ReviewerCreateRequestSchema
from app.services.notifications.notifications_service import NotificationsService, load_html

email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
CREATE_EVENT_NOTIFICATION_HTML = load_html("created-event-notification.html")
START_ORGS_EVENT_NOTIFICATION_HTML = load_html("started-orgs-event-notification.html")
WAITING_APPROVAL_USER_EVENT_NOTIFICATION_HTML = load_html("waiting-user-event-notification.html")
WAITING_APPROVAL_ADMIN_EVENT_NOTIFICATION_HTML = load_html("waiting-admin-event-notification.html")
INSCRIPTION_EVENT_NOTIFICATION_HTML = load_html("inscription-event-notification.html")
INSCRIPTION_USER_EVENT_NOTIFICATION_HTML = load_html("inscription-user-event-notification.html")
REVIEWER_EVENT_NOTIFICATION_HTML = load_html("reviewer-event-notification.html")
CHANGE_WORK_STATUS_NOTIFICATION_HTML = load_html("change-work-status-notification.html")


class EventsNotificationsService(NotificationsService):
    def __init__(
        self,
        event_repository: EventsRepository,
        users_repository: UsersRepository,
        organizer_repository: OrganizerRepository,
        background_tasks: BackgroundTasks,
    ):
        self.event_repository = event_repository
        self.users_repository = users_repository
        self.organizer_repository = organizer_repository
        self.recipients_emails: list[str] = []
        self.background_tasks = background_tasks

    def __recipients_message(self):
        message = EmailMessage()
        if len(self.recipients_emails) > 0:
            message["Bcc"] = ",".join(self.recipients_emails)
        else:
            message["Bcc"] = ""

        self.__print_email_to_send(self.recipients_emails, message)

        return message

    def __is_valid_email(self, email):
        return re.match(email_regex, email) is not None

    def __common_body(self, body, event):
        start_date = "Sin definir"
        start_time = "Sin definir"
        organized_by = "Sin definir"
        contact = "Sin definir"

        if event.dates[0]["date"] is not None:
            start_date = event.dates[0]["date"]
        if event.dates[0]["time"] is not None:
            start_time = event.dates[0]["time"]
        if event.organized_by is not None:
            organized_by = event.organized_by
        if event.contact is not None or len(event.contact) > 0:
            contact = event.contact

        body = body.replace("[title]", event.title)
        body = body.replace("[START_DATE]", start_date)
        body = body.replace("[START_TIME]", start_time)
        body = body.replace("[organized_by]", organized_by)
        body = body.replace("[contact]", contact)

        return body

    def __confirm_reject_body(self, body):
        body = body.replace("[url_confirm]", "https://eventito-frontend.vercel.app/")
        body = body.replace("[url_rejected]", "https://eventito-frontend.vercel.app/")

        return body

    async def __search_emails_admin(self):
        emails_to_send = []
        users_admin = await self.users_repository.get_admin_users()
        for user_admin in users_admin:
            emails_to_send.append(user_admin.email)
        return emails_to_send

    # Search organizer and extra notification emails
    async def __search_emails_organizers(self, event):
        emails_to_send = []
        users_organizers = await self.organizer_repository.get_all(event.id)
        for user, _ in users_organizers:
            if user.email is not None:
                emails_to_send.append(user.email)

        if event.notification_mails is not None:
            emails_to_send = list(set(emails_to_send + event.notification_mails))
        return emails_to_send

    # Search creator email
    async def __search_emails_creator(self, event):
        creator_id = event.creator_id
        creator_user = await self.users_repository.get(creator_id)
        return [creator_user.email]

    def __print_email_to_send(self, emails, message):
        print(f"Sending emails to {emails} | email message: {message}")

    def __config_common_and_send_specific_email(self, event, emails_to_send, body_common, subject, params=None):
        self.recipients_emails = emails_to_send

        message = self.__recipients_message()

        body = self.__common_body(body_common, event)
        # Using replace parameters with [$x]
        if params is not None:
            body = self._replace_params(params, body)

        self._add_subject(message, subject)
        self._add_body(message, body, params)
        self._add_body_extra(message, body)

        return self._send_email(message)

    def __notify_event_waiting_approval(self, event, subject, emails_to_send, params):
        self.__config_common_and_send_specific_email(
            event, emails_to_send, WAITING_APPROVAL_USER_EVENT_NOTIFICATION_HTML, subject, params
        )

    def __notify_event_waiting_approval_admin(self, event, subject, emails_to_send, params):
        self.__config_common_and_send_specific_email(
            event, emails_to_send, WAITING_APPROVAL_ADMIN_EVENT_NOTIFICATION_HTML, subject, params
        )

    def __notify_event_created(self, event, subject, emails_to_send):
        self.__config_common_and_send_specific_email(event, emails_to_send, CREATE_EVENT_NOTIFICATION_HTML, subject)

    def __notify_event_started_user(self, event, subject, emails_to_send):
        self.__config_common_and_send_specific_email(event, emails_to_send, START_ORGS_EVENT_NOTIFICATION_HTML, subject)

    def __notify_inscription_user(self, event, subject, emails_to_send, params):
        self.__config_common_and_send_specific_email(
            event, emails_to_send, INSCRIPTION_USER_EVENT_NOTIFICATION_HTML, subject, params
        )

    def __notify_inscription_gral(self, event, subject, emails_to_send, params):
        self.__config_common_and_send_specific_email(
            event, emails_to_send, INSCRIPTION_EVENT_NOTIFICATION_HTML, subject, params
        )

    def __notify_new_reviewers(self, event, subject, emails_to_send, params):
        self.__config_common_and_send_specific_email(
            event, emails_to_send, REVIEWER_EVENT_NOTIFICATION_HTML, subject, params
        )

    def __notify_change_work_status(self, event, subject, emails_to_send, params):
        self.__config_common_and_send_specific_email(
            event, emails_to_send, CHANGE_WORK_STATUS_NOTIFICATION_HTML, subject, params
        )

    async def notify_event_waiting_approval(self, event):
        org_emails_to_send = await self.__search_emails_organizers(event)
        creator_id = event.creator_id
        user_creator = await self.users_repository.get(creator_id)
        user_creator_fullname = f"{user_creator.name} {user_creator.lastname}"
        params_org = [user_creator_fullname]
        subject = f"El evento {event.title} ha sido enviado para su aprobación"

        self.background_tasks.add_task(
            self.__notify_event_waiting_approval, event, subject, org_emails_to_send, params_org
        )

        params_creator = [user_creator_fullname, creator_id]
        admin_emails_to_send = await self.__search_emails_admin()
        subject = f"El evento {event.title} espera aprobación"
        self.background_tasks.add_task(
            self.__notify_event_waiting_approval_admin, event, subject, admin_emails_to_send, params_creator
        )

        return True

    async def notify_event_created(self, event):
        org_emails_to_send = await self.__search_emails_organizers(event)

        subject = "Su solicitud de creación de evento fue aprobada"
        self.background_tasks.add_task(self.__notify_event_created, event, subject, org_emails_to_send)

        return True

    async def notify_event_started(self, event):
        org_emails_to_send = await self.__search_emails_organizers(event)

        subject = f"El evento {event.title} ha sido publicado"

        self.background_tasks.add_task(self.__notify_event_started_user, event, subject, org_emails_to_send)

        return True

    async def notify_inscription(self, event_id, user_inscripted_id):
        event = await self.event_repository.get(event_id)
        user_inscripted = await self.users_repository.get(user_inscripted_id)
        user_fullname = user_inscripted.name + " " + user_inscripted.lastname

        org_emails_to_send = await self.__search_emails_organizers(event)
        params = [user_fullname, user_inscripted.id]
        subject = f"El usuario {user_fullname} se ha inscripto al evento {event.title}"
        self.background_tasks.add_task(self.__notify_inscription_gral, event, subject, org_emails_to_send, params)

        user_inscripted_emails = [user_inscripted.email]
        params = [user_fullname]
        subject = "Su inscripción fue registrada con exito"
        self.background_tasks.add_task(self.__notify_inscription_user, event, subject, user_inscripted_emails, params)

        return True

    async def notify_new_reviewers(self, event_id, reviewers: ReviewerCreateRequestSchema):
        event = await self.event_repository.get(event_id)

        for reviewer in reviewers.reviewers:
            if reviewer.email is not None:
                emails_to_send = [reviewer.email]
                user_reviewer = await self.users_repository.get_user_by_email(reviewer.email)

                fullname = f"{user_reviewer.name} {user_reviewer.lastname}"
                params = [fullname, str(reviewer.work_id), str(reviewer.review_deadline)]

                subject = f"{fullname} fue asignado como reviewer"

                self.background_tasks.add_task(self.__notify_new_reviewers, event, subject, emails_to_send, params)

        return True

    async def notify_change_work_status(self, event_id, obj_work):
        event = await self.event_repository.get(event_id)
        emails_to_send = []

        for author in obj_work["work"].authors:
            notify_update = author["notify_updates"]
            if notify_update:
                author_email = author["mail"]
                emails_to_send.append(author_email)

        if obj_work["status"] == WorkStates.APPROVED:
            status_msg = "APROBADO"
        else:
            status_msg = "RECHAZADO"
        subject = "Su trabajo a cambiado de estado"
        params = [str(obj_work["work"].title), status_msg]

        self.background_tasks.add_task(self.__notify_change_work_status, event, subject, emails_to_send, params)

        return True
