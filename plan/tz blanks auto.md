# ТЗ — Система шаблонов бланков с автоматическим определением
## Safina Finance Bot · checkpoint branch

---

## Суть задачи

Сейчас в главном меню бота нет кнопок для бланков вообще (в ветке checkpoint).
Нужно реализовать систему где:
- У каждого **проекта** можно выбрать один или несколько шаблонов бланков
- У каждого **сотрудника** можно выдать личные дополнительные шаблоны
- В боте одна кнопка "📋 Заполнить бланк" — шаблон определяется автоматически

---

## Доступные шаблоны (константа, не меняется)

```
land        → LAND.docx        → "📋 LAND"
drujba      → Drujba.docx      → "📋 ЛС (Дружба)"
management  → Management.docx  → "📋 Management"
school      → School.docx      → "📋 School"
```

---

## ЧАСТЬ 1 — БАЗА ДАННЫХ

### 1.1 Модель `Project` (`app/db/models.py`)

Добавить одно поле после `code`:

```python
class Project(Base):
    __tablename__ = "projects"

    id         = Column(String, primary_key=True, default=generate_uuid)
    name       = Column(String, nullable=False)
    code       = Column(String, unique=True, nullable=False, index=True)
    templates  = Column(JSON, nullable=False, default=list)   # ← ДОБАВИТЬ
    # Хранит список ключей: [] или ["land"] или ["land", "management"]
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    # relationships — без изменений
```

### 1.2 Модель `TeamMember` (`app/db/models.py`)

Добавить одно поле после `team`:

```python
class TeamMember(Base):
    # ...
    branch    = Column(String, nullable=True)
    team      = Column(String, nullable=True)
    templates = Column(JSON, nullable=False, default=list)   # ← ДОБАВИТЬ
    # Личные шаблоны сверх проектных: [] или ["school"]
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    # relationships — без изменений
```

### 1.3 Alembic миграция

Создать файл `alembic/versions/XXXX_add_templates_fields.py`:

```python
"""add templates to projects and team_members

Revision ID: add_templates_fields
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column("projects",
        sa.Column("templates", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("team_members",
        sa.Column("templates", sa.JSON(), nullable=False, server_default="[]"))

def downgrade():
    op.drop_column("projects", "templates")
    op.drop_column("team_members", "templates")
```

`server_default="[]"` — все существующие строки получат пустой список.
Миграция запустится автоматически через `entrypoint.sh` при деплое.

---

## ЧАСТЬ 2 — СХЕМЫ И ВАЛИДАЦИЯ (`app/db/schemas.py`)

### 2.1 Добавить константу допустимых ключей

В начало файла после импортов:

```python
AVAILABLE_TEMPLATE_KEYS = {"land", "drujba", "management", "school"}
```

### 2.2 Обновить `ProjectBase`

```python
class ProjectBase(BaseModel):
    name:      str
    code:      str
    templates: List[str] = []    # ← ДОБАВИТЬ
```

`ProjectCreate` наследует от `ProjectBase` — изменять не нужно, поле
подтянется автоматически.

### 2.3 Обновить `ProjectSchema`

```python
class ProjectSchema(ProjectBase):   # templates уже есть через наследование
    id: str
    created_at: datetime
    members: List[MemberSummary] = []

    class Config:
        from_attributes = True
```

### 2.4 Обновить `TeamMemberBase`

```python
class TeamMemberBase(BaseModel):
    last_name:  str
    first_name: str
    login:      str
    position:   Optional[str] = None
    status:     str = "active"
    branch:     Optional[str] = None
    team:       Optional[str] = None
    templates:  List[str] = []    # ← ДОБАВИТЬ
```

`TeamMemberSchema` наследует от `TeamMemberBase` — изменять не нужно.

### 2.5 Добавить две новые схемы для PATCH эндпоинтов

```python
class ProjectTemplatesUpdate(BaseModel):
    templates: List[str]

    @validator("templates")
    def validate_keys(cls, v):
        invalid = set(v) - AVAILABLE_TEMPLATE_KEYS
        if invalid:
            raise ValueError(f"Неизвестные ключи: {invalid}. "
                             f"Допустимые: {AVAILABLE_TEMPLATE_KEYS}")
        return list(dict.fromkeys(v))   # убрать дубликаты, сохранить порядок


class TeamMemberTemplatesUpdate(BaseModel):
    templates: List[str]

    @validator("templates")
    def validate_keys(cls, v):
        invalid = set(v) - AVAILABLE_TEMPLATE_KEYS
        if invalid:
            raise ValueError(f"Неизвестные ключи: {invalid}.")
        return list(dict.fromkeys(v))
```

---

## ЧАСТЬ 3 — CRUD (`app/db/crud.py`)

В функции `create_project` добавить сохранение `templates`:

```python
def create_project(db: Session, project: schemas.ProjectCreate):
    db_project = models.Project(
        name=project.name,
        code=project.code,
        templates=project.templates,    # ← ДОБАВИТЬ
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    # создание counter — без изменений
    return db_project
```

---

## ЧАСТЬ 4 — API ЭНДПОИНТЫ

### 4.1 Новый эндпоинт для шаблонов проекта (`app/api/projects.py`)

Добавить в конец файла:

```python
@router.patch("/{project_id}/templates", response_model=schemas.ProjectSchema)
def update_project_templates(
    project_id: str,
    update: schemas.ProjectTemplatesUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.TeamMember = Depends(auth.get_current_user)
):
    """Обновить список шаблонов бланков для проекта."""
    if current_user.login != os.getenv("ADMIN_LOGIN", "safina"):
        raise HTTPException(status_code=403, detail="Only admins can manage templates")

    project = db.query(models.Project).filter(
        models.Project.id == project_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.templates = update.templates
    db.commit()
    db.refresh(project)
    return project
```

### 4.2 Новый эндпоинт для шаблонов сотрудника (`app/api/team.py`)

Добавить в конец файла:

```python
@router.patch("/{member_id}/templates", response_model=schemas.TeamMemberSchema)
def update_member_templates(
    member_id: str,
    update: schemas.TeamMemberTemplatesUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.TeamMember = Depends(auth.get_current_user)
):
    """Выдать сотруднику личные шаблоны бланков."""
    if current_user.login != os.getenv("ADMIN_LOGIN", "safina"):
        raise HTTPException(status_code=403, detail="Only admins can manage templates")

    member = db.query(models.TeamMember).filter(
        models.TeamMember.id == member_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.templates = update.templates
    db.commit()
    db.refresh(member)
    return member
```

---

## ЧАСТЬ 5 — ФРОНТЕНД

### 5.1 Типы (`frontend/src/lib/types.ts`)

Добавить `templates` в оба интерфейса:

```typescript
export interface Project {
  id: string;
  name: string;
  code: string;
  templates: string[];    // ← ДОБАВИТЬ
  createdAt: Date;
  members: Array<{
    id: string;
    lastName: string;
    firstName: string;
    position?: string;
  }>;
}

export interface TeamMember {
  id: string;
  lastName: string;
  firstName: string;
  position?: string;
  projectIds?: string[];
  projects?: Project[];
  login: string;
  password?: string;
  branch?: string;
  team?: string;
  templates: string[];    // ← ДОБАВИТЬ
  // остальные поля без изменений
}

// Добавить константу шаблонов для использования в UI
export const AVAILABLE_TEMPLATES = [
  { key: "land",       label: "📋 LAND"        },
  { key: "drujba",     label: "📋 ЛС (Дружба)" },
  { key: "management", label: "📋 Management"   },
  { key: "school",     label: "📋 School"       },
] as const;
```

### 5.2 Сервисы (`frontend/src/lib/store.ts` или `services/`)

Добавить два метода:

```typescript
// Обновить шаблоны проекта
updateProjectTemplates: async (
  projectId: string,
  templates: string[]
): Promise<Project> => {
  const res = await apiFetch(`/projects/${projectId}/templates`, {
    method: "PATCH",
    body: JSON.stringify({ templates }),
  });
  const data = await res.json();
  return mapProject(data);  // используй существующий маппер
},

// Обновить личные шаблоны сотрудника
updateMemberTemplates: async (
  memberId: string,
  templates: string[]
): Promise<TeamMember> => {
  const res = await apiFetch(`/team/${memberId}/templates`, {
    method: "PATCH",
    body: JSON.stringify({ templates }),
  });
  const data = await res.json();
  return mapTeamMember(data);  // используй существующий маппер
},
```

### 5.3 Страница проектов (`frontend/src/pages/Projects.tsx`)

**Изменение 1** — Добавить `templates` в состояние формы:

```typescript
const [formData, setFormData] = useState({
  name: "",
  code: "",
  templates: [] as string[],    // ← ДОБАВИТЬ
});
```

**Изменение 2** — Добавить мультиселект в форму создания проекта,
после поля `code` и перед кнопкой Submit:

```tsx
<div className="space-y-2">
  <Label>Шаблоны бланков</Label>
  <p className="text-xs text-muted-foreground">
    Какие бланки доступны сотрудникам этого проекта в боте
  </p>
  <div className="flex flex-wrap gap-2">
    {AVAILABLE_TEMPLATES.map((tpl) => {
      const selected = formData.templates.includes(tpl.key);
      return (
        <button
          key={tpl.key}
          type="button"
          onClick={() => setFormData(prev => ({
            ...prev,
            templates: selected
              ? prev.templates.filter(t => t !== tpl.key)
              : [...prev.templates, tpl.key]
          }))}
          className={cn(
            "px-3 py-1.5 rounded-lg text-sm border transition-colors",
            selected
              ? "bg-primary text-primary-foreground border-primary"
              : "bg-background border-border hover:bg-muted"
          )}
        >
          {tpl.label}
        </button>
      );
    })}
  </div>
  {formData.templates.length === 0 && (
    <p className="text-xs text-amber-500">
      ⚠️ Не выбрано — сотрудники будут видеть все шаблоны
    </p>
  )}
</div>
```

**Изменение 3** — Передавать `templates` при создании проекта:

```typescript
// Уже есть:
mutation.mutate(formData);   // теперь formData содержит templates — ничего менять не нужно

// Сброс формы после создания:
setFormData({ name: "", code: "", templates: [] });
```

**Изменение 4** — Показывать шаблоны в карточке существующего проекта
(рядом с кодом проекта):

```tsx
{/* Добавить после строки с кодом проекта */}
<div className="flex flex-wrap gap-1 mt-1">
  {project.templates?.length > 0
    ? project.templates.map(key => {
        const tpl = AVAILABLE_TEMPLATES.find(t => t.key === key);
        return (
          <span key={key} className="text-xs bg-blue-50 text-blue-700
                                     px-2 py-0.5 rounded border border-blue-200">
            {tpl?.label ?? key}
          </span>
        );
      })
    : <span className="text-xs text-muted-foreground italic">
        Шаблоны не настроены
      </span>
  }
</div>
```

### 5.4 Страница команды (`frontend/src/pages/Team.tsx`)

В карточке сотрудника или в диалоге редактирования добавить секцию
"Личные шаблоны". Отображать какие шаблоны уже идут от проекта (серые),
а какие выданы лично (синие):

```tsx
{/* Секция личных шаблонов в карточке/диалоге сотрудника */}
<div className="space-y-2 mt-3">
  <Label className="text-sm font-medium">Личные шаблоны</Label>
  <p className="text-xs text-muted-foreground">
    Дополнительные бланки сверх тех, что есть у проекта
  </p>
  <div className="flex flex-wrap gap-2">
    {AVAILABLE_TEMPLATES.map((tpl) => {
      // Шаблон доступен через проект?
      const fromProject = member.projects
        ?.flatMap(p => p.templates ?? [])
        .includes(tpl.key) ?? false;
      // Выдан лично?
      const isPersonal = member.templates?.includes(tpl.key) ?? false;

      return (
        <button
          key={tpl.key}
          type="button"
          disabled={fromProject}
          title={fromProject ? "Уже доступен через проект" : ""}
          onClick={() => {
            if (fromProject) return;
            const next = isPersonal
              ? (member.templates ?? []).filter(t => t !== tpl.key)
              : [...(member.templates ?? []), tpl.key];
            store.updateMemberTemplates(member.id, next)
              .then(() => queryClient.invalidateQueries({ queryKey: ["team"] }));
          }}
          className={cn(
            "px-3 py-1.5 rounded-lg text-sm border transition-colors",
            fromProject
              ? "bg-muted text-muted-foreground border-muted cursor-default opacity-60"
              : isPersonal
                ? "bg-primary text-primary-foreground border-primary"
                : "bg-background border-border hover:bg-muted"
          )}
        >
          {tpl.label}
          {fromProject && " (проект)"}
        </button>
      );
    })}
  </div>
</div>
```

---

## ЧАСТЬ 6 — TELEGRAM БОТ

### 6.1 States (`app/services/bot/states.py`)

Добавить новый StatesGroup в конец файла:

```python
class BlankWizard(StatesGroup):
    template_selection = State()  # выбор из нескольких шаблонов
    filling_method     = State()  # в боте или WebApp
    purpose            = State()  # цель расхода
    item_name          = State()
    item_qty           = State()
    item_amount        = State()
    item_currency      = State()
    confirm            = State()
```

### 6.2 Keyboards (`app/services/bot/keyboards.py`)

**Изменение 1** — В `get_main_kb` добавить две новые кнопки:

```python
def get_main_kb(is_ceo: bool = False):
    b = ReplyKeyboardBuilder()
    if is_ceo:
        b.button(text="🔄 Проверить новые заявки")
    else:
        b.button(text="Создать инвестицию (в боте)")
        b.button(text="Оформить возврат (в боте)")
        b.button(text="Создать инвестицию (Web-App)")
        b.button(text="Создать возврат (Web-App)")
        b.button(text="📋 Заполнить бланк")          # ← ДОБАВИТЬ
        b.button(text="🧾 Заявление на возврат")     # ← ДОБАВИТЬ
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)
```

**Изменение 2** — Добавить новые функции клавиатур:

```python
TEMPLATE_LABELS = {
    "land":       "📋 LAND",
    "drujba":     "📋 ЛС (Дружба)",
    "management": "📋 Management",
    "school":     "📋 School",
}

def get_template_select_kb(available: list) -> types.ReplyKeyboardMarkup:
    """Кнопки только с доступными шаблонами + Назад."""
    b = ReplyKeyboardBuilder()
    for key in available:
        b.button(text=TEMPLATE_LABELS.get(key, key))
    b.button(text=_BACK)
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

def get_fill_method_kb() -> types.ReplyKeyboardMarkup:
    """Выбор способа заполнения: бот или WebApp."""
    b = ReplyKeyboardBuilder()
    b.button(text="📱 Заполнить в боте")
    b.button(text="🌐 Открыть Web форму")
    b.button(text=_BACK)
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)
```

### 6.3 Новый файл `app/services/bot/handlers/blank_wizard.py`

Создать новый файл целиком:

```python
"""
blank_wizard.py
Воронка заполнения бланков служебных записок.
Шаблон определяется автоматически по проекту/личным правам пользователя.
"""
import os
import datetime
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from app.core import database
from app.db import models
from ..states import BlankWizard
from ..keyboards import (
    get_main_kb, get_fill_method_kb, get_template_select_kb,
    get_back_kb, get_currency_kb, get_confirm_kb,
    TEMPLATE_LABELS,
)
from ..utils import _BACK

router = Router()

# Обратный маппинг: "📋 LAND" → "land"
LABEL_TO_KEY = {v: k for k, v in TEMPLATE_LABELS.items()}
ALL_KEYS = list(TEMPLATE_LABELS.keys())
MAX_ITEMS = 50


# ── Вспомогательная функция ──────────────────────────────────────────────────

def get_user_templates(user: models.TeamMember) -> list:
    """
    Собирает доступные шаблоны пользователя из двух источников:
    1. templates каждого привязанного проекта
    2. личные templates сотрудника (TeamMember.templates)
    Возвращает список без дубликатов.
    """
    result = []
    for project in (user.projects or []):
        for tpl in (project.templates or []):
            if tpl not in result:
                result.append(tpl)
    for tpl in (user.templates or []):
        if tpl not in result:
            result.append(tpl)
    return result


# ── Точка входа: кнопка "📋 Заполнить бланк" ────────────────────────────────

@router.message(F.text == "📋 Заполнить бланк")
async def start_blank_wizard(message: types.Message, state: FSMContext):
    await state.clear()

    with next(database.get_db()) as db:
        user = db.query(models.TeamMember).filter(
            models.TeamMember.telegram_chat_id == message.from_user.id
        ).first()
        if not user:
            await message.answer("Сначала авторизуйтесь: /start")
            return
        available = get_user_templates(user)

    # Сценарий 0: шаблоны не настроены → показать все с предупреждением
    if not available:
        available = ALL_KEYS
        await message.answer(
            "⚠️ Для вашего проекта шаблоны не настроены.\n"
            "Выберите шаблон из всех доступных:",
            reply_markup=get_template_select_kb(available)
        )
        await state.update_data(items=[])
        await state.set_state(BlankWizard.template_selection)
        return

    # Сценарий 1: один шаблон → сразу к выбору способа
    if len(available) == 1:
        key = available[0]
        await state.update_data(template=key, items=[])
        await state.set_state(BlankWizard.filling_method)
        await message.answer(
            f"Бланк: *{TEMPLATE_LABELS[key]}*\nКак хотите заполнить?",
            parse_mode="Markdown",
            reply_markup=get_fill_method_kb()
        )
        return

    # Сценарий 2: несколько шаблонов → выбор кнопками
    await state.update_data(items=[])
    await state.set_state(BlankWizard.template_selection)
    await message.answer(
        "Выберите шаблон:",
        reply_markup=get_template_select_kb(available)
    )


# ── Выбор шаблона (сценарии 0 и 2) ──────────────────────────────────────────

@router.message(BlankWizard.template_selection)
async def handle_template_selection(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.clear()
        await message.answer("Главное меню", reply_markup=get_main_kb())
        return

    key = LABEL_TO_KEY.get(message.text)
    if not key:
        await message.answer("Выберите шаблон из кнопок")
        return

    await state.update_data(template=key)
    await state.set_state(BlankWizard.filling_method)
    await message.answer(
        f"Бланк: *{TEMPLATE_LABELS[key]}*\nКак хотите заполнить?",
        parse_mode="Markdown",
        reply_markup=get_fill_method_kb()
    )


# ── Выбор способа заполнения ─────────────────────────────────────────────────

@router.message(BlankWizard.filling_method)
async def handle_filling_method(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        # Вернуться к выбору шаблона или в главное меню
        data = await state.get_data()
        available = data.get("available_templates", ALL_KEYS)
        if len(available) <= 1:
            await state.clear()
            await message.answer("Главное меню", reply_markup=get_main_kb())
        else:
            await state.set_state(BlankWizard.template_selection)
            await message.answer("Выберите шаблон:",
                                 reply_markup=get_template_select_kb(available))
        return

    if message.text == "🌐 Открыть Web форму":
        data = await state.get_data()
        template = data.get("template")
        base_url = os.getenv("WEB_FORM_BASE_URL", "https://finance.thompson.uz")
        url = f"{base_url}/blank?type={template}&chat_id={message.from_user.id}"
        b = ReplyKeyboardBuilder()
        b.button(text="Открыть форму", web_app=types.WebAppInfo(url=url))
        b.button(text=_BACK)
        b.adjust(1)
        await message.answer(
            f"Откройте форму бланка {TEMPLATE_LABELS.get(template, template)}:",
            reply_markup=b.as_markup(resize_keyboard=True)
        )
        return

    if message.text == "📱 Заполнить в боте":
        await state.set_state(BlankWizard.purpose)
        await message.answer("Введите цель расхода:", reply_markup=get_back_kb())


# ── Воронка ввода данных ──────────────────────────────────────────────────────

@router.message(BlankWizard.purpose)
async def handle_purpose(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(BlankWizard.filling_method)
        await message.answer("Как хотите заполнить?", reply_markup=get_fill_method_kb())
        return
    await state.update_data(purpose=message.text)
    await state.set_state(BlankWizard.item_name)
    await message.answer("Позиция 1. Наименование:", reply_markup=get_back_kb())


@router.message(BlankWizard.item_name)
async def handle_item_name(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(BlankWizard.purpose)
        await message.answer("Введите цель расхода:", reply_markup=get_back_kb())
        return
    await state.update_data(current_item_name=message.text)
    await state.set_state(BlankWizard.item_qty)
    await message.answer("Количество:", reply_markup=get_back_kb())


@router.message(BlankWizard.item_qty)
async def handle_item_qty(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(BlankWizard.item_name)
        data = await state.get_data()
        n = len(data.get("items", [])) + 1
        await message.answer(f"Позиция {n}. Наименование:", reply_markup=get_back_kb())
        return
    try:
        qty = float(message.text.replace(",", "."))
        await state.update_data(current_item_qty=qty)
        await state.set_state(BlankWizard.item_amount)
        await message.answer("Сумма за 1 ед.:", reply_markup=get_back_kb())
    except ValueError:
        await message.answer("Введите число")


@router.message(BlankWizard.item_amount)
async def handle_item_amount(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(BlankWizard.item_qty)
        await message.answer("Количество:", reply_markup=get_back_kb())
        return
    try:
        amount = float(message.text.replace(",", ".").replace(" ", ""))
        await state.update_data(current_item_amount=amount)
        await state.set_state(BlankWizard.item_currency)
        await message.answer("Валюта:", reply_markup=get_currency_kb())
    except ValueError:
        await message.answer("Введите число")


@router.message(BlankWizard.item_currency)
async def handle_item_currency(message: types.Message, state: FSMContext):
    if message.text == _BACK:
        await state.set_state(BlankWizard.item_amount)
        await message.answer("Сумма за 1 ед.:", reply_markup=get_back_kb())
        return
    if message.text not in ("UZS", "USD"):
        await message.answer("Выберите UZS или USD")
        return

    data = await state.get_data()
    item = {
        "name":     data["current_item_name"],
        "qty":      data["current_item_qty"],
        "amount":   data["current_item_amount"],
        "currency": message.text,
    }
    items = data.get("items", [])
    items.append(item)
    await state.update_data(items=items)

    if len(items) >= MAX_ITEMS:
        await _show_summary(message, state)
    else:
        await state.set_state(BlankWizard.confirm)
        await message.answer(
            f"✅ Позиция {len(items)} добавлена. Добавить ещё?",
            reply_markup=get_confirm_kb()
        )


@router.message(BlankWizard.confirm)
async def handle_confirm(message: types.Message, state: FSMContext):
    if message.text == "Добавить ещё позицию":
        data = await state.get_data()
        n = len(data.get("items", [])) + 1
        await state.set_state(BlankWizard.item_name)
        await message.answer(f"Позиция {n}. Наименование:", reply_markup=get_back_kb())
    elif message.text == "Готово":
        await _show_summary(message, state)
    elif message.text == _BACK:
        data = await state.get_data()
        items = data.get("items", [])
        if items:
            items.pop()
            await state.update_data(items=items)
        await state.set_state(BlankWizard.item_currency)
        await message.answer("Валюта:", reply_markup=get_currency_kb())


async def _show_summary(message: types.Message, state: FSMContext):
    data = await state.get_data()
    items = data.get("items", [])
    total = sum(i["qty"] * i["amount"] for i in items)
    currency = items[0]["currency"] if items else "UZS"

    template_key = data.get("template", "")
    lines = "\n".join(
        f"  {i+1}. {item['name']} — {item['qty']} шт. × {item['amount']:,} {item['currency']}"
        for i, item in enumerate(items)
    )
    text = (
        f"📋 *{TEMPLATE_LABELS.get(template_key, template_key)}*\n"
        f"🎯 Цель: {data.get('purpose', '')}\n\n"
        f"📦 Позиции:\n{lines}\n\n"
        f"💰 Итого: *{total:,} {currency}*"
    )
    await state.update_data(total_amount=total, currency=currency)

    b = ReplyKeyboardBuilder()
    b.button(text="📥 Скачать бланк")
    b.button(text=_BACK)
    b.adjust(1)
    await message.answer(text, parse_mode="Markdown", reply_markup=b.as_markup(resize_keyboard=True))


@router.message(F.text == "📥 Скачать бланк", BlankWizard.confirm)
async def download_blank(message: types.Message, state: FSMContext):
    data = await state.get_data()

    with next(database.get_db()) as db:
        user = db.query(models.TeamMember).filter(
            models.TeamMember.telegram_chat_id == message.from_user.id
        ).first()
        if not user:
            await message.answer("Пользователь не найден")
            return

        template_key = data.get("template", "")
        template_files = {
            "land":       "LAND.docx",
            "drujba":     "Drujba.docx",
            "management": "Management.docx",
            "school":     "School.docx",
        }
        filename = template_files.get(template_key)
        if not filename:
            await message.answer("Неизвестный шаблон")
            return

        templates_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "docx", "templates"
        )
        template_path = os.path.join(templates_dir, filename)

        full_name = f"{user.last_name} {user.first_name}"
        parts = full_name.split()
        short_name = f"{parts[0]} {parts[1][0]}." if len(parts) >= 2 else full_name

        payload = {
            "template":          template_key,
            "sender_name":       full_name,
            "sender_name_short": short_name,
            "sender_position":   user.position or "Сотрудник",
            "purpose":           data.get("purpose", ""),
            "items":             data.get("items", []),
            "total_amount":      data.get("total_amount", 0),
            "currency":          data.get("currency", "UZS"),
            "date":              datetime.datetime.now().strftime("%d.%m.%Y"),
        }

        try:
            from app.services.docx.generator import generate_docx
            stream = generate_docx(template_path, payload)
            fname = f"blank_{template_key}_{datetime.datetime.now().strftime('%d%m%Y')}.docx"
            await message.answer_document(
                types.BufferedInputFile(stream.getvalue(), filename=fname)
            )
            await state.clear()
            await message.answer("✅ Готово!", reply_markup=get_main_kb())
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
```

### 6.4 Регистрация роутера (`app/services/bot/handlers/__init__.py`)

```python
from aiogram import Router
from . import auth, expense_wizard, refund_wizard, decisions, documents, ceo
from . import blank_wizard    # ← ДОБАВИТЬ

def register_all_handlers(dp):
    router = Router()
    router.include_router(auth.router)
    router.include_router(expense_wizard.router)
    router.include_router(refund_wizard.router)
    router.include_router(decisions.router)
    router.include_router(documents.router)
    router.include_router(ceo.router)
    router.include_router(blank_wizard.router)    # ← ДОБАВИТЬ
    dp.include_router(router)
```

---

## Итоговый список файлов для изменения

| Файл | Действие |
|---|---|
| `app/db/models.py` | Добавить `templates` в `Project` и `TeamMember` |
| `alembic/versions/` | Новая миграция с двумя `add_column` |
| `app/db/schemas.py` | `templates` в `ProjectBase` и `TeamMemberBase`, две новые схемы Update |
| `app/db/crud.py` | Сохранять `templates` при `create_project` |
| `app/api/projects.py` | Новый `PATCH /{id}/templates` |
| `app/api/team.py` | Новый `PATCH /{id}/templates` |
| `frontend/src/lib/types.ts` | `templates: string[]` в обоих интерфейсах + константа |
| `frontend/src/lib/store.ts` | Два новых метода `updateProjectTemplates`, `updateMemberTemplates` |
| `frontend/src/pages/Projects.tsx` | Мультиселект в форме, отображение в карточке |
| `frontend/src/pages/Team.tsx` | Секция личных шаблонов с серыми кнопками проектных |
| `app/services/bot/states.py` | Добавить `BlankWizard` |
| `app/services/bot/keyboards.py` | Две новые кнопки в `get_main_kb`, две новые функции |
| `app/services/bot/handlers/blank_wizard.py` | **Новый файл** — полная воронка |
| `app/services/bot/handlers/__init__.py` | Зарегистрировать `blank_wizard.router` |