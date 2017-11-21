# Release process

1. Check the version number and set the date in `CHANGELOG.md`
1. Check the version number in `setup.py`
1. Tag the release: ``git tag -a x.y.z; git push --tags``
1. Release on PyPI: ``python setup.py sdist upload``
1. Iterate the version number in `CHANGELOG.md` and `setup.py`.
