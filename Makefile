looptest:
	find . -name '*.pyc' -delete
	pytest --ds=project.settings.test --looponfail

test:
	find . -name '*.pyc' -delete
	./manage.py test --settings=project.settings.local
