# AI for Urban Dengue Outbreak

A local bilingual dengue forecasting dashboard for Bangladesh. Select a city and ward, an observation week 2, 3 or 4-week window, then choose **Update forecast**. Each result estimates the case count for one target week. Historical dates let you explore seasonal variation. The default uses the last recorded week on 29 December 2025.

## Run on Windows

1. Install 64-bit Python 3.12 with the Python launcher. Extract the entire ZIP into a writable folder.
2. Double-click **RUN_WINDOWS.bat**. Keep the window open. First launch installs the Python packages and needs internet access. Installation time depends on the connection.
3. Open **http://127.0.0.1:8000/**. Use the top bar to switch language or theme. Press Ctrl+C in the terminal to stop the server.

or manually,

POWERSHELL:
winget install Python.Python.3.12
py -3.12 -m venv .venv
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000

## Run on macOS or Linux

From this folder with Python 3.12 available:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Open http://127.0.0.1:8000/. To verify the installation run `python manage.py test` inside the active environment.

## Project inputs

The bundled CSV supplies 31,320 weekly observations for 60 wards across five city areas. The model file is the uploaded multiweek scikit-learn bundle. The service computes model inputs locally and loads the saved thresholds. The validation panel reports a rounded results from the supplied training notebook. Historical predictions from the bundled final model including dates used for its final fit. See ARCHITECTURE.md for the distinction between the final fit and held-out evaluation.

## AI and API disclosure

OpenAI ChatGPT (Codex) assisted with the Django integration, dashboard, Bengali localization, documentation and tests. Inference uses local files. The dashboard makes zero external API or LLM calls. This disclosure describes this integration session.
