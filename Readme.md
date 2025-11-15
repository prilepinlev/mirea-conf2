## Общее описание

Dependency Visualizer - это инструмент командной строки для анализа и визуализации графов зависимостей npm пакетов. Приложение позволяет строить транзитивные зависимости пакетов, обнаруживать циклические зависимости и фильтровать результаты по различным критериям.

### Основные возможности:

- Анализ зависимостей npm пакетов
    
- Построение полного графа зависимостей с помощью BFS
    
- Обнаружение циклических зависимостей
    
- Фильтрация пакетов по подстроке
    
- Поддержка тестового режима с локальными данными
    
- Статистика графа зависимостей

## Архитектура

Проект состоит из трех основных этапов:

### Этап 1: Конфигурация

- Загрузка параметров из JSON-файла
    
- Валидация конфигурационных параметров
    
- Вывод настроек в формате ключ-значение


### Этап 2: Сбор данных

- Получение информации о пакетах из npm registry
    
- Извлечение прямых зависимостей
    
- Поддержка различных типов зависимостей (dependencies, devDependencies, peerDependencies, optionalDependencies)


### Этап 3: Построение графа

- BFS-обход для построения транзитивного графа
    
- Обнаружение циклических зависимостей
    
- Визуализация дерева зависимостей
    
- Статистический анализ графа


## Описание функций и настроек

### Класс `DependencyVisualizer`

Основной класс приложения, отвечающий за весь процесс анализа зависимостей.

#### Методы:

**Конфигурация:**

- `load_config()` - загрузка конфигурации из JSON-файла
    
- `validate_config()` - валидация параметров конфигурации
    
- `display_config()` - вывод текущих настроек


**Работа с пакетами:**

- `get_npm_package_info(package_name)` - получение информации о пакете из npm registry
    
- `_get_real_package_info(package_name)` - работа с реальным npm registry
    
- `_get_test_package_info(package_name)` - работа с тестовыми данными


**Анализ зависимостей:**

- `extract_dependencies(package_info, package_name)` - извлечение зависимостей из package.json
    
- `build_dependency_graph_bfs()` - построение графа зависимостей с помощью BFS
    
- `_find_cyclic_dependencies()` - поиск циклических зависимостей с помощью DFS


**Визуализация:**

- `display_dependency_graph()` - вывод дерева зависимостей
    
- `_build_pretty_tree_limited()` - форматированное отображение дерева
    
- `analyze_graph_properties()` - вывод статистики графа

### Пример config.json

``` json
{
    "package_name": "express",
    "repository_url": "https://registry.npmjs.org/",
    "test_repository_mode": false,
    "version": "latest",
    "filter_substring": ""
}
```

### Типы зависимостей

Приложение анализирует все типы npm зависимостей:

- **dependencies** - основные зависимости
    
- **devDependencies** - зависимости для разработки
    
- **peerDependencies** - peer-зависимости
    
- **optionalDependencies** - опциональные зависимости

## Команды для сборки и запуска

### Требования

- Python 3.7+
    
- Доступ к интернету (для работы с npm registry)


1. **Клонирование репозитория:**

``` bash
git clone <repository-url>
cd dependency-visualizer
```

2. **Создание конфигурационного файла:**

``` bash
# Создайте config.json в корневой директории
cat > config.json << EOF
{
    "package_name": "express",
    "repository_url": "https://registry.npmjs.org/",
    "test_repository_mode": false,
    "version": "latest",
    "filter_substring": ""
}
EOF
```

3. **Запуск приложения:**

``` bash
python3 dependency_visualizer.py
```

### Запуск тестов

Для тестирования используется режим тестового репозитория:

1. **Создание тестовых данных:**

``` bash 
cat > test_repo.json << EOF
{  
  "REACT": {  
    "name": "REACT",  
    "versions": {  
      "1.0.0": {  
        "dependencies": {  
          "BABEL": "^1.0.0",  
          "WEBPACK": "^1.0.0"  
        }  
      }  
    },  
    "dist-tags": {"latest": "1.0.0"}  
  },  
  "BABEL": {  
    "name": "BABEL",  
    "versions": {  
      "1.0.0": {  
        "dependencies": {  
          "PLUGIN-A": "^1.0.0"  
        }  
      }  
    },  
    "dist-tags": {"latest": "1.0.0"}  
  },  
  "WEBPACK": {  
    "name": "WEBPACK",  
    "versions": {  
      "1.0.0": {  
        "dependencies": {  
          "LOADER": "^1.0.0"  
        }  
      }  
    },  
    "dist-tags": {"latest": "1.0.0"}  
  },  
  "PLUGIN-A": {  
    "name": "PLUGIN-A",  
    "versions": {  
      "1.0.0": {  
        "dependencies": {}  
      }  
    },  
    "dist-tags": {"latest": "1.0.0"}  
  },  
  "LOADER": {  
    "name": "LOADER",  
    "versions": {  
      "1.0.0": {  
        "dependencies": {}  
      }  
    },  
    "dist-tags": {"latest": "1.0.0"}  
  }  
}
EOF
```

2. **Настройка тестового режима:**
``` json
{  
    "package_name": "REACT",  
    "repository_url": "my_test.json",  
    "test_repository_mode": true,  
    "version": "latest",  
    "filter_substring": ""  
}
```

3. **Запуск в тестовом режиме:**

``` bash
python3 dependency_visualizer.py
```

## Примеры использования

### Пример 1: Анализ пакета Express

**Конфигурация:**

``` json
{
    "package_name": "express",
    "repository_url": "https://registry.npmjs.org/",
    "test_repository_mode": false,
    "version": "latest",
    "filter_substring": ""
}
```

``` text
====================================================
ДЕРЕВО ЗАВИСИМОСТЕЙ express:
====================================================
└── express
    ├── body-parser
    │   ├── bytes
    │   ├── debug
    │   └── [...]
    ├── cookie-parser
    │   └── cookie
    └── [...]
====================================================

СТАТИСТИКА ГРАФА:
• Всего пакетов: 45
• Всего зависимостей: 127
• Пакетов без зависимостей: 12
• Обнаружено циклических зависимостей: 0
```

### Пример 2: Анализ с фильтрацией

**Конфигурация:**

``` json
{
    "package_name": "react",
    "repository_url": "https://registry.npmjs.org/",
    "test_repository_mode": false, 
    "version": "18.2.0",
    "filter_substring": "test"
}
```

**Результат:** Все пакеты, содержащие "test" в имени, будут исключены из анализа.

### Пример 3: Тестовый режим с циклическими зависимостями

**Конфигурация:**
``` json
{
    "package_name": "A",
    "repository_url": "test_repo.json",
    "test_repository_mode": true,
    "version": "latest", 
    "filter_substring": ""
}
```

**Результат:**

``` text
====================================================
ДЕРЕВО ЗАВИСИМОСТЕЙ A:
====================================================
└── A
    ├── B
    │   └── D
    │       └── B [ЦИКЛ]
    └── C
        ├── D
        │   └── B [ЦИКЛ]
        └── E
====================================================

СТАТИСТИКА ГРАФА:
• Всего пакетов: 5
• Всего зависимостей: 6  
• Обнаружено циклических зависимостей: 2
```

