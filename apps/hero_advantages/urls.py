from django.conf.urls import url

from . import views

urlpatterns = [
    # eg: /hero_advantages/
    url(r'^$', views.index, name='index'),
    # eg: /hero_advantages/heroes/
    url(r'^heroes/$', views.hero_list, name='hero_list'),
    # eg: /hero_advantages/3/hero_name/
    url(r'^(?P<hero_id>[0-9]+)/hero_name/$', views.hero_name, name='hero_name'),
    # eg: /hero_advantages/advantages/Axe/Pudge/
    url(r'^advantages/(?P<enemy_names>[a-zA-Z-/\' ]*)/$', views.advantages, name='advantages'),
]
