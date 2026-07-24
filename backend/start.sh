#!/bin/bash
pip install -r requirements.txt
pip install pyjwt bcrypt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
