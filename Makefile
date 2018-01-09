looptest:
	find . -name '*.pyc' -delete
	py.test --looponfail

test:
	find . -name '*.pyc' -delete
	./manage.py test --settings=project.settings.local
