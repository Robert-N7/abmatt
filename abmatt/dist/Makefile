VERSION=0.6.0

windows: version build_windows clean_windows dist add_windows_files zip
	echo ...done

linux: version build_linux clean_linux dist add_linux_files tar
	echo ...done

# updates the version
version:
	./update_version.py


build_linux:
	DIR=abmatt-ubu_x64-${VERSION}
	./build.sh && ./__main__ -b ..\test.brres -d test.brres -o

build_windows:
	@echo off
	$(eval DIR=abmatt-win10_x64-$(VERSION))
	build.bat && __main__ -b ..\test.brres -d test.brres -o

# create distribution folder
dist:
	echo Creating distribution in "${DIR}"... && \
 	mkdir "${DIR}" && \
  	cd "${DIR}" && mkdir bin && mkdir etc && cd etc && mkdir abmatt && cd "../.."
	cp ../../LICENSE "${DIR}" && \
	cp ../../README.md "${DIR}" && \
	cp ../presets.txt "${DIR}"/etc/abmatt && cp ../config.conf "${DIR}"/etc/abmatt && \
	cp __main__ "${DIR}"/bin/abmatt

tar:
	tar -czvf ($DIR).tar.gz "${DIR}"

zip:
	7z a -tzip "${DIR}".zip "${DIR}"

add_linux_files:
	cp install.sh "${DIR}" && cp uninstall.sh "${DIR}" &&\
	cp install-ubu.txt "${DIR}"/install.txt

add_windows_files:
	cp install-win.txt ${DIR}\install.txt && cp make_installer.nsi "${DIR}" &&\
	cd "${DIR}" && makensis make_installer.nsi && del make_installer.nsi && cd ..


linux_install:
	cd "${DIR}" && sudo ./install.sh && cd ..

windows_install:
	cd "${DIR}" && install.exe && cd ..

clean_windows:
	if exist ${DIR} rmdir /S /Q "${DIR}"
	if exist ${DIR}.zip del ${DIR}.zip

clean_linux:
	rm -rf "${DIR}" "${DIR}".tar.gz
