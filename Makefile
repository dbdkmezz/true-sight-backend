clean = find . -name '*.pyc' -delete
run-tests = py.test --ds=project.settings.test


looptest:
	$(clean)
	$(run-tests) --looponfail

test:
	$(clean)
	$(run-tests)

coverage:
	$(clean)
	$(run-tests) --cov=apps --cov-report html

