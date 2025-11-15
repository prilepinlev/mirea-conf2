#!/usr/bin/env python3

import json
import os
import sys
from typing import Dict, Any, List, Set, Tuple
from urllib.parse import urlparse
import urllib.request
import urllib.error
from collections import deque

class ConfigError(Exception):
    """Базовое исключение для ошибок конфигурации"""
    pass

class DependencyFetchError(ConfigError):
    """Ошибка получения зависимостей"""
    pass

class DependencyVisualizer:
    """Класс для визуализации графа зависимостей пакетов"""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.dependency_graph: Dict[str, List[str]] = {}
        self.visited_packages: Set[str] = set()
        self.package_cache: Dict[str, Dict[str, Any]] = {}
        self.package_depths: Dict[str, int] = {}

    def load_config(self) -> None:
        try:
            if not os.path.exists(self.config_file):
                raise ConfigError(f"Конфигурационный файл '{self.config_file}' не найден")

            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.loads(f.read().strip())

        except Exception as e:
            raise ConfigError(f"Ошибка загрузки конфига: {e}")

    def validate_config(self) -> None:
        if not self.config.get("package_name"):
            raise ConfigError("Имя пакета не может быть пустым")

    def get_npm_package_info(self, package_name: str) -> Dict[str, Any]:
        if self.config.get("test_repository_mode", False):
            return self._get_test_package_info(package_name)
        else:
            return self._get_real_package_info(package_name)

    def _get_real_package_info(self, package_name: str) -> Dict[str, Any]:
        """Получает информацию о реальном пакете"""
        try:
            url = f"https://registry.npmjs.org/{package_name}"
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'DependencyVisualizer/1.0'}
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))

        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise DependencyFetchError(f"Пакет '{package_name}' не найден в npm registry. Проверьте имя пакета.")
            else:
                raise DependencyFetchError(f"HTTP ошибка {e.code} для пакета '{package_name}': {e.reason}")
        except Exception as e:
            raise DependencyFetchError(f"Ошибка получения пакета '{package_name}': {e}")

    def _get_test_package_info(self, package_name: str) -> Dict[str, Any]:
        """Получает информацию о тестовом пакете из файла"""
        try:
            with open(self.config["repository_url"], 'r', encoding='utf-8') as f:
                test_data = json.loads(f.read())

            # Ищем пакет в тестовых данных (пакеты называются большими буквами)
            if package_name in test_data:
                return test_data[package_name]
            else:
                # Если пакет не найден, возвращаем пустые зависимости
                return {
                    "name": package_name,
                    "versions": {
                        "1.0.0": {
                            "dependencies": {}
                        }
                    },
                    "dist-tags": {"latest": "1.0.0"}
                }

        except Exception as e:
            raise DependencyFetchError(f"Ошибка чтения тестового файла: {e}")

    def extract_dependencies(self, package_info: Dict[str, Any], package_name: str) -> List[str]:

        version = self.config["version"]

        # Определяем версию
        if version == "latest":
            target_version = package_info.get('dist-tags', {}).get('latest', '1.0.0')
        else:
            target_version = version

        # Получаем информацию о версии
        version_info = package_info.get('versions', {}).get(target_version, {})
        if not version_info:
            # Если версия не найдена, берем первую доступную
            versions = list(package_info.get('versions', {}).keys())
            if versions:
                version_info = package_info['versions'][versions[0]]
            else:
                return []

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

        # Убираем дубликаты
        unique_dependencies = list(set(dependencies))

        # ПРИМЕНЯЕМ ФИЛЬТР (требование этапа 3)
        filter_substring = self.config.get("filter_substring", "")
        if filter_substring:
            unique_dependencies = [
                dep for dep in unique_dependencies
                if filter_substring.lower() not in dep.lower()
            ]

        return sorted(unique_dependencies)

    def build_dependency_graph_bfs(self) -> None:

        start_package = self.config["package_name"]
        self.dependency_graph = {}
        self.visited_packages = set()
        self.package_cache = {}
        self.package_depths = {start_package: 0}

        max_depth = 4
        max_packages = 300

        queue = deque([(start_package, 0)])
        self.visited_packages.add(start_package)

        processed_count = 0

        while queue and len(self.visited_packages) < max_packages:
            current_package, current_depth = queue.popleft()
            processed_count += 1

            print(f"[{processed_count}/{max_packages}] Анализ {current_package} (глубина: {current_depth})...")

            try:
                # Получаем информацию о пакете
                package_info = self.get_npm_package_info(current_package)

                # Извлекаем зависимости
                dependencies = self.extract_dependencies(package_info, current_package)

                # Сохраняем зависимости в граф
                self.dependency_graph[current_package] = dependencies

                if current_depth < max_depth:
                    for dep in dependencies:
                        if (dep not in self.visited_packages and
                                len(self.visited_packages) < max_packages):

                            #УПРОЩЕННАЯ ПРОВЕРКА ЦИКЛОВ
                            if dep not in self.visited_packages:
                                self.visited_packages.add(dep)
                                self.package_depths[dep] = current_depth + 1
                                queue.append((dep, current_depth + 1))
                else:
                    #Достигли максимальной глубины - не анализируем дальше
                    print(f"Достигнута максимальная глубина {max_depth} для {current_package}")

            except DependencyFetchError as e:
                print(f"Ошибка получения пакета {current_package}: {e}")
                self.dependency_graph[current_package] = []

        print(f"Проанализировано пакетов: {len(self.dependency_graph)}")
        print(f"Всего зависимостей в графе: {sum(len(deps) for deps in self.dependency_graph.values())}")
        print(f"Максимальная глубина анализа: {max_depth}")

    def display_dependency_graph(self) -> None:
        """ВЫВОД ГРАФА С ОГРАНИЧЕНИЕМ ГЛУБИНЫ"""
        if not self.dependency_graph:
            print("Граф зависимостей пуст")
            return

        print("\n" + "=" * 60)
        print(f"ДЕРЕВО ЗАВИСИМОСТЕЙ {self.config['package_name']}:")
        print("=" * 60)

        start_package = self.config["package_name"]

        # Строим дерево с ограничением глубины
        tree_lines = self._build_pretty_tree_limited(start_package, "", True, set(), 0)
        for line in tree_lines:
            print(line)

        print("=" * 60)

    def _build_pretty_tree_limited(self, package: str, prefix: str, is_last: bool, visited: set, current_depth: int) -> \
    List[str]:
        #if current_depth > 4:
            #return [f"{prefix}└── ... (глубже 4 уровней)"]

        if package in visited:
            return [f"{prefix}└── {package} [ЦИКЛ]"]

        visited.add(package)

        # Текущий пакет
        current_prefix = "└── " if is_last else "├── "
        lines = [f"{prefix}{current_prefix}{package}"]

        # Зависимости этого пакета
        dependencies = self.dependency_graph.get(package, [])

        new_prefix = prefix + ("    " if is_last else "│   ")

        for i, dep in enumerate(dependencies):
            is_last_dep = (i == len(dependencies) - 1)
            child_lines = self._build_pretty_tree_limited(dep, new_prefix, is_last_dep, visited.copy(),
                                                          current_depth + 1)
            lines.extend(child_lines)

        return lines

    def analyze_graph_properties(self) -> None:

        if not self.dependency_graph:
            return

        print("\nСТАТИСТИКА ГРАФА:")
        print("-" * 40)

        # Количество пакетов
        total_packages = len(self.dependency_graph)
        print(f"• Всего пакетов: {total_packages}")

        # Количество зависимостей
        total_dependencies = sum(len(deps) for deps in self.dependency_graph.values())
        print(f"• Всего зависимостей: {total_dependencies}")

        # Пакеты без зависимостей
        leaf_packages = [pkg for pkg, deps in self.dependency_graph.items() if not deps]
        print(f"• Пакетов без зависимостей: {len(leaf_packages)}")

        # Статистика по уровням
        level_stats = {}
        for pkg, depth in self.package_depths.items():
            if depth not in level_stats:
                level_stats[depth] = 0
            level_stats[depth] += 1

        print(f"• Распределение по уровням:")
        for level in sorted(level_stats.keys()):
            print(f"  Уровень {level}: {level_stats[level]} зависимостей")

        # Циклические зависимости
        cyclic_deps = self._find_cyclic_dependencies()
        print(f"• Обнаружено циклических зависимостей: {len(cyclic_deps)}")

    def _find_cyclic_dependencies(self) -> List[List[str]]:
        cycles = []
        visited = set()

        def dfs(node, path):
            if node in path:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return

            if node in visited:
                return

            visited.add(node)
            path.append(node)

            for neighbor in self.dependency_graph.get(node, []):
                if neighbor in self.dependency_graph:
                    dfs(neighbor, path.copy())

        for package in self.dependency_graph:
            dfs(package, [])

        return cycles

    def run(self) -> None:
        try:
            self.load_config()
            self.validate_config()

            print("=" * 60)
            print("ВИЗУАЛИЗАТОР ЗАВИСИМОСТЕЙ - ЭТАП 3")
            print("=" * 60)

            # 2. Вывод конфигурации
            print("Конфигурация:")
            for key, value in self.config.items():
                print(f"  {key}: {value}")

            # 3. Построение графа зависимостей с помощью BFS
            print(f"\nПостроение графа для {self.config['package_name']}...")
            self.build_dependency_graph_bfs()

            # 4. ВЫВОД ГРАФА (главное требование этапа)
            self.display_dependency_graph()

            # 5. Дополнительная статистика
            self.analyze_graph_properties()

            print(f"\nЭтап 3 завершен. Граф построен и выведен.")

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