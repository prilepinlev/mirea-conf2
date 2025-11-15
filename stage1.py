#!/usr/bin/env python3
import json
import os
import sys
from typing import Dict, Any
from urllib.parse import urlparse

class ConfigError(Exception):
    """Базовое исключение для ошибок конфигурации"""
    pass

class PackageNameError(ConfigError):
    """Ошибка в имени пакета"""
    pass


class RepositoryURLError(ConfigError):
    """Ошибка в URL репозитория"""
    pass

class VersionError(ConfigError):
    """Ошибка в версии пакета"""
    pass

class FilterError(ConfigError):
    """Ошибка в фильтре пакетов"""
    pass

class TestModeError(ConfigError):
    """Ошибка в режиме тестового репозитория"""
    pass


class DependencyVisualizer:
    """Класс для визуализации графа зависимостей пакетов"""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config: Dict[str, Any] = {}

    def load_config(self) -> None:
        try:
            if not os.path.exists(self.config_file):
                raise ConfigError(f"Конфигурационный файл '{self.config_file}' не найден")

            with open(self.config_file, 'r', encoding='utf-8') as f:
                file_content = f.read().strip()
                if not file_content:
                    raise ConfigError("Конфигурационный файл пуст")

                self.config = json.loads(file_content)

        except json.JSONDecodeError as e:
            raise ConfigError(f"Ошибка парсинга JSON: {e}")
        except UnicodeDecodeError as e:
            raise ConfigError(f"Ошибка декодирования файла: {e}")
        except IOError as e:
            raise ConfigError(f"Ошибка чтения файла: {e}")

    def validate_config(self) -> None:
        self._validate_package_name()
        self._validate_repository_url()
        self._validate_test_repository_mode()
        self._validate_version()
        self._validate_filter_substring()

    def _validate_package_name(self) -> None:
        package_name = self.config.get("package_name", "")

        if not package_name:
            raise PackageNameError("Имя пакета не может быть пустым")

        if not isinstance(package_name, str):
            raise PackageNameError("Имя пакета должно быть строкой")

        if not all(c.isalnum() or c in ['-', '_', '.'] for c in package_name):
            raise PackageNameError("Имя пакета содержит недопустимые символы")

        if len(package_name) > 100:
            raise PackageNameError("Имя пакета слишком длинное (максимум 100 символов)")

    def _validate_repository_url(self) -> None:
        repository_url = self.config.get("repository_url", "")

        if not repository_url:
            raise RepositoryURLError("URL репозитория не может быть пустым")

        if not isinstance(repository_url, str):
            raise RepositoryURLError("URL репозитория должен быть строкой")

        if self.config.get("test_repository_mode", False):
            if not os.path.exists(repository_url):
                raise RepositoryURLError(f"Файл тестового репозитория не найден: {repository_url}")
            if not os.path.isfile(repository_url):
                raise RepositoryURLError("Путь тестового репозитория должен указывать на файл")
        else:
            try:
                result = urlparse(repository_url)
                if not all([result.scheme, result.netloc]):
                    raise RepositoryURLError("Некорректный URL репозитория")
                if result.scheme not in ['http', 'https', 'ftp']:
                    raise RepositoryURLError("Неподдерживаемая схема URL")
            except Exception as e:
                raise RepositoryURLError(f"Ошибка парсинга URL: {e}")

    def _validate_test_repository_mode(self) -> None:
        test_mode = self.config.get("test_repository_mode")

        if not isinstance(test_mode, bool):
            raise TestModeError("Режим тестового репозитория должен быть булевым значением")

    def _validate_version(self) -> None:
        version = self.config.get("version", "latest")

        if not isinstance(version, str):
            raise VersionError("Версия пакета должна быть строкой")

        if version != "latest":
            version_parts = version.split('.')
            if len(version_parts) not in [1, 2, 3]:
                raise VersionError("Некорректный формат версии")

            for part in version_parts:
                if not part.isdigit():
                    raise VersionError("Версия должна состоять из цифр, разделенных точками")

    def _validate_filter_substring(self) -> None:
        filter_substring = self.config.get("filter_substring", "")

        if not isinstance(filter_substring, str):
            raise FilterError("Подстрока для фильтрации должна быть строкой")

        if len(filter_substring) > 50:
            raise FilterError("Подстрока для фильтрации слишком длинная (максимум 50 символов)")

    def display_config(self) -> None:
        print("=" * 50)
        print("Конфигурация визуализатора зависимостей:")
        print("=" * 50)

        for key, value in self.config.items():
            print(f"{key}: {value}")

        print("=" * 50)

    def run(self) -> None:
        try:
            # 1. Загрузка конфигурации
            self.load_config()

            # 2. Валидация параметров
            self.validate_config()

            # 3. ВЫВОД ПАРАМЕТРОВ (главное требование этапа)
            self.display_config()

            # 4. Завершение работы (минимальный прототип)
            print("Этап 1 завершен. Конфигурация проверена и выведена.")

        except ConfigError as e:
            print(f"Ошибка конфигурации: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Неожиданная ошибка: {e}", file=sys.stderr)
            sys.exit(1)


def main():
    visualizer = DependencyVisualizer()
    visualizer.run()

if __name__ == "__main__":
    main()