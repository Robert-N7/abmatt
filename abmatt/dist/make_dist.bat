@echo off
:: update version and build
.\update_version.py
set /p version=<version.txt
set package=abmatt-win10_x64-%version%
:: clean
rmdir /S /Q %package%
del %package%.zip
echo building...
start /min /wait cmd.exe /C build.bat &&\
__main__.exe -b ..\test.brres -c info &&\
echo creating package %package% &&\
:: make directories
mkdir %package% &&\
cd %package% &&\
mkdir bin &&\
mkdir etc &&\
cd etc &&\
mkdir abmatt &&\
cd ..\.. &&\
:: copy files
cp __main__.exe %package%\bin\abmatt.exe &&\
cp ..\presets.txt %package%\etc\abmatt &&\
cp ..\config.conf %package%\etc\abmatt &&\
cp ..\..\LICENSE %package% &&\
cp ..\..\README.md %package% &&\
cp install-win.txt %package%\install.txt &&\
cp make_installer.nsi %package% &&\
:: make installer
echo making installer &&\
cd %package% &&\
makensis make_installer.nsi &&\
del make_installer.nsi &&\
:: install
install.bat &&\
cd .. &&\
:: zip
7z a -tzip %package%.zip %package%
echo ...done
