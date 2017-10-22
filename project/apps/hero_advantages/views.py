from django.http import HttpResponse, JsonResponse

from .models import Hero, Advantage

def index(request):
    return HttpResponse("Hellooo")

def hero_list(request):
    hero_list = Hero.objects.all()
    return JsonResponse({'Heroes': [h.name for h in hero_list]})

def hero_name(request, hero_id):
    return JsonResponse({'Name': format(Hero.objects.get(pk=hero_id))})

def single_advantage(request, enemy_name):
    return JsonResponse({'data': Advantage.generate_info_dict([enemy_name])})

def multiple_advantages(request, enemy_names):
    pass

# api.add_resource(hero_name, '/hero/<string:hero_id>')
# api.add_resource(FiveAdvantages, '/advantages/<string:name1>/<string:name2>/<string:name3>/<string:name4>/<string:name5>')
# api.add_resource(SingleAdvantage, '/advantages/<string:enemyName>')
