@echo off
if not exist src\data mkdir src\data
cd src
pip install -r requirements.txt
python main.py