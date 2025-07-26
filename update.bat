@echo off
echo.
echo [1/5] Checking for virtual environment...
if not exist .\\venv (
    echo Virtual environment not found. Creating it now...
    python -m venv .venv
    echo Virtual environment created successfully.
) else (
    echo Virtual environment found.
)

echo.
echo [2/5] Updating dependencies from requirements.txt...
.\\.venv\\Scripts\\pip.exe install -r requirements.txt

echo.
echo [3/5] Cleaning up old build directories...
powershell -Command "Remove-Item -Recurse -Force ./build, ./dist -ErrorAction SilentlyContinue"
echo Cleanup complete.

echo.
echo [4/5] Building the new executable...
.\\.venv\\Scripts\\python.exe -m PyInstaller Cline-X-App.spec

echo.
echo [5/5] =======================================================
echo  Build complete! 
echo  The updated 'Cline-X-App.exe' is in the 'dist' folder.
echo =======================================================
echo.
pause
