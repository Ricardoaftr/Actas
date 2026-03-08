@echo off
title MODO PRUEBA - SISTEMA MODULAR
cd /d "%~dp0"
py -m streamlit run main.py --server.port 8502
pause