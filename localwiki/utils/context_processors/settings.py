from django.conf import settings


def license_agreements(context):
    return {
        'EDIT_LICENSE_NOTE': settings.EDIT_LICENSE_NOTE,
        'SIGNUP_TOS': settings.SIGNUP_TOS,
    }


def hostnames(context):
    return {
        'MAIN_HOSTNAME': settings.MAIN_HOSTNAME,
    }
