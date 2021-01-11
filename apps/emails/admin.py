import string

from django.contrib import admin, messages
from django.db import models
from django.template import Context, Template
from django.utils.translation import ngettext
from martor.widgets import AdminMartorWidget

from apps.accounts.models import Profile
from apps.emails.forms import EmailRecipientsForm
from apps.emails.models import Email, EmailTemplate, EmailTemplateKeywords, EmailRecipient
from apps.emails.tasks import send_email


'''
    For some features, we need users university, 
    Instead of 'Profile', use a model with needed fields.
    In this project, Profile is a model with this filed and it also
    has a relation to User model.
'''


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    exclude = ('html_context', 'text_context', 'recipients')
    formfield_overrides = {
        models.TextField: {'widget': AdminMartorWidget},
    }
    actions = ['send_emails', 'clear_recipients']

    def clear_recipients(self, request, queryset):
        [email.recipients.clear() for email in queryset]

        self.message_user(request, ngettext(
            '%d email was successfully deleted.',
            '%d emails were successfully deleted.',
            len(queryset),
        ) % len(queryset), messages.SUCCESS)

    def send_emails(self, request, queryset):
        for email in queryset:
            email_keywords = email.template.emailtemplatekeywords_set.all()
            if email_keywords:
                self.send_email_with_keyword(email)
            else:
                self.send_email_without_keyword(email)

        self.message_user(request, ngettext(
            '%d email was successfully sent.',
            '%d emails were successfully sent.',
            len(queryset),
        ) % len(queryset), messages.SUCCESS)

    def send_email_without_keyword(self, email: Email) -> None:
        self.set_values_to_template_fields(email)
        recipients_email_list = self.get_recipients_emails(email.recipients)
        self.call_send_email_task(email, recipients_email_list)

    def send_email_with_keyword(self, email: Email) -> None:
        email_keywords = email.template.emailtemplatekeywords_set.values_list('keyword_type', flat=True)
        for recipient in email.recipients.all():
            for email_keyword in email_keywords:
                keyword_regex = self.get_keyword_regex(email_keyword)
                if email_keyword == EmailTemplateKeywords.USER_NAME:
                    self.handle_user_name_keyword(email, recipient, keyword_regex)
                elif email_keyword == EmailTemplateKeywords.USER_UNIVERSITY:
                    self.handle_user_university_keyword(email, recipient, keyword_regex)
                elif email_keyword == EmailTemplateKeywords.USER_FELLOW_STUDENT:
                    self.handle_user_fellow_students_keyword(email, recipient, keyword_regex)
            self.set_values_to_template_fields(email)
            self.call_send_email_task(email, [recipient.email_address])

    def set_values_to_template_fields(self, email: Email) -> None:
        template = email.template
        context = dict()
        for field in template.emailtemplatefield_set.all():
            context.update({field.field_name: field.field_value})
        email.html_context = self.render_email_templates(email.html_context, context)
        email.text_context = self.render_email_templates(email.text_context, context)

    def render_email_templates(self, template: string, context: dict):
        return Template(template).render(Context(context))

    def handle_user_fellow_students_keyword(self, email: Email, recipient: EmailRecipient, keyword_regex) -> None:
        '''
            For this features, we need users university.
            Instead of 'Profile', use a model with needed fields.
        '''
        university = Profile.objects.get(user__email=recipient.email_address).university
        fellow_students_string = ''
        try:
            fellow_students = Profile.objects.filter(university=university)
            for fellow_student in fellow_students:
                fellow_students_string = fellow_students_string.__add__(f'{fellow_student.__str__()}: {fellow_student.user.email}')
        except Profile.DoesNotExist:
            fellow_students_string = 'از دانشگاه شما کسی ثبت‌نام نکرده است'
        email.html_context = email.html_context.replace(keyword_regex, fellow_students_string, 1)

    def handle_user_university_keyword(self, email: Email, recipient: EmailRecipient, keyword_regex) -> None:
        try:
            university = Profile.objects.get(user__email=recipient.email_address).university
        except Profile.DoesNotExist:
            university = None
        email.html_context = email.html_context.replace(keyword_regex, university, 1)

    def handle_user_name_keyword(self, email: Email, recipient: EmailRecipient, keyword_regex) -> None:
        if recipient.user:
            email.html_context = email.html_context.replace(keyword_regex, recipient.user.get_full_name(), 1)

    def call_send_email_task(self, email: Email, to: list) -> None:
        send_email.apply_async(args=[email.html_context,
                                    email.text_context,
                                    email.subject,
                                    to])

    def get_recipients_emails(self, recipients) -> list:
        email_addresses = list()
        [email_addresses.append(recipient.email_address) for recipient in recipients.all()]
        return email_addresses

    def get_keyword_regex(self, email_keyword: string) -> string:
        for KEYWORD, VALUE in EmailTemplateKeywords.KEYWORDS:
            if email_keyword == KEYWORD:
                return '{{ ' + VALUE + ' }}'

    def save_form(self, request, form, change):
        return super().save_form(request, form, change)

    def get_form(self, request, obj=None, change=False, **kwargs):
        if request.user.is_superuser:
            kwargs['form'] = EmailRecipientsForm
        return super().get_form(request, obj, **kwargs)

    send_emails.short_description = 'Send selected emails'
    clear_recipients.short_description = 'Clear all email recipients'


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    pass
