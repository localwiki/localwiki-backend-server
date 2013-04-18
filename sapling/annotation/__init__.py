import datetime
import jwt

from django.conf import settings

TTL = 60 * 60 * 24  # one day

def get_annotation_token(request):
    def _generate_user_id():
        if hasattr(request, 'user') and request.user.is_authenticated():
            user_id = request.user.username
        else:
            user_id = request.META.get('REMOTE_ADDR', None)

        return 'acct:%s@localwiki.org' % user_id

    issued_at = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
    return jwt.encode({
        'consumerKey': settings.HYPOTHESIS_CONSUMER_KEY,
        'userId': _generate_user_id(),
        'ttl': TTL,
        'issuedAt': issued_at,
    },
    settings.HYPOTHESIS_SECRET_KEY)
