VERSION=0.6.0
DIR=abmatt-ubu_x64-${VERSION}

all: update build dist install

# updates the version
update:
	./update_version.py

# creates __main__ binary and tests
build:
	./build.sh && ./__main__ -c info -b ../test.brres

# distribution, bundle everything in tar
dist:
	rm -rf "${DIR}"
	echo Creating distribution in "${DIR}"... && \
 	mkdir "${DIR}" && \
  	cd "${DIR}" && mkdir bin && mkdir etc && cd etc && mkdir abmatt && cd "../.."
	cp install.sh "${DIR}" && cp uninstall.sh "${DIR}" &&\
	cp ../../LICENSE "${DIR}" && cp install-ubu.txt "${DIR}"/install.txt &&\
	cp ../../README.md "${DIR}"
	cp ../presets.txt "${DIR}"/etc/abmatt && cp ../config.conf "${DIR}"/etc/abmatt &&\
	cp __main__ "${DIR}"/bin/abmatt &&\
	tar -czvf "${DIR}".tar.gz "${DIR}"
	echo ...done

install:
	cd "${DIR}" && sudo ./install.sh && cd ..