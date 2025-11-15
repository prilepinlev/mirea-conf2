#!/usr/bin/env python3
import json
import os
import sys
from typing import Dict, Any, List
from urllib.parse import urlparse
import urllib.request
import urllib.error

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

class DependencyFetchError(ConfigError):
    """Ошибка получения зависимостей"""
    pass


class DependencyVisualizer:
    """Класс для визуализации графа зависимостей пакетов"""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.dependencies: List[str] = []

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

        # Для npm пакетов допустимы символы: буквы, цифры, -, _, ., @, /
        if not all(c.isalnum() or c in ['-', '_', '.', '@', '/'] for c in package_name):
            raise PackageNameError("Имя пакета содержит недопустимые символы")

        if len(package_name) > 214:  # Максимальная длина npm пакета
            raise PackageNameError("Имя пакета слишком длинное")

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
                if result.scheme not in ['http', 'https']:
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

        # Для npm версии могут быть: 1.2.3, ^1.2.3, ~1.2.3, latest и т.д.
        if version != "latest" and len(version) > 100:
            raise VersionError("Версия пакета слишком длинная")

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

    def get_npm_package_info(self) -> Dict[str, Any]:

        package_name = self.config["package_name"]
        version = self.config["version"]

        # URL npm registry API
        if self.config.get("test_repository_mode", False):
            # Тестовый режим - читаем из локального файла
            try:
                with open(self.config["repository_url"], 'r', encoding='utf-8') as f:
                    return json.loads(f.read())
            except Exception as e:
                raise DependencyFetchError(f"Ошибка чтения тестового файла: {e}")
        else:
            try:
                url = f"https://registry.npmjs.org/{package_name}"

                req = urllib.request.Request(
                    url,
                    headers={'User-Agent': 'DependencyVisualizer/1.0'}
                )

                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode('utf-8'))

                return data

            except urllib.error.HTTPError as e:
                if e.code == 404:
                    raise DependencyFetchError(f"Пакет '{package_name}' не найден в npm registry")
                else:
                    raise DependencyFetchError(f"HTTP ошибка {e.code}: {e.reason}")
            except urllib.error.URLError as e:
                raise DependencyFetchError(f"Ошибка сети: {e.reason}")
            except Exception as e:
                raise DependencyFetchError(f"Ошибка получения данных: {e}")

    def extract_dependencies(self, package_info: Dict[str, Any]) -> List[str]:

        version = self.config["version"]

        # Определяем какую версию использовать
        if version == "latest":
            target_version = package_info.get('dist-tags', {}).get('latest', '')
            if not target_version:
                # Если нет latest, берем последнюю версию из versions
                versions = list(package_info.get('versions', {}).keys())
                if versions:
                    target_version = versions[-1]  # Последняя версия
                else:
                    raise DependencyFetchError("Не найдено ни одной версии пакета")
        else:
            target_version = version

        # Получаем информацию о конкретной версии
        version_info = package_info.get('versions', {}).get(target_version)
        if not version_info:
            available_versions = list(package_info.get('versions', {}).keys())
            raise DependencyFetchError(
                f"Версия '{target_version}' не найдена. "
                f"Доступные версии: {', '.join(available_versions[:5])}"
                f"{'...' if len(available_versions) > 5 else ''}"
            )

        # Извлекаем зависимости
        dependencies = []

        # dependencies - обычные зависимости
        deps = version_info.get('dependencies', {})
        dependencies.extend(deps.keys())

        # devDependencies - зависимости разработки
        dev_deps = version_info.get('devDependencies', {})
        dependencies.extend(dev_deps.keys())

        # peerDependencies - peer зависимости
        peer_deps = version_info.get('peerDependencies', {})
        dependencies.extend(peer_deps.keys())

        # optionalDependencies - опциональные зависимости
        optional_deps = version_info.get('optionalDependencies', {})
        dependencies.extend(optional_deps.keys())

        # Убираем дубликаты и применяем фильтр
        unique_dependencies = list(set(dependencies))

        # Применяем фильтр если указан
        filter_substring = self.config.get("filter_substring", "")
        if filter_substring:
            unique_dependencies = [
                dep for dep in unique_dependencies
                if filter_substring.lower() in dep.lower()
            ]

        return sorted(unique_dependencies)

    def display_dependencies(self) -> None:
        if not self.dependencies:
            print("Прямые зависимости не найдены")
            return

        print("\n" + "=" * 50)
        print(f"ПРЯМЫЕ ЗАВИСИМОСТИ пакета {self.config['package_name']}:")
        print("=" * 50)

        for i, dependency in enumerate(self.dependencies, 1):
            print(f"{i:2d}. {dependency}")

        print("=" * 50)
        print(f"Всего найдено зависимостей: {len(self.dependencies)}")

    def run(self) -> None:
        try:
            # 1. Загрузка и валидация конфигурации
            self.load_config()
            self.validate_config()

            # 2. Вывод конфигурации (из Этапа 1)
            self.display_config()

            # 3. ЭТАП 2: Получение и вывод зависимостей
            print(f"\nПолучение информации о пакете {self.config['package_name']}...")

            package_info = self.get_npm_package_info()
            self.dependencies = self.extract_dependencies(package_info)

            # 4. ВЫВОД ЗАВИСИМОСТЕЙ (главное требование этапа 2)
            self.display_dependencies()

            print(f"\nЭтап 2 завершен. Зависимости получены и выведены.")

        except (ConfigError, DependencyFetchError) as e:
            print(f"Ошибка: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Неожиданная ошибка: {e}", file=sys.stderr)
            sys.exit(1)


def main():
    visualizer = DependencyVisualizer()
    visualizer.run()


if __name__ == "__main__":
    main()