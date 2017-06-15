#!/bin/bash

service mongod start
echo "Base de datos preparada"
source flask/bin/activate
echo "Entorno virtual preparado"
echo "Ejecutando aplicación"
./run.py
