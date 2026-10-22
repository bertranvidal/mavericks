#!/bin/bash
cd /Users/josemiguel/mavericks/supplier-radar

echo "=== Entrenando modelo de texto ==="
python3 train_text.py --epochs 3 --bs 8

echo "=== Entrenando modelo de vinculacion ==="
python3 train_link.py --epochs 2 --bs 8

echo "=== Calibrando umbrales ==="
python3 calibrate.py

echo "=== Comprobando contra Answer Key - Test ==="
python3 check_answers.py --mode models

echo "=== Comprobando contra Answer Key - Live Day ==="
python3 check_answers.py --mode models --live

echo "=== TERMINADO ==="
