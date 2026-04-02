import React from "react";
import { ExternalLink, CheckSquare, Settings, FileText, Download, Activity, Key, Users } from "lucide-react";

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
          <a href="#roles" className="hover:text-foreground hover:bg-muted/50 px-3 py-2 rounded-md transition-colors leading-tight">
            2. Роли и уровни доступа
          </a>
          <a href="#automation" className="hover:text-foreground hover:bg-muted/50 px-3 py-2 rounded-md transition-colors leading-tight">
            3. Автоматизация документов
          </a>
          <a href="#reports" className="hover:text-foreground hover:bg-muted/50 px-3 py-2 rounded-md transition-colors leading-tight">
            4. Выгрузка отчетов и фильтры
          </a>
          <a href="#flow" className="hover:text-foreground hover:bg-muted/50 px-3 py-2 rounded-md transition-colors leading-tight">
            5. Путь заявки
          </a>
          <a href="#statuses" className="hover:text-foreground hover:bg-muted/50 px-3 py-2 rounded-md transition-colors leading-tight">
            6. Статусы: правила и переходы
          </a>
          <a href="#best-practices" className="hover:text-foreground hover:bg-muted/50 px-3 py-2 rounded-md transition-colors leading-tight">
            7. Золотые правила бухгалтера
          </a>
          <a href="#developers" className="hover:text-foreground hover:bg-muted/50 px-3 py-2 rounded-md transition-colors leading-tight">
            8. Технический раздел
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
            Официальная инструкция по работе с системой заявок Thompson Finance (Safina). Разработано для финансистов, руководителей и инициаторов.
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
                <li><strong>Контроль расходов:</strong> Многоуровневое согласование, исключающее ошибки (Сотрудник → На рассмотрении → CFO → CEO).</li>
                <li><strong>Управление возвратами:</strong> Визуальная Канбан-доска для отслеживания движения денег клиентов на каждом этапе.</li>
                <li><strong>Авто-документы:</strong> Автоматическая генерация файлов Word/Excel (заявления, сметы) на основе введённых данных.</li>
              </ul>
              <h3 className="font-semibold text-lg mt-6 mb-2">Архитектура простыми словами</h3>
              <p>Система состоит из единой защищенной <strong>Базы данных</strong>, интегрированной с двумя интерфейсами: Telegram-ботом (для быстрой подачи заявок «в полях») и Веб-панелью (для контроля, утверждения и детального анализа).</p>
            </div>
          </section>

          {/* Section 2 */}
          <section id="roles" className="scroll-mt-32 space-y-6">
            <h2 className="text-2xl font-bold text-foreground border-b pb-2">
              2. Роли и уровни доступа
            </h2>
            <div className="text-foreground/80 leading-relaxed overflow-hidden border rounded-lg">
              <table className="w-full text-left text-sm">
                <thead className="bg-muted text-muted-foreground">
                  <tr>
                    <th className="px-5 py-3 font-medium">Роль</th>
                    <th className="px-5 py-3 font-medium">Пример должности</th>
                    <th className="px-5 py-3 font-medium">Зона ответственности</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  <tr className="hover:bg-muted/30">
                    <td className="px-5 py-4 font-semibold">Инициатор</td>
                    <td className="px-5 py-4 text-muted-foreground">Сотрудник филиала</td>
                    <td className="px-5 py-4">Создает заявки на расходы или возвраты через бот. Видит только свои заявки.</td>
                  </tr>
                  <tr className="hover:bg-muted/30">
                    <td className="px-5 py-4 font-semibold">Финансист (CFO)</td>
                    <td className="px-5 py-4 text-muted-foreground">Главный бухгалтер</td>
                    <td className="px-5 py-4">Осуществляет первый этап проверки: контроль лимитов, ведение учета, выгрузка сводных отчетов.</td>
                  </tr>
                  <tr className="hover:bg-muted/30">
                    <td className="px-5 py-4 font-semibold">Директор (Admin/CEO)</td>
                    <td className="px-5 py-4 text-muted-foreground">Руководитель сети</td>
                    <td className="px-5 py-4">Финальное согласование выплат. Имеет полный доступ ко всем настройкам, правам сотрудников и аналитике.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          {/* Section 3 */}
          <section id="automation" className="scroll-mt-32 space-y-6">
            <h2 className="text-2xl font-bold text-foreground border-b pb-2">
              3. Автоматизация документов
            </h2>
            <div className="text-foreground/80 leading-relaxed space-y-4">
              <h3 className="font-semibold text-lg">Сбор данных (Бот)</h3>
              <p>Telegram-бот опрашивает сотрудника шаг за шагом. Как только ввод всей необходимой информации завершён, данные мгновенно отправляются на сервер, исключая потерю сообщений.</p>
              
              <h3 className="font-semibold text-lg mt-4">Генерация файлов (Веб-панель)</h3>
              <p>Система автоматически берёт готовые утверждённые шаблоны Word и заполняет их введенными данными. Готовые документы (.docx с подставленными фамилиями и суммами) можно скачать двумя кликами прямо из интерфейса заявки.</p>
            </div>
          </section>

          {/* Section 4 */}
          <section id="reports" className="scroll-mt-32 space-y-6">
            <h2 className="text-2xl font-bold text-foreground border-b pb-2">
              4. Выгрузка отчетов и фильтры
            </h2>
            <div className="text-foreground/80 leading-relaxed space-y-4">
              <p>Функция <strong>«Скачать расходы»</strong> собирает все заявки, соответствующие текущим фильтрам интерфейса.</p>
              
              <div className="bg-muted/30 border rounded-lg p-5 mt-4 space-y-3">
                <h4 className="font-semibold">Правила работы выгрузки (Excel/CSV):</h4>
                <ul className="list-disc pl-5 space-y-1 text-sm">
                  <li>Без фильтров: скачивается вся база за всё время (возможно ограничение до 5000 строк).</li>
                  <li>Детализация: каждая затрата (позиция, количество) идёт отдельной строкой.</li>
                  <li>Курсы валют: иностранные валюты автоматически конвертируются в UZS по курсу на день подачи заявки.</li>
                  <li>Фильтрация статусов: по умолчанию скачиваются только <em>финальные</em> статусы (Одобрено, Подтверждено), чтобы не искажать текущий баланс ожидаемыми выплатами. Для полной выгрузки выберите параметр «Все статусы».</li>
                </ul>
              </div>
            </div>
          </section>

          {/* Section 5 */}
          <section id="flow" className="scroll-mt-32 space-y-6">
            <h2 className="text-2xl font-bold text-foreground border-b pb-2">
              5. Путь заявки (от создания до оплаты)
            </h2>
            <div className="text-foreground/80 leading-relaxed">
              <div className="space-y-6 pl-2">
                <div className="flex gap-4 relative">
                  <div className="w-8 h-8 shrink-0 bg-primary/10 text-primary border border-primary/20 rounded-full flex items-center justify-center font-bold font-mono">1</div>
                  <div className="pb-6">
                    <h4 className="font-bold text-foreground">Подача</h4>
                    <p className="text-sm mt-1 text-muted-foreground">Инициатор заполняет все поля в интерфейсе бота или на сайте. Заявка создается в статусе «Запрос».</p>
                  </div>
                </div>
                <div className="flex gap-4 relative">
                  <div className="w-8 h-8 shrink-0 bg-primary/10 text-primary border border-primary/20 rounded-full flex items-center justify-center font-bold font-mono">2</div>
                  <div className="pb-6">
                    <h4 className="font-bold text-foreground">Проверка бухгалтерией</h4>
                    <p className="text-sm mt-1 text-muted-foreground">Модератор или CFO переводит заявку «На рассмотрение». Запрашиваются уточнения, если требуется.</p>
                  </div>
                </div>
                <div className="flex gap-4 relative">
                  <div className="w-8 h-8 shrink-0 bg-primary/10 text-primary border border-primary/20 rounded-full flex items-center justify-center font-bold font-mono">3</div>
                  <div className="pb-6">
                    <h4 className="font-bold text-foreground">Согласование (CFO → CEO)</h4>
                    <p className="text-sm mt-1 text-muted-foreground">Последовательное утверждение финансовым и генеральным директором. Одобряется общая смета и её целесообразность.</p>
                  </div>
                </div>
                <div className="flex gap-4 relative">
                  <div className="w-8 h-8 shrink-0 bg-primary/10 text-primary border border-primary/20 rounded-full flex items-center justify-center font-bold font-mono">4</div>
                  <div>
                    <h4 className="font-bold text-foreground">Выплата и Архивирование</h4>
                    <p className="text-sm mt-1 text-muted-foreground">Фактическая выплата средств закрепляется статусом «Подтверждено», после чего заявка может быть убрана в Архив.</p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Section 6 */}
          <section id="statuses" className="scroll-mt-32 space-y-6">
            <h2 className="text-2xl font-bold text-foreground border-b pb-2">
              6. Статусы: правила и переходы
            </h2>
            <div className="text-foreground/80 leading-relaxed space-y-6">
              <p>В системе реализована строгая конечная машина состояний. Запрещается переводить заявки в произвольные статусы, нарушающие цепочку согласований.</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border rounded-lg p-5">
                  <h4 className="font-bold border-b pb-2 mb-3">Особые статусы</h4>
                  <ul className="space-y-4 text-sm">
                    <li>
                      <strong className="block mb-1 text-foreground">Архивировано (archived)</strong>
                      <span className="text-muted-foreground">Скрытие заявки с активных досок. Доступно только из финальных статусов: <em>Подтверждено</em> или <em>Отклонено</em>.</span>
                    </li>
                    <li>
                      <strong className="block mb-1 text-foreground">Возврат на доработку (revision)</strong>
                      <span className="text-muted-foreground">Возможен возврат из статусов проверки и согласований (вплоть до CEO). Требует <strong>обязательного комментария</strong> с указанием ошибки.</span>
                    </li>
                  </ul>
                </div>

                <div className="border rounded-lg p-5 bg-muted/20">
                  <h4 className="font-bold border-b pb-2 mb-3">Хронология состояний</h4>
                  <ol className="list-decimal pl-5 space-y-2 text-sm text-muted-foreground">
                    <li><strong className="text-foreground">Запрос (request)</strong> — новая заявка.</li>
                    <li><strong className="text-foreground">На рассмотрении (review)</strong> — заявка взята в работу CFO.</li>
                    <li><strong className="text-foreground">Согласование CFO (pending_senior)</strong> — запрос на утверждение финансовым директором.</li>
                    <li><strong className="text-foreground">Согласование CEO (pending_ceo)</strong> — отправлено генеральному директору.</li>
                    <li><strong className="text-foreground">Подтверждено (confirmed)</strong> / <strong>Отклонено (declined)</strong> — итог.</li>
                  </ol>
                </div>
              </div>
            </div>
          </section>

          {/* Section 7 */}
          <section id="best-practices" className="scroll-mt-32 space-y-6">
            <h2 className="text-2xl font-bold text-foreground border-b pb-2">
              7. Золотые правила работы (Best Practices)
            </h2>
            <div className="text-foreground/80 leading-relaxed grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="border border-primary/10 bg-primary/5 rounded-lg p-5 space-y-2">
                <h4 className="font-bold text-foreground">Утренний клиринг</h4>
                <p className="text-sm">Начинайте рабочий день с вкладки заявок. Своевременные переводы заявок в статус «На рассмотрении» успокаивают инициаторов и снижают количество звонков с вопросами.</p>
              </div>
              <div className="border border-primary/10 bg-primary/5 rounded-lg p-5 space-y-2">
                <h4 className="font-bold text-foreground">Обязательные комментарии</h4>
                <p className="text-sm">При отклонении (Declined) или возврате на доработку (Revision) пишите развернутую причину. «История статусов» сохраняется навсегда: через год восстановить контекст без комментария будет невозможно.</p>
              </div>
              <div className="border border-primary/10 bg-primary/5 rounded-lg p-5 space-y-2">
                <h4 className="font-bold text-foreground">Внутренний контекст</h4>
                <p className="text-sm">Поле «Внутренний контекст» доступно только для администрации. Используйте его для служебных пометок о проекте или клиенте.</p>
              </div>
              <div className="border border-primary/10 bg-primary/5 rounded-lg p-5 space-y-2">
                <h4 className="font-bold text-foreground">Контроль реквизитов</h4>
                <p className="text-sm">Для возвратов (Blank Refund). Всегда сверяйте фамилии и номера карт. Финансовая ошибка на этапе Подтверждения необратима.</p>
              </div>
            </div>
          </section>

          {/* Section 8 */}
          <section id="developers" className="scroll-mt-32 space-y-6">
            <h2 className="text-2xl font-bold text-foreground border-b pb-2">
              8. Раздел для разработчиков
            </h2>
            <div className="text-foreground/80 leading-relaxed bg-muted/30 p-6 rounded-lg border">
              <p className="mb-4">Техническая архитектура, скрипты развертывания баз данных, конфигурации CI/CD и API документация вынесены в корпоративную Wiki.</p>
              <a 
                href="https://deepwiki.com/axatsa/Safina-bot/1-overview" 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 font-semibold text-primary hover:text-primary/80 transition-colors"
              >
                Перейти в DeepWiki <ExternalLink size={16} />
              </a>
            </div>
          </section>
        </div>

      </main>
    </div>
  );
};

export default FAQ;
