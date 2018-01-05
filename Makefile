looptest:
	find . -name '*.pyc' -delete
	py.test --looponfail
