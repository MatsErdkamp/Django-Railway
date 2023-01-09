from platform import release
from django.utils.timezone import make_aware
import datetime
import string
import re



def create_song_identifier(name, include_brackets=True):
    # delete punctuation marks and make lowercase

    brackets = re.findall(r'\(([^()]+)\)', name)

    song_name = re.sub("([\(\[]).*?([\)\]])", "", name).strip()

    song_name = song_name.translate(
        str.maketrans('', '', string.punctuation))
    # remove spaces

    song_name = song_name.replace(" ", "").replace("'", "").replace(
        '"', '').replace("’", "").replace("‘", '').casefold()


    if include_brackets == True and len(brackets) > 0:

        brackets = brackets[0].translate(str.maketrans('', '', string.punctuation)).replace(" ", "").replace("'", "").replace(
            '"', '').replace("’", "").replace("‘", '').casefold()

        song_name = song_name + '#' + str(brackets)

    return song_name



def create_album_identifier(name, release_date, include_brackets=True):
    # delete punctuation marks and make lowercase

    brackets = re.findall(r'\(([^()]+)\)', name)

    album_name = re.sub("([\(\[]).*?([\)\]])", "", name).strip()

    album_name = album_name.translate(
        str.maketrans('', '', string.punctuation))
    # remove spaces

    album_name = album_name.replace(" ", "").replace("'", "").replace(
        '"', '').replace("’", "").replace("‘", '').casefold()

    # add the release_date
    album_name = album_name + '@' + str(release_date)[:4]

    if include_brackets == True and len(brackets) > 0:

        brackets = brackets[0].translate(str.maketrans('', '', string.punctuation)).replace(" ", "").replace("'", "").replace(
            '"', '').replace("’", "").replace("‘", '').casefold()

        album_name = album_name + '#' + str(brackets)

    return album_name


def set_timeframe(queryset, timeframe):
    
    
    if timeframe == 'weekly':
        time_filter = make_aware(datetime.datetime.now() -
                                 datetime.timedelta(days=7))
        queryset = queryset.filter(played_at__gte=time_filter)
    elif timeframe == 'monthly':
        time_filter = make_aware(datetime.datetime.now() -
                                 datetime.timedelta(days=30))
        queryset = queryset.filter(played_at__gte=time_filter)
    elif timeframe == 'quarterly':
        time_filter = make_aware(datetime.datetime.now() -
                                 datetime.timedelta(days=92))
        queryset = queryset.filter(played_at__gte=time_filter)
    elif timeframe == 'yearly':
        time_filter = make_aware(datetime.datetime.now() -
                                 datetime.timedelta(days=365))
        queryset = queryset.filter(played_at__gte=time_filter)


    return queryset
