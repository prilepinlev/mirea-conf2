@echo off
chcp 65001 >nul

if "%1"=="" (
    echo Запуск всех этапов...
    python stage1.py
    python stage2.py
    python stage3.py
) else if "%1"=="1" (
    echo Запуск этапа 1...
    python stage1.py
) else if "%1"=="2" (
    echo Запуск этапа 2...
    python stage2.py %2 %3 %4 %5
) else if "%1"=="3" (
    echo Запуск этапа 3...
    python stage3.py %2 %3 %4 %5
) else if "%1"=="help" (
    echo Использование:
    echo   setup.bat       - все этапы
    echo   setup.bat 1     - только этап 1
    echo   setup.bat 2     - только этап 2
    echo   setup.bat 3     - только этап 3
) else (
    echo Неизвестная команда: %1
    echo Используйте: setup.bat help
)

pause