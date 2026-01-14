#!/usr/bin/env python3
"""
Скрипт для инициализации .env файла и создания симлинков.
"""

import os
import sys
from pathlib import Path


def create_env_file(env_path: Path) -> bool:
    """Создаёт .env файл с шаблоном переменных окружения.

    Returns:
        True если файл был создан или уже существует, False если отменено
    """
    if env_path.exists():
        print(f"⚠️  Файл {env_path} уже существует")
        response = input("Перезаписать? (y/N): ").strip().lower()
        if response != "y":
            print("⏭️  Используется существующий файл")
            return True

    env_template = """# Telegram Bot Token (получить у @BotFather)
BOT_TOKEN=

# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=vmeste_db
POSTGRES_PORT=5432

# Backend API
API_BASE_URL=http://localhost:8000/api/v1

# Database URL (для backend, формируется автоматически из POSTGRES_*)
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/vmeste_db

# Debug режим
DEBUG=false
"""

    env_path.write_text(env_template, encoding="utf-8")
    print(f"✅ Создан файл {env_path}")
    return True


def create_symlink(target: Path, link_path: Path) -> None:
    """Создаёт симлинк на .env файл."""
    # Удаляем существующий файл/симлинк, если есть
    if link_path.exists() or link_path.is_symlink():
        if link_path.is_symlink():
            link_path.unlink()
            print(f"🔄 Удалён старый симлинк {link_path}")
        else:
            response = (
                input(f"⚠️  {link_path} уже существует. Заменить на симлинк? (y/N): ")
                .strip()
                .lower()
            )
            if response != "y":
                print(f"⏭️  Пропущен {link_path}")
                return
            link_path.unlink()

    try:
        # Создаём относительный симлинк
        relative_target = os.path.relpath(target, link_path.parent)
        link_path.symlink_to(relative_target)
        print(f"✅ Создан симлинк {link_path} -> {relative_target}")
    except OSError as e:
        print(f"❌ Ошибка при создании симлинка {link_path}: {e}")


def main():
    """Основная функция инициализации."""
    # Определяем корневую директорию проекта
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    env_file = project_root / ".env"
    symlinks = [
        project_root / "bot" / ".env",
        project_root / "backend" / ".env",
        project_root / "deployment" / ".env",
    ]

    print("🚀 Инициализация .env файла и симлинков...\n")

    # Создаём .env файл
    if not create_env_file(env_file):
        print("\n❌ Инициализация отменена")
        sys.exit(0)

    # Создаём симлинки только если .env существует
    if env_file.exists():
        print("\n📎 Создание симлинков...")
        for symlink in symlinks:
            # Создаём директорию, если её нет
            symlink.parent.mkdir(parents=True, exist_ok=True)
            create_symlink(env_file, symlink)

        print("\n✅ Инициализация завершена!")
        print(f"\n📝 Отредактируйте {env_file} и укажите необходимые переменные окружения")
    else:
        print("\n❌ Не удалось создать .env файл")
        sys.exit(1)


if __name__ == "__main__":
    main()
