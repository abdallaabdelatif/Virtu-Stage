## Setup
python -m venv venv  #create a virtual environment to avoid conflicting with global system python packages
venv\Scripts\activate # activate it
pip install -r requirements.txt # install dependecies
uvicorn app.main:app --reload # run the server