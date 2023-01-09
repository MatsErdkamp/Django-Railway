from .. import models
import spotipy
from django.db.models import Count
import collections
from . import spotify_post_functions
import spotipy
from .authorization_functions import get_token
import json
import time
import datetime




def export_social_display_session_data(session_id):


    session = models.SocialDisplaySession.objects.get(id=session_id)

    session_logs = session.socialdisplayuserlog_set.all().order_by('timestamp').values()

    user_ids_in_logs = set([x['user_id'] for x in session_logs])
    print(user_ids_in_logs)
    

    master_list = []

    previous_timestamp = 0


    for log in session_logs:

        log['timestamp'] = time.mktime(log['timestamp'].timetuple())

        if log['timestamp'] == previous_timestamp:
            print('same timestamp!!')
            master_list.append(log)
        else:
            master_list.append(log)

        previous_timestamp = log['timestamp']
    

    with open('data.json', 'w') as f:
        json.dump(master_list, f)
