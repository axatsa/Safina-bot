import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.db import models, schemas
from app.services.core.expense_service import expense_service
from app.db.repository.expense_repository import expense_repository
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
        
        users = db.query(models.User).filter(models.User.login != "admin").all()

        projects = db.query(models.Project).all()
        if not projects:
            print("Проекты не найдены. Создаю тестовые проекты...")
            from app.db.repository.project_repository import project_repository
            project_repository.create(db, obj_in=schemas.ProjectCreate(name="Основной проект", code="MAIN", templates=["land", "drujba", "management"]))
            project_repository.create(db, obj_in=schemas.ProjectCreate(name="Школа Safina", code="SCH", templates=["school", "management"]))
            project_repository.create(db, obj_in=schemas.ProjectCreate(name="Детский сад", code="KND", templates=["drujba"]))
            projects = db.query(models.Project).all()
        
        if not users:
            print("Не удалось создать пользователей. Проверьте настройки.")
            return

        # Создаем еще несколько случайных сотрудников для разнообразия филиалов
        print("Создание филиалов...")
        from app.db.repository.branch_repository import branch_repository
        additional_branches = ["Школа", "Детский сад", "СПАРТА", "Администрация", "Бухгалтерия"]
        branch_objs = {}
        for branch_name in additional_branches:
            br = db.query(models.Branch).filter(models.Branch.name == branch_name).first()
            if not br:
                br = branch_repository.create(db, obj_in=schemas.BranchCreate(
                    name=branch_name, 
                    code=branch_name[:3].upper() + str(random.randint(10, 99))
                ), project_id=projects[0].id)
            branch_objs[branch_name] = br

        for i, (branch_name, br_obj) in enumerate(branch_objs.items()):
            login = f"staff_{i+1}"
            existing = db.query(models.User).filter(models.User.login == login).first()
            if not existing:
                print(f"Создание сотрудника для филиала: {branch_name}...")
                new_staff = models.User(
                    login=login,
                    password_hash=auth.get_password_hash("password123"),
                    first_name=f"Сотрудник",
                    last_name=f"{branch_name}",
                    position="staff",
                    status="active",
                    team="Стандарт",
                    role="user"
                )
                new_staff.branches = [br_obj]
                db.add(new_staff)
                db.commit()
        
        # Обновляем список пользователей для генерации
        users = db.query(models.User).filter(models.User.login != "admin").all()

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
                branch_name = random.choice(["Школа", "Детский сад", "Спарта"])
                client_name = f"Клиент {random.randint(100, 999)} Тестовый"
                refund_data = schemas.RefundDataSchema(
                    student_id=f"STD-{random.randint(1000, 9999)}",
                    retention=random.choice([True, False]),
                    branch=branch_name,
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
                branch_id=user.branches[0].id if user.branches else None,
                total_amount=total_amount,
                currency=currency,
                date=req_date,
                request_type=req_type,
                template_key=random.choice(["land", "drujba", "management", "school", "refund", None]),
                receipt_photo_file_id=file_id,
                refund_data=refund_data
            )
            
            from app.services.currency.service import currency_service
            # We bypass the async await here by manually setting usd_rate if needed
            usd_rate = Decimal("12850.0") if currency == schemas.CurrencyEnum.USD else None

            # Создаем заявку
            new_req = expense_service.create_expense_request(
                db=db,
                expense_in=expense_in,
                user_id=user.id,
                usd_rate=usd_rate
            )
            
            # Обновляем статус
            if status != schemas.ExpenseStatusEnum.request:
                expense_repository.update_status(
                    db=db,
                    db_obj=new_req,
                    new_status=status,
                    comment="Автоматический тестовый статус для аналитики",
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

