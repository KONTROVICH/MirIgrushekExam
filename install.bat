@echo off
chcp 65001 >nul
echo ============================================
echo   Установка проекта "МирИгрушек"
echo ============================================

:: Проверяем Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не найден. Установите Python и добавьте в PATH.
    pause
    exit /b 1
)

:: Определяем команду python (желательно 3.12)
set PYTHON_CMD=python
py -3.12 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py -3.12
    echo Используется Python 3.12
) else (
    echo Используется Python по умолчанию
)

:: Создаём виртуальное окружение, если его нет
if not exist venv_exam\ (
    echo Создаю виртуальное окружение...
    %PYTHON_CMD% -m venv venv_exam
    if %errorlevel% neq 0 (
        echo [ОШИБКА] Не удалось создать виртуальное окружение.
        pause
        exit /b 1
    )
)

:: Активируем окружение
call venv_exam\Scripts\activate.bat

:: Устанавливаем зависимости
if exist wheelhouse\ (
    echo Папка wheelhouse найдена. Устанавливаю зависимости без интернета...
    pip install --no-index --find-links=wheelhouse -r app/requirements.txt
) else (
    echo Папка wheelhouse не найдена. Устанавливаю зависимости из интернета...
    pip install -r app/requirements.txt
)

:: Если wheelhouse не сработал, пробуем докачать из интернета
if %errorlevel% neq 0 (
    echo Wheelhouse не сработал, пробую интернет...
    pip install -r app/requirements.txt
)

:: Проверяем результат
if %errorlevel% neq 0 (
    echo [ОШИБКА] Не удалось установить зависимости. Проверьте подключение к интернету или целостность wheelhouse.
    pause
    exit /b 1
)

:: Применяем миграции
echo Применяю миграции...
python app/manage.py migrate
if %errorlevel% neq 0 (
    echo [ОШИБКА] Ошибка при миграциях.
    pause
    exit /b 1
)

echo ============================================
echo   Установка завершена успешно!
echo   Для запуска сервера:
echo   venv_exam\Scripts\activate
echo   python app/manage.py runserver
echo ============================================
pause