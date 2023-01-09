from .. import models, decorators
import io
import colorgram
from django.contrib.auth.models import User
from urllib.request import urlopen
from django.db import connection


def generate_colors(objects=None):

    print('Initializing color generation!')

    if objects == None:
        objectsWithoutPrimaryColor = models.Image.objects.filter(
            primary_color=None)
    else:
        objectsWithoutPrimaryColor = [objects]



    for i in reversed(objectsWithoutPrimaryColor):
        if (i.px64 != '#'):
            col = get_colors(i.px64)
            color = ','.join(str(x) for x in col)
            models.Image.objects.filter(pk=i.id).update(primary_color=color)
            print(str(i) + ' now has color:' + str(col))



def get_colors(image):
    """Color generator"""

    fd = urlopen(image)
    f = io.BytesIO(fd.read())

    colors = colorgram.extract(f, 6)

    best_index = -1
    best_val = 99999999

    for index, i in enumerate(colors):

        L = i.hsl.l
        S = i.hsl.s

        if(L < 50):
            continue

        val = abs(L-125)**2 + abs(S-200)**2

        if val < best_val:
            best_val = val
            best_index = index

    if (best_index == -1):
        print("NO BEST INDEX DEFAULTING TO 0")
        best_index = 0

    return (colors[best_index].rgb.r, colors[best_index].rgb.g, colors[best_index].rgb.b)


def sRGBtoLin(colorChannel):

    if (colorChannel <= 0.04045):
        return colorChannel / 12.92
    else:
        return pow(((colorChannel + 0.055)/1.055), 2.4)


def delete_colors():
    print("Deleting all primary colors!")
    models.Image.objects.all().update(primary_color=None)
