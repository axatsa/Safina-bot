import os
import secrets
import string

def generate_secure_password(length=12):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(length))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)):
            return password

def update_env_file(env_path, safina_pass, sf_pass):
    env_content = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        env_content[parts[0]] = parts[1]
    
    env_content['ADMIN_LOGIN'] = 'safina'
    env_content['ADMIN_PASSWORD'] = safina_pass
    env_content['SF_LOGIN'] = 'farrukh'
    env_content['SF_PASSWORD'] = sf_pass

    with open(env_path, 'w', encoding='utf-8') as f:
        for k, v in env_content.items():
            f.write(f"{k}={v}\n")

if __name__ == "__main__":
    print("Генерация безопасных доступов для системы...")
    
    safina_pass = generate_secure_password()
    sf_pass = generate_secure_password()
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base_dir, ".env")
    
    update_env_file(env_path, safina_pass, sf_pass)
    
    print("\n" + "="*50)
    print("УЧЕТНЫЕ ДАННЫЕ УСПЕШНО СГЕНЕРИРОВАНЫ И СОХРАНЕНЫ В .env")
    print("="*50)
    print(f"Роль: Менеджер (Web-App Dashboard)")
    print(f"Логин: safina")
    print(f"Пароль: {safina_pass}")
    print("-" * 50)
    print(f"Роль: Старший Финансист (Telegram Bot)")
    print(f"Логин: farrukh")
    print(f"Пароль: {sf_pass}")
    print("="*50 + "\n")
    
    # Теперь запускаем наполнение базы данных
    print("Запуск наполнения базы данных тестовыми данными...")
    import sys
    sys.path.append(base_dir)
    
    try:
        from populate_test_data import populate_test_data
        populate_test_data()
        print("\n" + "="*50)
        print("БАЗА ДАННЫХ УСПЕШНО НАПОЛНЕНА ПОЛНЫМИ ТЕСТОВЫМИ ДАННЫМИ")
        print("="*50)
    except Exception as e:
        print(f"Ошибка при наполнении базы данных: {e}")
        print("Вы можете запустить наполнение вручную: python populate_test_data.py")

    print("\nПодсказка: Для применения новых учетных данных, перезапустите приложение.")
