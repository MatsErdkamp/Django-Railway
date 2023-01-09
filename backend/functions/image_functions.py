# code to refresh to the image currently by spotify
import os
import io
import random
import colorsys
from PIL import Image
import base64
import math
from django.db.models.query import QuerySet
from .. import models
import spotipy
import spotipy.util as util
from spotipy import oauth2
from django.contrib.auth.models import User
from .color_functions import generate_colors, get_colors
from . import spotify_get_functions

SPOTIPY_CLIENT_ID = '5d7b7b63771f45efb4c618aa0046adb7'
SPOTIPY_CLIENT_SECRET = '0cb723fd54fb43bd86bde40acaa65916'
SPOTIPY_REDIRECT_URI = 'http://localhost:8000'

sp_oauth = oauth2.SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI)


def refresh_artist_images(queryset=None):

    if queryset == None:
        queryset = models.Artist.objects.all()

    responseList = []

    print("ARTISTS:" + str(len(queryset)))

    for i in range(math.ceil(len(queryset)/50)):

        user = User.objects.get(username="MatsErdkamp")
        # print(user)

        social = user.social_auth.get(provider='spotify')
        token_info = sp_oauth.refresh_access_token(
            social.extra_data['refresh_token'])
        token = token_info['access_token']

        first = i*50
        last = first+50

        artistListSlice = queryset[first:last]
        artistListSliceURI = [i.uri for i in artistListSlice]

        # print(artistListSliceURI)

        x = spotipy.Spotify(auth=token).artists(artistListSliceURI)
        # print(x)

        responseList += x['artists']

    print(len(responseList))

    for i in responseList:
        # print(i['uri'])

        try:
            artist = models.Artist.objects.get(uri=i['uri'])
        except:
            print("COULDN'T GET ARTIST OBJECT FOR:" + i['uri'])
            continue

        try:
            gotdata = i['images'][0]['url']
        except:
            gotdata = '#'

        # print(gotdata)

        if (artist.image.px640 != gotdata):

            if (gotdata != '#'):
                print("New image for: " + str(artist.name))
                models.Image.objects.filter(pk=artist.image.id).update(
                    px640=i['images'][0]['url'])
                models.Image.objects.filter(pk=artist.image.id).update(
                    px300=i['images'][1]['url'])
                models.Image.objects.filter(pk=artist.image.id).update(
                    px64=i['images'][-1]['url'])

                # generate a new color for the new image
                col = get_colors(i['images'][-1]['url'])
                color = ','.join(str(x) for x in col)

                models.Image.objects.filter(pk=artist.image.id).update(
                    primary_color=color)


def refresh_album_images(queryset=None, save_to_db=True):

    if queryset == None:
        queryset = models.Album.objects.all()[:500]

    responseList = []

    print("ALBUMS:" + str(len(queryset)))

    for i in range(math.ceil(len(queryset)/20)):

        user = User.objects.get(username="MatsErdkamp")
        # print(user)

        social = user.social_auth.get(provider='spotify')
        token_info = sp_oauth.refresh_access_token(
            social.extra_data['refresh_token'])
        token = token_info['access_token']

        first = i*20
        last = first+20

        albumListSlice = queryset[first:last]
        albumListSliceURI = [i.uri for i in albumListSlice]

        # print(artistListSliceURI)

        x = spotipy.Spotify(auth=token).albums(albumListSliceURI)
        # print(x)

        responseList += x['albums']

    print(len(responseList))

    for i in responseList:
        print(i['uri'])

        try:
            album = models.Album.objects.get(uri=i['uri'])
        except:
            print("COULDN'T GET ALBUM OBJECT FOR:" + i['uri'])
            continue

        try:
            gotdata = i['images'][0]['url']
        except:
            gotdata = '#'

        # print(gotdata)

        if (album.image.px640 != gotdata):

            if (gotdata != '#'):
                print("New image for: " + str(album.name) + " } " +
                      str(gotdata) + " - saving=" + str(save_to_db))

                if (save_to_db == True):

                    models.Image.objects.filter(pk=album.image.id).update(
                        px640=i['images'][0]['url'])
                    models.Image.objects.filter(pk=album.image.id).update(
                        px300=i['images'][1]['url'])
                    models.Image.objects.filter(pk=album.image.id).update(
                        px64=i['images'][-1]['url'])

                    # generate a new color for the new image
                    col = get_colors(i['images'][-1]['url'])
                    color = ','.join(str(x) for x in col)

                    models.Image.objects.filter(pk=album.image.id).update(
                        primary_color=color)


def refresh_profile_images(queryset=None, save_to_db=True):

    if queryset == None:
        queryset = models.Profile.objects.all()[:20]

    responseList = []

    print("profiles:" + str(len(queryset)))

    for profile in queryset:

        try:
            create_or_refresh_profile_image_object(profile.user)
        except:
            print('image generation did not work! probably no PF on Spotify')


def get_recommendation_playlist_image():


    filename = '../media/playlist_logos/LOGO_PLAYLIST_RECOMMENDED.jpg'

    img = Image.open(filename, "r").convert('RGB')

    img_bytes = io.BytesIO()
    img.save(img_bytes, format="Jpeg")
    imgEncoded = base64.b64encode(img_bytes.getvalue())

    return imgEncoded


def get_hue_shifted_image(index):

    filename_hue_suffix = index

    filename = '../media/playlist_logos/LOGO_PLAYLIST_' + str(filename_hue_suffix) + '.png'

    img = Image.open(filename, "r").convert('RGB')

    img_bytes = io.BytesIO()
    img.save(img_bytes, format="Jpeg")
    imgEncoded = base64.b64encode(img_bytes.getvalue())

    return imgEncoded


def create_or_refresh_profile_image_object(user):

    spotify_profile = spotify_get_functions.get_spotify_profile(user)

    img_url = spotify_profile['images'][0]['url']



    if user.profile.image != None:


        if user.profile.image.px640 != img_url:
            primary_color = get_colors(img_url)
            color = ','.join(str(x) for x in primary_color)

            image = user.profile.image
            image.px640 = img_url
            image.px300 = img_url
            image.px64 = img_url
            image.primary_color = color
            image.save()
    else:
        primary_color = get_colors(img_url)
        color = ','.join(str(x) for x in primary_color)
        image = models.Image.objects.create_image(img_url, img_url, img_url, color)
        user.profile.image = image
        user.profile.save()


