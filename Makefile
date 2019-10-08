.PHONY: check
check:
	mypy gotypist_stats
	pyflakes gotypist_stats
	black --check gotypist_stats
	[ '$(shell grep -oP 'version="[\d\.]+"' setup.py)' = '$(shell grep -oP 'version="[\d\.]+"' gotypist_stats/__main__.py)' ]

publish:
	rm -rf dist
	python3 setup.py sdist
	twine upload --repository-url https://upload.pypi.org/legacy/ dist/gotypist-stats-*.tar.gz
