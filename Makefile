PYTHONVERSION=`python3 -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))'`

.PHONY: tests tests-python2

version:
	@echo "$(PYTHONVERSION)"

doc:
	echo "" > DOC
	pydoc3 ./clap/* >> DOC

global-install:
	make tests
	make clean
	mkdir -p $(PREFIX)/lib/python$(PYTHONVERSION)/site-packages/clap
	cp -v ./clap/*.py $(PREFIX)/lib/python$(PYTHONVERSION)/site-packages/clap/

install: ./clap/*.py
	mkdir -p ~/.local/lib/python$(PYTHONVERSION)/site-packages/clap
	cp -v ./clap/*.py ~/.local/lib/python$(PYTHONVERSION)/site-packages/clap/

clean:
	rm -rf ./clap/__pycache__


test:
	python3 ./tests/clap/tests.py --catch --failfast --verbose 

test-builder:
	python3 ./tests/clap/buildertests.py --catch --failfast --verbose 

test-example-ui-run:
	python3 ./examples/nested.py > /dev/null
	python3 ./examples/nested.py help > /dev/null
	python3 ./examples/nested.py help help > /dev/null
	python3 ./examples/nested.py help help --help > /dev/null

test-example-ui-helper-output:
	@python3 ./examples/nested.py help
	@python3 ./examples/nested.py help help
	@python3 ./examples/nested.py help help --usage

test-cover: test test-builder test-example-ui-run
