import React from "react";
import { ExternalLink, CheckSquare, Settings, FileText, Download, Activity, Key, Users, FolderKanban, Building2, ShieldCheck, Plus, Info } from "lucide-react";

const FAQ = () => {
  return (
    <div className="max-w-7xl mx-auto flex flex-col md:flex-row gap-10 p-6 lg:p-12 pb-24 animate-fade-in relative items-start">
      {/* Table of Contents - Sidebar */}
      <aside className="w-full md:w-72 shrink-0 md:sticky md:top-24 bg-card border rounded-xl shadow-sm p-6">
        <h2 className="text-lg font-bold border-b pb-4 mb-4 text-foreground tracking-tight">
          Содержание
        </h2>
        <nav className="flex flex-col space-y-1 text-sm font-medium text-muted-foreground">
          <a href="#purpose" className="hover:text-foreground hover:bg-muted/50 px-3 py-2 rounded-md transition-colors leading-tight">
            1. Назначение системы
          </a>
          <a href="#projects" className="hover:text-foreground hover:bg-muted/50 px-3 py-2 rounded-md transition-colors leading-tight font-bold text-primary">
            2. Типы проектов и филиалы
          </a>
          <a href="#roles" className="hover:text-foreground hover:bg-muted/50 px-3 py-2 rounded-md transition-colors leading-tight">
            3. Роли и уровни доступа
          </a>
          <a href="#automation" className="hover:text-foreground hover:bg-muted/50 px-3 py-2 rounded-md transition-colors leading-tight">
            4. Автоматизация документов
          </a>
          <a href="#reports" className="hover:text-foreground hover:bg-muted/50 px-3 py-2 rounded-md transition-colors leading-tight">
            5. Выгрузка отчетов и фильтры
          </a>
          <a href="#flow" className="hover:text-foreground hover:bg-muted/50 px-3 py-2 rounded-md transition-colors leading-tight">
            6. Путь заявки
          </a>
          <a href="#statuses" className="hover:text-foreground hover:bg-muted/50 px-3 py-2 rounded-md transition-colors leading-tight">
            7. Статусы: правила и переходы
          </a>
          <a href="#best-practices" className="hover:text-foreground hover:bg-muted/50 px-3 py-2 rounded-md transition-colors leading-tight">
            8. Золотые правила работы
          </a>
          <a href="#developers" className="hover:text-foreground hover:bg-muted/50 px-3 py-2 rounded-md transition-colors leading-tight">
            9. Технический раздел
          </a>
          <a href="#team-access" className="hover:text-foreground hover:bg-muted/50 px-3 py-2 rounded-md transition-colors leading-tight font-semibold text-primary">
            10. Управление командой
          </a>
          <a href="#faq-users" className="hover:text-foreground hover:bg-muted/50 px-3 py-2 rounded-md transition-colors leading-tight font-semibold">
            11. Частые вопросы (FAQ)
          </a>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 min-w-0">
        <div className="mb-14 border-b pb-10">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground mb-4">
            Руководство пользователя
          </h1>
          <p className="text-xl text-muted-foreground leading-relaxed">
            Официальная инструкция по работе с системой заявок Thompson Finance (Safina). Разработано для финансистов, руководителей и сотрудников.
          </p>
        </div>

        <div className="space-y-16">
          {/* Section 1 */}
          <section id="purpose" className="scroll-mt-32 space-y-6">
            <h2 className="text-2xl font-bold text-foreground border-b pb-2">
              1. Назначение системы
            </h2>
            <div className="text-foreground/80 leading-relaxed space-y-4">
              <p>Платформа создана для замены бумажной волокиты и хаоса в рабочих чатах. Система стандартизирует и автоматизирует три ключевых направления:</p>
              <ul className="list-disc pl-6 space-y-2 mt-2">
                <li><strong>Контроль расходов:</strong> Многоуровневое согласование (Сотрудник → Бухгалтер → Финансовый директор → CEO).</li>
                <li><strong>Управление возвратами:</strong> Отслеживание каждой операции возврата денег клиенту на Канбан-доске.</li>
                <li><strong>Авто-документы:</strong> Автоматическая генерация файлов Word/Excel (заявления, сметы) на основе ваших данных.</li>
              </ul>
            </div>
          </section>

          {/* Section 2 */}
          <section id="projects" className="scroll-mt-32 space-y-6">
            <h2 className="text-2xl font-bold text-foreground border-b pb-2">
              2. Типы проектов и филиалы (Объяснение структуры)
            </h2>
            <div className="text-foreground/80 leading-relaxed space-y-4">
              <p>В нашей системе все бизнесы делятся на два типа. Это помогает системе понимать, как считать деньги и какие документы готовить.</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                <div className="border rounded-xl p-6 bg-blue-500/5 border-blue-500/20">
                  <h3 className="font-bold text-lg text-foreground mb-3 flex items-center gap-2">
                    <CheckSquare className="text-blue-500 w-5 h-5" /> Стартап (Startup)
                  </h3>
                  <p className="text-sm">Это простой проект, где все работают как одна единая команда. У него нет деления на города или подотделы.</p>
                  <p className="text-xs text-muted-foreground mt-3 italic">Пример: Начиная новый проект, мы ведем его как Стартап, пока он не вырастет.</p>
                </div>

                <div className="border rounded-xl p-6 bg-amber-500/5 border-amber-500/20">
                  <h3 className="font-bold text-lg text-foreground mb-3 flex items-center gap-2">
                    <Users className="text-amber-500 w-5 h-5" /> Корпоративный проект
                  </h3>
                  <p className="text-sm">Это большая организация, у которой есть много <strong>филиалов</strong> (локаций, школ, офисов).</p>
                  <p className="text-xs text-muted-foreground mt-3 italic">Пример: Thompson School, где много школ в разных районах.</p>
                </div>
              </div>

              <div className="bg-muted/30 p-6 rounded-xl border space-y-4 shadow-sm mt-4">
                <h3 className="font-bold text-lg">Что такое филиалы и зачем они нам?</h3>
                <p className="text-sm">Филиалы — это как разные кошельки в одной сумке. Мы используем их, чтобы:</p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-1">
                    <span className="font-bold text-foreground text-sm">Считать честно</span>
                    <p className="text-xs text-muted-foreground">Мы точно видим, сколько денег тратит каждая локация отдельно.</p>
                  </div>
                  <div className="space-y-1">
                    <span className="font-bold text-foreground text-sm">Свой порядок</span>
                    <p className="text-xs text-muted-foreground">У каждого филиала своя очередь заявок (например, HAYAT-1, HAYAT-2).</p>
                  </div>
                  <div className="space-y-1">
                    <span className="font-bold text-foreground text-sm">Привязка людей</span>
                    <p className="text-xs text-muted-foreground">Сотрудник привязан к своему филиалу и подает заявки именно по нему.</p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Section 3 */}
          <section id="roles" className="scroll-mt-32 space-y-6">
            <h2 className="text-2xl font-bold text-foreground border-b pb-2">
              3. Роли и уровни доступа
            </h2>
            <div className="text-foreground/80 leading-relaxed overflow-hidden border rounded-lg">
              <table className="w-full text-left text-sm">
                <thead className="bg-muted text-muted-foreground">
                  <tr>
                    <th className="px-5 py-3 font-medium">Роль</th>
                    <th className="px-5 py-3 font-medium">Кто это</th>
                    <th className="px-5 py-3 font-medium">Что делает</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  <tr className="hover:bg-muted/30">
                    <td className="px-5 py-4 font-semibold">Инициатор</td>
                    <td className="px-5 py-4 text-muted-foreground">Сотрудник</td>
                    <td className="px-5 py-4">Подает заявки через Telegram-бот. Видит только свои траты.</td>
                  </tr>
                  <tr className="hover:bg-muted/30">
                    <td className="px-5 py-4 font-semibold">Финансист (CFO)</td>
                    <td className="px-5 py-4 text-muted-foreground">Бухгалтер</td>
                    <td className="px-5 py-4">Проверяет чеки, следит за бюджетом, выгружает отчеты для налоговой.</td>
                  </tr>
                  <tr className="hover:bg-muted/30">
                    <td className="px-5 py-4 font-semibold">Директор (CEO)</td>
                    <td className="px-5 py-4 text-muted-foreground">Руководитель</td>
                    <td className="px-5 py-4">Финально нажимает «Оплатить». Видит всю аналитику по компании.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          {/* Section 4 */}
          <section id="automation" className="scroll-mt-32 space-y-6">
            <h2 className="text-2xl font-bold text-foreground border-b pb-2">
              4. Автоматизация документов
            </h2>
            <div className="text-foreground/80 leading-relaxed space-y-4">
              <h3 className="font-semibold text-lg">Как это работает?</h3>
              <p>Вам больше не нужно печатать заявления на бумаге и нести их на подпись. Как только вы заполнили данные в боте, система сама формирует нужный документ (Word или Excel) со всеми суммами и именами.</p>
            </div>
          </section>

          {/* Section 5 */}
          <section id="reports" className="scroll-mt-32 space-y-6">
            <h2 className="text-2xl font-bold text-foreground border-b pb-2">
              5. Выгрузка отчетов и фильтры
            </h2>
            <div className="text-foreground/80 leading-relaxed space-y-4">
              <p>Финансисты могут в любой момент скачать Excel-таблицу. Благодаря новой системе филиалов, отчет можно сделать как по всей компании сразу, так и по одной конкретной школе или офису.</p>
            </div>
          </section>

          {/* Section 6 */}
          <section id="flow" className="scroll-mt-32 space-y-6">
            <h2 className="text-2xl font-bold text-foreground border-b pb-2">
              6. Путь заявки (от идеи до денег)
            </h2>
            <div className="space-y-4">
              <div className="border-l-2 border-primary/30 pl-6 space-y-8">
                <div className="relative">
                  <div className="absolute -left-8 top-1 w-4 h-4 rounded-full bg-primary border-4 border-background shadow-sm" />
                  <h4 className="font-bold text-foreground">1. Подача</h4>
                  <p className="text-sm text-muted-foreground">Выбираете филиал и заполняете данные в боте.</p>
                </div>
                <div className="relative">
                  <div className="absolute -left-8 top-1 w-4 h-4 rounded-full bg-muted border-4 border-background shadow-sm" />
                  <h4 className="font-bold text-foreground">2. Проверка</h4>
                  <p className="text-sm text-muted-foreground">Бухгалтер смотрит чек и детали. Если всё ок — отправляет Директору.</p>
                </div>
                <div className="relative">
                  <div className="absolute -left-8 top-1 w-4 h-4 rounded-full bg-muted border-4 border-background shadow-sm" />
                  <h4 className="font-bold text-foreground">3. Согласование</h4>
                  <p className="text-sm text-muted-foreground">Директор одобряет выплату онлайн.</p>
                </div>
                <div className="relative">
                  <div className="absolute -left-8 top-1 w-4 h-4 rounded-full bg-primary w-5 h-5 -left-[34px] -top-0.5 shadow-md flex items-center justify-center"><CheckSquare className="text-white w-3 h-3" /></div>
                  <h4 className="font-bold text-foreground">4. Выплата</h4>
                  <p className="text-sm text-muted-foreground">Деньги переведены! Заявка уходит в архив.</p>
                </div>
              </div>
            </div>
          </section>

          {/* Section 7 */}
          <section id="statuses" className="scroll-mt-32 space-y-6">
            <h2 className="text-2xl font-bold text-foreground border-b pb-2">
              7. Статусы: что они значат
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="border rounded-lg p-5 space-y-3">
                <p><strong>Запрос (Request):</strong> Ваша заявка только создана и ждет очереди.</p>
                <p><strong>На рассмотрении (Review):</strong> Бухгалтер уже занялся вашим вопросом.</p>
                <p><strong>На доработку (Revision):</strong> Есть ошибка. Посмотрите комментарий и исправьте данные.</p>
              </div>
              <div className="border rounded-lg p-5 space-y-3 bg-muted/20">
                <p><strong>Подтверждено (Confirmed):</strong> Самый важный статус. Значит деньги реально выплачены.</p>
                <p><strong>Отклонено (Declined):</strong> В выплате отказано. Читайте причину в карточке заявки.</p>
              </div>
            </div>
          </section>

          {/* Section 8 */}
          <section id="best-practices" className="scroll-mt-32 space-y-6">
            <h2 className="text-2xl font-bold text-foreground border-b pb-2">
              8. Три золотых правила
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center space-y-2">
                <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto text-primary font-bold">1</div>
                <p className="font-bold text-sm">Верный филиал</p>
                <p className="text-xs text-muted-foreground">Всегда проверяйте, для какого офиса просите деньги. Это нельзя исправить потом.</p>
              </div>
              <div className="text-center space-y-2">
                <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto text-primary font-bold">2</div>
                <p className="font-bold text-sm">Четкое фото</p>
                <p className="text-xs text-muted-foreground">Фотографируйте чек так, чтобы были видны все цифры и дата. Размытые фото отклоняют.</p>
              </div>
              <div className="text-center space-y-2">
                <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto text-primary font-bold">3</div>
                <p className="font-bold text-sm">Без дубликатов</p>
                <p className="text-xs text-muted-foreground">Если ошиблись — не шлите вторую заявку. Попросите вернуть старую на доработку.</p>
              </div>
            </div>
          </section>

          {/* Section 9 */}
          <section id="developers" className="scroll-mt-32 space-y-6">
            <h2 className="text-2xl font-bold text-foreground border-b pb-2">
              9. Технический раздел
            </h2>
            <div className="bg-muted/30 p-6 rounded-lg border text-sm">
              <p>Для программистов: архитектура API и документация по базе данных доступны здесь:</p>
              <a href="https://deepwiki.com/axatsa/Safina-bot" className="text-primary font-bold mt-2 block hover:underline">DeepWiki →</a>
            </div>
          </section>

          {/* Section 10 */}
          <section id="team-access" className="scroll-mt-32 space-y-6">
            <h2 className="text-2xl font-bold text-foreground border-b pb-2">
              10. Управление командой и доступами
            </h2>
            <p className="text-foreground/80 leading-relaxed">
              Этот раздел объясняет, как правильно настроить доступы для сотрудника через страницу «Команда». Здесь нет ничего сложного — просто следуйте шагам.
            </p>

            {/* Step-by-step */}
            <div className="space-y-4">
              <h3 className="font-bold text-lg">Как открыть настройки сотрудника</h3>
              <div className="border-l-2 border-primary/30 pl-6 space-y-6">
                <div className="relative">
                  <div className="absolute -left-[29px] top-1 w-4 h-4 rounded-full bg-primary border-4 border-background shadow-sm" />
                  <h4 className="font-bold text-foreground text-sm">1. Перейдите в раздел «Команда»</h4>
                  <p className="text-sm text-muted-foreground mt-1">Нажмите на пункт «Команда» в левом меню. Вы увидите таблицу со всеми сотрудниками.</p>
                </div>
                <div className="relative">
                  <div className="absolute -left-[29px] top-1 w-4 h-4 rounded-full bg-muted border-4 border-background shadow-sm" />
                  <h4 className="font-bold text-foreground text-sm">2. Нажмите иконку карандаша</h4>
                  <p className="text-sm text-muted-foreground mt-1">Найдите нужного сотрудника и нажмите на иконку <strong>✏️</strong> справа в его строке. Откроется окно редактирования.</p>
                </div>
              </div>
            </div>

            {/* 4 blocks explanation */}
            <div className="space-y-4 mt-6">
              <h3 className="font-bold text-lg">Что означает каждый блок в окне редактирования</h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border rounded-xl p-5 space-y-2">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Users className="w-4 h-4 text-primary" />
                    </div>
                    <p className="font-bold text-sm">Блок 1: Личные данные</p>
                  </div>
                  <p className="text-sm text-muted-foreground">Фамилия, имя и должность сотрудника. Эти данные отображаются в таблице команды и в заявках.</p>
                </div>

                <div className="border rounded-xl p-5 space-y-2">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                      <FolderKanban className="w-4 h-4 text-primary" />
                    </div>
                    <p className="font-bold text-sm">Блок 2: Проекты и филиалы</p>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Выберите, к каким <strong>проектам</strong> привязан сотрудник. Если проект корпоративный (например, Thompson School), под ним появятся <strong>филиалы</strong> — выберите конкретные школы/офисы, где работает человек.
                  </p>
                  <div className="bg-amber-50 border border-amber-100 rounded-lg p-3 mt-2">
                    <p className="text-xs text-amber-700">
                      <strong>Важно:</strong> Сотрудник сможет подавать заявки <em>только</em> по тем проектам и филиалам, которые вы здесь выберете.
                    </p>
                  </div>
                </div>

                <div className="border rounded-xl p-5 space-y-2">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                      <FileText className="w-4 h-4 text-primary" />
                    </div>
                    <p className="font-bold text-sm">Блок 3: Доступ к формам</p>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Показывает, какие типы заявок (формы) доступны сотруднику в боте.
                  </p>
                  <div className="space-y-2 mt-2">
                    <div className="flex items-start gap-2">
                      <div className="w-4 h-4 rounded bg-emerald-500 flex items-center justify-center shrink-0 mt-0.5">
                        <ShieldCheck className="w-2.5 h-2.5 text-white" />
                      </div>
                      <p className="text-xs text-muted-foreground">
                        <strong className="text-foreground">Зелёные формы</strong> — добавляются <em>автоматически</em> из выбранных проектов. Их не нужно включать вручную.
                      </p>
                    </div>
                    <div className="flex items-start gap-2">
                      <Plus className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                      <p className="text-xs text-muted-foreground">
                        <strong className="text-foreground">Дополнительные формы</strong> — если сотруднику нужна форма, которая не входит ни в один его проект, включите её здесь вручную.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="border rounded-xl p-5 space-y-2">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Key className="w-4 h-4 text-primary" />
                    </div>
                    <p className="font-bold text-sm">Блок 4: Данные для входа</p>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Логин и пароль для входа в систему. Если хотите сменить пароль — введите новый. Если менять не нужно — оставьте поле пустым, старый пароль сохранится.
                  </p>
                </div>
              </div>
            </div>

            {/* Typical scenarios */}
            <div className="space-y-3 mt-4">
              <h3 className="font-bold text-lg">Типичные ситуации</h3>
              <div className="space-y-3">
                <div className="flex gap-3 p-4 border rounded-xl">
                  <div className="w-6 h-6 rounded-full bg-primary text-white text-xs font-bold flex items-center justify-center shrink-0">?</div>
                  <div>
                    <p className="font-semibold text-sm">Сотрудник пишет, что не видит нужный филиал в боте</p>
                    <p className="text-sm text-muted-foreground mt-1">Откройте его карточку → Блок «Проекты и филиалы» → раскройте нужный проект → поставьте галочку на нужном филиале → нажмите «Сохранить изменения».</p>
                  </div>
                </div>

                <div className="flex gap-3 p-4 border rounded-xl">
                  <div className="w-6 h-6 rounded-full bg-primary text-white text-xs font-bold flex items-center justify-center shrink-0">?</div>
                  <div>
                    <p className="font-semibold text-sm">Нужно дать доступ к «Заявлению на возврат», но проект не настроен</p>
                    <p className="text-sm text-muted-foreground mt-1">Откройте карточку → Блок «Доступ к формам» → в разделе «Добавить отдельно» поставьте галочку «Заявление на возврат» → сохраните.</p>
                  </div>
                </div>

                <div className="flex gap-3 p-4 border rounded-xl">
                  <div className="w-6 h-6 rounded-full bg-primary text-white text-xs font-bold flex items-center justify-center shrink-0">?</div>
                  <div>
                    <p className="font-semibold text-sm">Сотрудник говорит, что обновлённые доступы не работают в боте</p>
                    <p className="text-sm text-muted-foreground mt-1">Попросите его отправить команду <code className="bg-muted px-1 rounded">/start</code> в Telegram-боте. Это перезагружает его профиль с новыми правами.</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex gap-2 p-4 bg-blue-50 border border-blue-100 rounded-xl">
              <Info className="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
              <p className="text-sm text-blue-700 leading-relaxed">
                <strong>Совет:</strong> Всегда нажимайте «Сохранить изменения» после каждого редактирования. Пока кнопка не нажата — ничего не сохранится, даже если вы закроете окно.
              </p>
            </div>
          </section>

          {/* Section 11 */}
          <section id="faq-users" className="scroll-mt-32 space-y-6">
            <h2 className="text-2xl font-bold text-foreground border-b pb-2">
              11. Частые вопросы (FAQ)
            </h2>
            <div className="space-y-4">
              <div className="border rounded-xl p-6 space-y-4">
                <h3 className="font-bold text-lg text-foreground">Как понять номер моей заявки (HAYAT-5, OXR-12)?</h3>
                <p className="text-sm text-foreground/80 leading-relaxed">
                  Это ваш персональный «номер в очереди». <br />
                  Первые буквы — это код вашего филиала (например, <strong>HAYAT</strong> для школы Hayat). <br />
                  Если вы видите <code>HAYAT-REF-3</code>, значит это 3-й по счету <strong>возврат денег клиенту</strong> в вашем филиале. Это помогает бухгалтерии не путать покупки для офиса и возвраты ученикам.
                </p>
              </div>

              <div className="border rounded-xl p-6 space-y-4">
                <h3 className="font-bold text-lg text-foreground">Бот просит выбрать филиал, а моего нет в списке. Что делать?</h3>
                <p className="text-sm text-foreground/80 leading-relaxed">
                  Значит, вы не привязаны к этому филиалу в системе. Напишите бухгалтеру (Сафине), и она добавит вам доступ к нужным локациям через раздел «Команда».
                </p>
              </div>

              <div className="bg-primary/5 border border-primary/20 rounded-xl p-6">
                <h3 className="font-bold text-lg text-foreground mb-2">Важное про валюту!</h3>
                <p className="text-sm text-foreground/80">
                  Подавайте заявку в той валюте, в которой вы реально тратите деньги. Если покупаете бумагу за сумы — пишите UZS. Если платите за иностранный сервис в долларах — выбирайте USD. Система сама пересчитает всё по актуальному курсу.
                </p>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
};

export default FAQ;
