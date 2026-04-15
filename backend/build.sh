#!/bin/bash
# Render Build Script
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium
