TITLE Setting up virtual env
:: Running it once is fine, this just sets up virtual env >> install all modules there 
py -m venv env && env\scripts\activate.bat && pip install -r requirements.txt

:: Note to rerun the requirements.txt in case you ever add a mdoule.
:: Running this multiple time will not make a mess of your setup, dont worry about that bit.
