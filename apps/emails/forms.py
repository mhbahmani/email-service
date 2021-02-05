import string

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from apps.emails.models import Email, EmailRecipient

import re


class EmailRecipientsForm(forms.ModelForm):
    '''
        Customized admin form for Email model.
    '''

    EMAILS_FILE_SPLIT_PATTERN = '||'

    NONE_OF_THESE = 'none_of_these'
    ALL = 'all_users'
    OPTIONS_CHOICES = [
        (NONE_OF_THESE, 'None Of These'),
        (ALL, 'All Of The Users'),
    ]
    recipients_file = forms.FileField(allow_empty_file=True, required=False)
    recipients_options = forms.ChoiceField(choices=OPTIONS_CHOICES, widget=forms.RadioSelect,
                                           required=False,
                                           label='Send Email to')

    class Meta:
        model = Email
        fields = '__all__'

    def save(self, commit=True):
        instance = super(EmailRecipientsForm, self).save(commit)
        context = dict()
        email_values = re.split(Email.TEMPLATE_FIELDS_SPLITTER, instance.values_of_fields)
        template_fields = instance.template.emailtemplatefield_set.all().values_list('field_name', flat=True)
        for (field, value) in zip(template_fields, email_values):
            context[field] = value
            instance.template.emailtemplatefield_set.filter(field_name=field).update(field_value=value)
        if not instance.subject:
            instance.subject = context.get('subject')
        instance.html_context = instance.template.html
        instance.text_context = instance.template.text
        return super().save(commit)

    def _save_m2m(self):
        option = self.cleaned_data['recipients_options']
        if option and option != self.NONE_OF_THESE:
            if option == self.ALL:
                self.set_all_users_as_recipient(self.instance)
        file = self.cleaned_data['recipients_file']
        if file:
            file = file.read().decode()
            email_addresses = re.sub('\s+', '||', file.strip()).split(self.EMAILS_FILE_SPLIT_PATTERN)
            self.set_email_recipients(self.instance, email_addresses)
        super(EmailRecipientsForm, self)._save_m2m()

    def set_email_recipients(self, email: Email, email_addresses: list):
        from django.core.validators import validate_email
        for email_address in email_addresses:
            try:
                validate_email(email_address)
            except ValidationError:
                    continue
            '''
                EmailRecipient User relation
            '''
            user, _ = User.objects.get_or_create(email=email_address)
            recipient, _ = EmailRecipient.objects.get_or_create(email_address=email_address, user=user)
            email.recipients.add(recipient)
        
    def set_all_users_as_recipient(self, email: Email) -> None:
        '''
            EmailRecipient User relation
        '''
        all_users = User.objects.all()
        for user in all_users:
            recipient, created = EmailRecipient.objects.get_or_create(user=user, email_address=user.email)
            email.recipients.add(recipient)
