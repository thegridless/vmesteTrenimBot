#!/usr/bin/env python3
"""
Скрипт для запуска docker-compose с очисткой и пересборкой образов.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], check: bool = True) -> int:
    """Выполняет команду и выводит результат."""
    print(f"🔧 Выполняется: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check)
    return result.returncode


def main():
    """Основная функция запуска docker-compose."""
    # Определяем корневую директорию проекта
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    deployment_dir = project_root / "deployment"

    if not deployment_dir.exists():
        print(f"❌ Директория {deployment_dir} не найдена")
        sys.exit(1)

    docker_compose_file = deployment_dir / "docker-compose.yaml"
    if not docker_compose_file.exists():
        print(f"❌ Файл {docker_compose_file} не найден")
        sys.exit(1)

    print("🚀 Запуск docker-compose с очисткой и пересборкой...\n")

    # Переходим в директорию deployment
    os.chdir(deployment_dir)

    try:
        # 1. Останавливаем и удаляем контейнеры, volumes и образы
        print("📦 Остановка и удаление существующих контейнеров, volumes и образов...")
        run_command(
            ["docker-compose", "down", "-v", "--rmi", "local"],
            check=False,  # Не критично, если контейнеров нет
        )

        # 2. Пересобираем образы
        print("\n🔨 Пересборка образов...")
        run_command(["docker-compose", "build", "--no-cache"])

        # 3. Запускаем сервисы
        print("\n🚀 Запуск сервисов...")
        run_command(["docker-compose", "up", "-d"])

        # 4. Показываем статус
        print("\n📊 Статус сервисов:")
        run_command(["docker-compose", "ps"])

        print("\n✅ Все сервисы запущены!")
        print("\n📝 Полезные команды:")
        print("  - Просмотр логов: docker-compose logs -f")
        print("  - Остановка: docker-compose down")
        print("  - Перезапуск: docker-compose restart")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка при выполнении команды: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)


if __name__ == "__main__":
    main()
