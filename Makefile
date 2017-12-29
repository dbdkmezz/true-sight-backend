# DOES NOT WORK
# looptest:
# 	find . -name '*.pyc' -delete
# 	DJANGO_SETTINGS_MODULE='project.settings.test' py.test --looponfail

test:
	find . -name '*.pyc' -delete
	DJANGO_SETTINGS_MODULE='project.settings.test' ./manage.py test 
