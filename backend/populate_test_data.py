from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.db import models, schemas
from app.db.crud import create_expense_request, update_expense_status
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

        print("Получение пользователей и проектов...")
        users = db.query(models.TeamMember).filter(models.TeamMember.login != "admin").all()
        projects = db.query(models.Project).all()
        
        if not users:
            print("Пользователи не найдены. Сначала создайте пользователей.")
            return

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
        
        for i in range(30):
            user = random.choice(users)
            project = random.choice(projects) if random.random() > 0.2 and projects else None
            req_type = random.choice(types)
            status = random.choice(statuses)
            currency = random.choice(currencies)
            
            items = []
            for j in range(random.randint(1, 3)):
                amount = round(random.uniform(10, 500) if currency == schemas.CurrencyEnum.USD else random.uniform(50000, 500000), 2)
                items.append(schemas.ExpenseItemSchema(
                    name=f"Тестовый товар {i}-{j}",
                    quantity=Decimal(random.randint(1, 10)),
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

            expense_in = schemas.ExpenseRequestCreate(
                purpose=f"Тестовая заявка {i} (Бот: {'Да' if is_bot else 'Нет'})",
                items=items,
                project_id=project.id if project else None,
                total_amount=total_amount,
                currency=currency,
                date=datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 30)),
                request_type=req_type,
                template_key=random.choice(["land", "drujba", "management", "school", "refund", None]),
                receipt_photo_file_id=file_id,
                refund_data=refund_data
            )
            
            usd_rate = Decimal("12800.0") if currency == schemas.CurrencyEnum.USD else None

            # Создаем заявку через функцию crud (как это делают бот и веб-форма)
            new_req = create_expense_request(
                db=db,
                expense=expense_in,
                user_id=user.id,
                usd_rate=usd_rate
            )
            
            # Если нужно сменить статус, используем crud функцию обновления статуса
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

