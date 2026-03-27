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
            print("Проекты не найдены. Создаю тестовый проект...")
            from app.db.crud import create_project
            create_project(db, schemas.ProjectCreate(name="Тестовый проект", code="TST", templates=["land", "drujba", "management", "school"]))
            projects = db.query(models.Project).all()
        
        if not users:
            print("Не удалось создать пользователей. Проверьте настройки.")
            return

        # Создаем еще несколько случайных сотрудников для разнообразия филиалов
        additional_branches = ["Школа", "Детский сад", "СПАРТА", "Администрация"]
        for i in range(len(additional_branches)):
            login = f"staff_{i+1}"
            branch = additional_branches[i]
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
                    status="active"
                )
                db.add(new_staff)
                db.commit()
        
        # Обновляем список пользователей для генерации
        users = db.query(models.TeamMember).filter(models.TeamMember.login != "admin").all()

        print("Генерация тестовых данных через CRUD...")
        
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
            req_type = random.choice(types)
            
            # Bias toward approved/confirmed statuses for better charts (70% probability)
            if random.random() < 0.7:
                status = random.choice([schemas.ExpenseStatusEnum.confirmed, schemas.ExpenseStatusEnum.approved_senior])
            else:
                status = random.choice(statuses)
                
            currency = random.choice(currencies)
            
            items = []
            for j in range(random.randint(1, 4)):
                amount = round(random.uniform(10, 500) if currency == schemas.CurrencyEnum.USD else random.uniform(50000, 2000000), 2)
                items.append(schemas.ExpenseItemSchema(
                    name=f"Тестовый товар {i}-{j}",
                    quantity=Decimal(random.randint(1, 5)),
                    amount=Decimal(str(amount)),
                    currency=currency
                ))
            
            is_bot = random.choice([True, False])
            file_id = f"AgACAgIAAxkBAAIE_test_{i}" if is_bot else None
            
            total_amount = sum(item.amount * item.quantity for item in items)
            
            refund_data = None
            if "refund" in req_type:
                refund_data = schemas.RefundDataSchema(
                    client_name=f"Клиент {i}",
                    reason="Тестовая причина возврата",
                    amount=float(total_amount)
                )

            # Spread dates more evenly over the month
            # Ensure at least 3-4 items per day for a visible line
            day_offset = random.randint(0, 30)
            req_date = datetime.datetime.now() - datetime.timedelta(days=day_offset)

            expense_in = schemas.ExpenseRequestCreate(
                purpose=f"Тестовая заявка {i} (Бот: {'Да' if is_bot else 'Нет'})",
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
            
            usd_rate = Decimal("12800.0") if currency == schemas.CurrencyEnum.USD else None

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
                    comment="Автоматический тестовый статус"
                )
                update_expense_status(
                    db=db,
                    expense_id=new_req.id,
                    update=status_update,
                    user_id=user.id,
                    user_name=f"{user.last_name} {user.first_name}"
                )
                
        print("Тестовые данные успешно сгенерированы! Вы можете проверить статистику.")

    except Exception as e:
        print(f"Ошибка при генерации данных: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_test_data()

