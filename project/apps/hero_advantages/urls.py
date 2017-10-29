from django.conf.urls import url

from . import views

urlpatterns = [
    # eg: /data/
    url(r'^$', views.index, name='index'),
    # eg: /data/heroes/
    url(r'^heroes/$', views.hero_list, name='hero_list'),
    # eg: /data/3/hero_name/
    url(r'^(?P<hero_id>[0-9]+)/hero_name/$', views.hero_name, name='hero_name'),
    # eg: /data/Axe/advantages/
    url(r'^advantages/(?P<enemy_name>[a-zA-Z-\' ]+)/$', views.single_advantage, name='single_advantage'),
]
