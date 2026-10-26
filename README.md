# Evolución de un campo escalar masivo en Schwarzschild

Trabajo universitario sobre Klein–Gordon en espacio plano y sobre una geometría
fija de Schwarzschild. Se han ejecutado siete evoluciones planas para comprobar
la dispersión y el refinamiento conjunto de espacio y tiempo. La evolución en
Schwarzschild y el cálculo de frecuencias complejas siguen pendientes.

- `report/`: memoria en español, plantilla institucional y bibliografía.
- `src/`: código de las simulaciones.
- `results/flat/`: datos, tablas, figuras y parámetros de las ejecuciones.

Desde la raíz del repositorio, en PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python src\run_flat_validation.py
.\report\compilar.ps1
```

La compilación requiere pdfLaTeX y Biber; el script detecta la instalación habitual
de MiKTeX. El principal es `report/main.tex` y el PDF generado es `report/main.pdf`.
En Git se conservan las figuras WebP. Al ejecutar la simulación también se generan
los PDF locales que utiliza LaTeX; por eso se ejecuta el programa antes de compilar.
