from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest

from .models import Hero, Advantage
from .exceptions import InvalidEnemyNames


def index(request):
    return HttpResponse("Hellooo")


def hero_list(request):
    hero_list = Hero.objects.all()
    return JsonResponse({'Heroes': [h.name for h in hero_list]})


def hero_name(request, hero_id):
    return JsonResponse({'Name': format(Hero.objects.get(pk=hero_id))})


def advantages(request, enemy_names):
    enemy_names = enemy_names.split('/')
    try:
        return JsonResponse({'data': Advantage.generate_info_dict(enemy_names)})
    except InvalidEnemyNames:
        return HttpResponseBadRequest()
