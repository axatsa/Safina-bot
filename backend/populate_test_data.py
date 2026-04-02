from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.db import models, schemas
from app.db.crud import create_expense_request, update_expense_status
from app.core import auth
import random
from decimal import Decimal
import datetime

def populate_test_data():
    db: Session = SessionLocal()
    try:
        print("Очистка существующих заявок и истории...")
        db.query(models.ExpenseStatusHistory).delete()
        db.query(models.ExpenseRequest).delete()
        db.query(models.ProjectCounter).update({"counter": 0})
        db.commit()

        print("Обновление системных пользователей...")
        from app.db import seed
        seed.seed_users()
        
        users = db.query(models.TeamMember).filter(models.TeamMember.login != "admin").all()

        projects = db.query(models.Project).all()
        if not projects:
            print("Проекты не найдены. Создаю тестовые проекты...")
            from app.db.crud import create_project
            create_project(db, schemas.ProjectCreate(name="Основной проект", code="MAIN", templates=["land", "drujba", "management"]))
            create_project(db, schemas.ProjectCreate(name="Школа Safina", code="SCH", templates=["school", "management"]))
            create_project(db, schemas.ProjectCreate(name="Детский сад", code="KND", templates=["drujba"]))
            projects = db.query(models.Project).all()
        
        if not users:
            print("Не удалось создать пользователей. Проверьте настройки.")
            return

        # Создаем еще несколько случайных сотрудников для разнообразия филиалов
        additional_branches = ["Школа", "Детский сад", "СПАРТА", "Администрация", "Бухгалтерия"]
        for i, branch in enumerate(additional_branches):
            login = f"staff_{i+1}"
            existing = db.query(models.TeamMember).filter(models.TeamMember.login == login).first()
            if not existing:
                print(f"Создание сотрудника для филиала: {branch}...")
                new_staff = models.TeamMember(
                    login=login,
                    password_hash=auth.get_password_hash("password123"),
                    first_name=f"Сотрудник",
                    last_name=f"{branch}",
                    position="staff",
                    branch=branch,
                    status="active",
                    team="Стандарт"
                )
                db.add(new_staff)
                db.commit()
        
        # Обновляем список пользователей для генерации
        users = db.query(models.TeamMember).filter(models.TeamMember.login != "admin").all()

        print("Генерация 100 тестовых заявок с полными данными...")
        
        statuses = [
            schemas.ExpenseStatusEnum.request,
            schemas.ExpenseStatusEnum.review,
            schemas.ExpenseStatusEnum.pending_senior,
            schemas.ExpenseStatusEnum.approved_senior,
            schemas.ExpenseStatusEnum.rejected_senior,
            schemas.ExpenseStatusEnum.confirmed,
            schemas.ExpenseStatusEnum.declined,
            schemas.ExpenseStatusEnum.revision,
            schemas.ExpenseStatusEnum.archived
        ]
        types = ["expense", "refund", "blank", "blank_refund"]
        currencies = [schemas.CurrencyEnum.UZS, schemas.CurrencyEnum.USD]
        
        for i in range(100):
            user = random.choice(users)
            project = random.choice(projects) if random.random() > 0.2 and projects else None
            req_type = random.choices(types, weights=[0.4, 0.2, 0.2, 0.2])[0]
            
            # Bias toward approved/confirmed/archived statuses for better charts (70% probability)
            if random.random() < 0.7:
                status = random.choice([
                    schemas.ExpenseStatusEnum.confirmed, 
                    schemas.ExpenseStatusEnum.approved_senior,
                    schemas.ExpenseStatusEnum.archived
                ])
            else:
                status = random.choice(statuses)
                
            currency = random.choice(currencies)
            
            items = []
            for j in range(random.randint(1, 3)):
                amount = round(random.uniform(10, 500) if currency == schemas.CurrencyEnum.USD else random.uniform(100000, 5000000), 2)
                items.append(schemas.ExpenseItemSchema(
                    name=f"Расходный материал {i}-{j}",
                    quantity=Decimal(random.randint(1, 10)),
                    amount=Decimal(str(amount)),
                    currency=currency
                ))
            
            is_bot = random.choice([True, False])
            file_id = f"AgACAgIAAxkBAAIE_test_file_{i}" if is_bot else None
            
            total_amount = sum(item.amount * item.quantity for item in items)
            
            refund_data = None
            if "refund" in req_type:
                # Генерируем "полные" данные для возврата
                branch = random.choice(["Школа", "Детский сад", "Спарта"])
                client_name = f"Клиент {random.randint(100, 999)} Тестовый"
                refund_data = schemas.RefundDataSchema(
                    student_id=f"STD-{random.randint(1000, 9999)}",
                    retention=random.choice([True, False]),
                    branch=branch,
                    team="Группа-" + str(random.randint(1, 10)),
                    client_name=client_name,
                    passport_series="AA",
                    passport_number=str(random.randint(1000000, 9999999)),
                    passport_issued_by="УВД г. Ташкента",
                    passport_date="2018-10-12",
                    phone="+998901234567",
                    contract_number=f"CNTR-{random.randint(100, 999)}",
                    contract_date="2023-01-15",
                    reason="Тестовая причина возврата: переезд или смена планов",
                    amount=float(total_amount),
                    amount_words="Сумма прописью для проверки",
                    card_holder=client_name,
                    card_number="8600 " + " ".join([str(random.randint(1000, 9999)) for _ in range(3)]),
                    transit_account="20208000" + str(random.randint(100000000000, 999999999999)),
                    bank_iin="301234567",
                    bank_mfo="00450",
                    bank_name="Halyk Bank"
                )

            # Spread dates over the last 60 days
            day_offset = random.randint(0, 60)
            req_date = datetime.datetime.now() - datetime.timedelta(days=day_offset)

            expense_in = schemas.ExpenseRequestCreate(
                purpose=f"Тестовая заявка #{i+1} ({req_type})",
                items=items,
                project_id=project.id if project else None,
                total_amount=total_amount,
                currency=currency,
                date=req_date,
                request_type=req_type,
                template_key=random.choice(["land", "drujba", "management", "school", "refund", None]),
                receipt_photo_file_id=file_id,
                refund_data=refund_data
            )
            
            usd_rate = Decimal("12850.0") if currency == schemas.CurrencyEnum.USD else None

            # Создаем заявку
            new_req = create_expense_request(
                db=db,
                expense=expense_in,
                user_id=user.id,
                usd_rate=usd_rate
            )
            
            # Обновляем статус
            if status != schemas.ExpenseStatusEnum.request:
                status_update = schemas.ExpenseStatusUpdate(
                    status=status,
                    comment="Автоматический тестовый статус для аналитики"
                )
                update_expense_status(
                    db=db,
                    expense_id=new_req.id,
                    update=status_update,
                    user_id=user.id,
                    user_name=f"{user.last_name} {user.first_name}"
                )
                
        print("Тестовые данные успешно сгенерированы! База готова к тестированию аналитики и экспортов.")

    except Exception as e:
        print(f"Ошибка при генерации данных: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_test_data()

