os := $(if $(filter $(OS),Windows_NT),win10,ubu)
cat := $(if $(filter $(os),win10),type,cat)
dir := $(shell $(cat) dist_dir)

windows: dist add_windows_files zip
	echo ...done

linux: dist add_linux_files tar
	echo ...done

# updates the version
update_version:
	./update_version.py
	version := $(shell $(cat) version)
	bit_width := $(shell $(cat) bit_width)

build:
	./build.py && ./__main__ -b ../test.brres -d test.brres -o

# create distribution folder
dist:
	echo Creating distribution in "${dir}"... && \
 	mkdir "${dir}" && \
  	cd "${dir}" && mkdir bin && mkdir etc && cd etc && mkdir abmatt && cd "../.."
	cp ../../LICENSE "${dir}" && \
	cp ../../README.md "${dir}" && \
	cp ../presets.txt "${dir}"/etc/abmatt && cp ../config.conf "${dir}"/etc/abmatt && \
	cp main ${dir}/bin/abmatt

tar:
	tar -czvf "${dir}".tar.gz "${dir}"

zip:
	7z a -tzip ${dir}.zip "${dir}"

add_linux_files:
	cp install.sh "${dir}" && cp uninstall.sh "${dir}" &&\
	cp install-ubu.txt "${dir}"/install.txt

add_windows_files:
	cp install-win.txt ${dir}\install.txt && cp make_installer.nsi "${dir}" &&\
	cd "${dir}" && makensis make_installer.nsi && del make_installer.nsi && \
	rmdir /S /Q etc && rmdir /S /Q bin && del README.md && del LICENSE && \
	cd ..


linux_install:
	cd "${dir}" && sudo ./install.sh && cd ..

windows_install:
	cd "${dir}" && install.exe && cd ..

clean_windows:
	if exist ${dir} rmdir /S /Q "${dir}"
	if exist ${dir}.zip del ${dir}.zip

clean_linux:
	rm -rf "${dir}" "${dir}".tar.gz
