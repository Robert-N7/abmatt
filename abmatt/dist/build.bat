cd ..
pyinstaller __main__.py --onefile --paths=venv/Lib/site-packages;venv\Lib\site-packages\numpy\.libs
cd dist