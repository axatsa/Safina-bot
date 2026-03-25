import { 
  HelpCircle, 
  BookOpen, 
  Bot, 
  Monitor, 
  Lightbulb, 
  FileText, 
  BarChart3, 
  DollarSign, 
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Download,
  Calendar,
  Layers,
  Users,
  Workflow,
  Cpu,
  Code2,
  ExternalLink
} from "lucide-react";
import { 
  Accordion, 
  AccordionContent, 
  AccordionItem, 
  AccordionTrigger 
} from "@/components/ui/accordion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const FAQ = () => {
  return (
    <div className="p-6 max-w-5xl mx-auto space-y-12 animate-fade-in pb-20">
      {/* Шапка (Header) */}
      <div className="text-center space-y-4 relative py-10">
        <div className="absolute inset-0 -z-10 bg-gradient-to-b from-primary/5 to-transparent rounded-3xl blur-3xl opacity-50" />
        <div className="inline-flex items-center justify-center p-4 bg-primary/10 rounded-3xl mb-4 backdrop-blur-sm border border-primary/20 shadow-lg animate-float">
          <BookOpen className="w-10 h-10 text-primary" />
        </div>
        <h1 className="text-5xl font-display font-bold text-foreground tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/70">
          База знаний и FAQ
        </h1>
        <p className="text-muted-foreground text-xl max-w-2xl mx-auto leading-relaxed">
          Подробное руководство по системе Thompson Finance / Safina для финансистов и администрации.
        </p>
      </div>

      {/* Обзор системы (Core Systems Overview) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="glass-card overflow-hidden group hover:border-primary/50 transition-all duration-300">
          <CardHeader className="pb-2 space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center group-hover:bg-indigo-500/20 transition-colors">
              <Bot className="w-6 h-6 text-indigo-600" />
            </div>
            <CardTitle className="text-lg font-bold">Бот @safina_expense_bot</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground leading-relaxed">
            Мобильный пульт управления для сотрудников «в полях». Используется для подачи заявок, мгновенных уведомлений и быстрых одобрений.
          </CardContent>
          <div className="h-1 bg-indigo-500/20 w-full mt-4" />
        </Card>
        
        <Card className="glass-card overflow-hidden group hover:border-primary/50 transition-all duration-300">
          <CardHeader className="pb-2 space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 flex items-center justify-center group-hover:bg-emerald-500/20 transition-colors">
              <Monitor className="w-6 h-6 text-emerald-600" />
            </div>
            <CardTitle className="text-lg font-bold">Веб-панель (Админка)</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground leading-relaxed">
            Полноценный рабочий стол для глубокого анализа, работы с большими таблицами, архивом и финансовыми отчетами.
          </CardContent>
          <div className="h-1 bg-emerald-500/20 w-full mt-4" />
        </Card>

        <Card className="glass-card overflow-hidden group hover:border-primary/50 transition-all duration-300">
          <CardHeader className="pb-2 space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-amber-500/10 flex items-center justify-center group-hover:bg-amber-500/20 transition-colors">
              <ShieldCheck className="w-6 h-6 text-amber-600" />
            </div>
            <CardTitle className="text-lg font-bold">Прозрачность и Учет</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground leading-relaxed">
            Каждое действие записывается в «Историю» (Timeline) с цифровой подписью. Ни одно решение не останется незамеченным.
          </CardContent>
          <div className="h-1 bg-amber-500/20 w-full mt-4" />
        </Card>
      </div>

      <Accordion type="single" collapsible className="w-full space-y-6">
        
        {/* 1. Назначение системы */}
        <AccordionItem value="purpose" className="border-0 rounded-3xl px-6 bg-card/50 backdrop-blur-md shadow-sm border border-white/10">
          <AccordionTrigger className="hover:no-underline py-8">
            <div className="flex items-center gap-5 text-left">
              <div className="p-3 bg-blue-500/10 rounded-2xl border border-blue-500/20 shadow-inner">
                <Layers className="w-6 h-6 text-blue-600" />
              </div>
              <div className="space-y-1">
                <p className="font-bold text-xl tracking-tight">Зачем нужна эта система?</p>
                <p className="text-sm font-normal text-muted-foreground">Основные задачи и преимущества</p>
              </div>
            </div>
          </AccordionTrigger>
          <AccordionContent className="pb-8 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 px-2">
              <div className="space-y-4">
                <h4 className="font-bold text-md flex items-center gap-2 text-foreground">
                  <Workflow className="w-4 h-4 text-blue-600" /> Единый рабочий процесс
                </h4>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Платформа заменяет бумажную волокиту и хаос в чатах тремя ключевыми решениями:
                </p>
                <ul className="space-y-3">
                  <li className="flex gap-3 text-sm items-start">
                    <div className="mt-1 p-1 bg-blue-500/20 rounded text-blue-600"><CheckIcon size={12} /></div>
                    <span><strong className="text-foreground">Контроль расходов:</strong> Двухэтапное согласование (Финдиректор → Директор) исключает ошибки.</span>
                  </li>
                  <li className="flex gap-3 text-sm items-start">
                    <div className="mt-1 p-1 bg-blue-500/20 rounded text-blue-600"><CheckIcon size={12} /></div>
                    <span><strong className="text-foreground">Управление возвратами:</strong> Простая доска (Канбан) для контроля денег клиентов на каждом этапе.</span>
                  </li>
                  <li className="flex gap-3 text-sm items-start">
                    <div className="mt-1 p-1 bg-blue-500/20 rounded text-blue-600"><CheckIcon size={12} /></div>
                    <span><strong className="text-foreground">Авто-документы:</strong> Система сама создает Word и Excel файлы на основе введенных данных.</span>
                  </li>
                </ul>
              </div>
              <div className="bg-muted/30 p-5 rounded-2xl border border-dashed border-muted-foreground/20">
                <h4 className="font-bold text-sm mb-3">Простыми словами об устройстве</h4>
                <p className="text-xs text-muted-foreground leading-relaxed mb-4">
                  Система состоит из «мозга» (сервера), который хранит все данные, и двух «рук»: Телеграм-бота для быстрой работы и Веб-панели для детального анализа.
                </p>
                <div className="space-y-3 text-xs text-muted-foreground font-mono">
                  <div className="flex justify-between items-center bg-background/50 p-2 rounded border">
                    <span>Сайт</span>
                    <Badge variant="outline" className="text-[10px]">Удобный интерфейс</Badge>
                  </div>
                  <div className="flex justify-between items-center bg-background/50 p-2 rounded border">
                    <span>База данных</span>
                    <Badge variant="outline" className="text-[10px]">Надежное хранение</Badge>
                  </div>
                  <div className="flex justify-between items-center bg-background/50 p-2 rounded border">
                    <span>Синхронизация</span>
                    <Badge variant="outline" className="text-[10px]">Мгновенно везде</Badge>
                  </div>
                </div>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* 2. Роли и доступы */}
        <AccordionItem value="roles" className="border-0 rounded-3xl px-6 bg-card/50 backdrop-blur-md shadow-sm border border-white/10">
          <AccordionTrigger className="hover:no-underline py-8">
            <div className="flex items-center gap-5 text-left">
              <div className="p-3 bg-purple-500/10 rounded-2xl border border-purple-500/20 shadow-inner">
                <Users className="w-6 h-6 text-purple-600" />
              </div>
              <div className="space-y-1">
                <p className="font-bold text-xl tracking-tight">Кто и что делает в системе?</p>
                <p className="text-sm font-normal text-muted-foreground">Роли пользователей и уровни доступа</p>
              </div>
            </div>
          </AccordionTrigger>
          <AccordionContent className="pb-8 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 border rounded-2xl bg-gradient-to-br from-background to-blue-50/20">
                <Badge className="mb-2 bg-blue-500/10 text-blue-600 border-blue-500/20 hover:bg-blue-500/10">Инициатор</Badge>
                <p className="text-sm font-bold mb-1">Сотрудник филиала</p>
                <p className="text-xs text-muted-foreground leading-relaxed">Создает заявки на расходы или возвраты через Телеграм-бота.</p>
              </div>
              <div className="p-4 border rounded-2xl bg-gradient-to-br from-background to-purple-50/20">
                <Badge className="mb-2 bg-purple-500/10 text-purple-600 border-purple-500/20 hover:bg-purple-500/10">Финансист / CFO</Badge>
                <p className="text-sm font-bold mb-1">Бухгалтерия</p>
                <p className="text-xs text-muted-foreground leading-relaxed">Первый этап проверки. Видит все цифры, ведет учет и выгружает отчеты.</p>
              </div>
              <div className="p-4 border rounded-2xl bg-gradient-to-br from-background to-amber-50/20">
                <Badge className="mb-2 bg-amber-500/10 text-amber-600 border-amber-500/20 hover:bg-amber-500/10">Директор / Admin</Badge>
                <p className="text-sm font-bold mb-1">Руководство</p>
                <p className="text-xs text-muted-foreground leading-relaxed">Финальное решение. Имеет доступ ко всем настройкам системы.</p>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* 3. Автоматизация документов */}
        <AccordionItem value="automation" className="border-0 rounded-3xl px-6 bg-card/50 backdrop-blur-md shadow-sm border border-white/10">
          <AccordionTrigger className="hover:no-underline py-8">
            <div className="flex items-center gap-5 text-left">
              <div className="p-3 bg-orange-500/10 rounded-2xl border border-orange-500/20 shadow-inner">
                <FileText className="w-6 h-6 text-orange-600" />
              </div>
              <div className="space-y-1">
                <p className="font-bold text-xl tracking-tight">Работа с документами</p>
                <p className="text-sm font-normal text-muted-foreground">Как создаются Word и Excel отчеты</p>
              </div>
            </div>
          </AccordionTrigger>
          <AccordionContent className="pb-8 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <h4 className="font-bold text-sm text-foreground">Умные анкеты в боте</h4>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Бот опрашивает сотрудника шаг за шагом. Как только ввод завершен, система берет готовый шаблон Word и вставляет туда все данные.
                </p>
                <div className="p-4 bg-muted/30 rounded-2xl border border-dashed flex flex-col items-center justify-center text-center space-y-2">
                  <Download className="w-8 h-8 text-muted-foreground/50" />
                  <p className="text-xs font-medium">Готовые документы сразу доступны для скачивания в админке</p>
                </div>
              </div>
              <div className="space-y-4">
                <h4 className="font-bold text-sm text-foreground">Финансовые отчеты (Excel)</h4>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  В разделе <strong>«Архив»</strong> вы можете выбрать нужные даты и филиалы, и система за секунду соберет таблицу Excel.
                </p>
                <div className="p-4 bg-emerald-500/5 rounded-2xl border border-emerald-500/10 text-emerald-800 dark:text-emerald-400">
                  <p className="text-xs font-bold mb-1 flex items-center gap-1"><ArrowRight size={12} /> Совет для профи:</p>
                  <p className="text-[11px] leading-relaxed opacity-80">Используйте фильтры по проектам, чтобы увидеть аналитику конкретного филиала перед выгрузкой.</p>
                </div>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* 4. Как проходит процесс */}
        <AccordionItem value="flow" className="border-0 rounded-3xl px-6 bg-card/50 backdrop-blur-md shadow-sm border border-white/10">
          <AccordionTrigger className="hover:no-underline py-8">
            <div className="flex items-center gap-5 text-left">
              <div className="p-3 bg-rose-500/10 rounded-2xl border border-rose-500/20 shadow-inner">
                <Workflow className="w-6 h-6 text-rose-600" />
              </div>
              <div className="space-y-1">
                <p className="font-bold text-xl tracking-tight">Путь заявки: От создания до оплаты</p>
                <p className="text-sm font-normal text-muted-foreground">Пошаговая схема движения данных</p>
              </div>
            </div>
          </AccordionTrigger>
          <AccordionContent className="pb-8 space-y-4">
            <div className="relative p-6 bg-muted/20 border-l-2 border-rose-500 rounded-r-2xl space-y-4">
              <div className="flex gap-4 items-start">
                <div className="w-6 h-6 rounded-full bg-rose-500 text-white flex items-center justify-center text-[10px] font-bold shrink-0">1</div>
                <div>
                  <p className="text-sm font-bold">Подача</p>
                  <p className="text-xs text-muted-foreground italic">Сотрудник вводит данные в бот @safina_expense_bot</p>
                </div>
              </div>
              <div className="flex gap-4 items-start">
                <div className="w-6 h-6 rounded-full bg-rose-500 text-white flex items-center justify-center text-[10px] font-bold shrink-0">2</div>
                <div>
                  <p className="text-sm font-bold">Доставка</p>
                  <p className="text-xs text-muted-foreground italic">Система сохраняет заявку и мгновенно «подсвечивает» её в Веб-панели финансиста</p>
                </div>
              </div>
              <div className="flex gap-4 items-start">
                <div className="w-6 h-6 rounded-full bg-rose-500 text-white flex items-center justify-center text-[10px] font-bold shrink-0">3</div>
                <div>
                  <p className="text-sm font-bold">Одобрение</p>
                  <p className="text-xs text-muted-foreground italic">Финансист и Директор нажимают кнопки в админке или боте → сотрудник получает уведомление о результате</p>
                </div>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

      </Accordion>

      {/* Лучшие практики (Best Practices for CFO) */}
      <div className="glass-card p-10 rounded-[3rem] space-y-8 relative overflow-hidden shadow-xl border border-white/10">
        <div className="absolute top-0 right-0 w-64 h-64 bg-amber-500/5 rounded-full blur-3xl -mr-32 -mt-32" />
        <h3 className="text-2xl font-bold flex items-center gap-4">
          <div className="p-2 bg-amber-500/10 rounded-xl"><Lightbulb className="w-7 h-7 text-amber-500" /></div>
          Золотые правила для финансистов
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          <div className="flex gap-5">
            <div className="flex-shrink-0 w-10 h-10 rounded-2xl bg-primary text-primary-foreground flex items-center justify-center font-bold text-lg shadow-lg">1</div>
            <div>
              <p className="font-bold text-md mb-2 text-foreground">Утренняя проверка</p>
              <p className="text-sm text-muted-foreground leading-relaxed">Начинайте рабочий день с кнопки «Проверить новые заявки» в боте. Это предотвратит «заторы» в оплатах.</p>
            </div>
          </div>
          <div className="flex gap-5">
            <div className="flex-shrink-0 w-10 h-10 rounded-2xl bg-primary text-primary-foreground flex items-center justify-center font-bold text-lg shadow-lg">2</div>
            <div>
              <p className="font-bold text-md mb-2 text-foreground">Комментарии — это след</p>
              <p className="text-sm text-muted-foreground leading-relaxed">Всегда пишите причину отклонения. Через полгода эти записи помогут вспомнить, почему трата была заблокирована.</p>
            </div>
          </div>
          <div className="flex gap-5">
            <div className="flex-shrink-0 w-10 h-10 rounded-2xl bg-primary text-primary-foreground flex items-center justify-center font-bold text-lg shadow-lg">3</div>
            <div>
              <p className="font-bold text-md mb-2 text-foreground">Личные заметки (Internal context)</p>
              <p className="text-sm text-muted-foreground leading-relaxed">Используйте поле «Внутренний контекст» для записей, которые увидите только вы и Директор. Обычный сотрудник их не прочитает.</p>
            </div>
          </div>
          <div className="flex gap-5">
            <div className="flex-shrink-0 w-10 h-10 rounded-2xl bg-primary text-primary-foreground flex items-center justify-center font-bold text-lg shadow-lg">4</div>
            <div>
              <p className="font-bold text-md mb-2 text-foreground">Проверка реквизитов</p>
              <p className="text-sm text-muted-foreground leading-relaxed">Для возвратов всегда сверяйте номер карты и ФИО. Ошибка здесь — это реальная потеря денег.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Раздел для разработчиков (Developer Section) */}
      <div className="p-8 rounded-3xl bg-muted/50 border border-muted-foreground/10 space-y-4">
        <h4 className="font-bold text-lg flex items-center gap-2 text-foreground/80">
          <Code2 className="w-5 h-5 text-muted-foreground" /> Для разработчиков и IT
        </h4>
        <p className="text-sm text-muted-foreground leading-relaxed">
          Если вам нужны технические детали архитектуры, схемы базы данных или инструкции по развертыванию, пожалуйста, обратитесь к официальной документации проекта.
        </p>
        <a 
          href="https://deepwiki.com/axatsa/Safina-bot/1-overview" 
          target="_blank" 
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 text-sm font-semibold text-primary hover:underline group"
        >
          Техническая вики Safina Bot (DeepWiki) <ExternalLink className="w-4 h-4 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
        </a>
      </div>
      
      {/* Подвал (Footer) */}
      <div className="text-center text-muted-foreground text-sm flex flex-col items-center gap-4 border-t pt-10">
        <p className="font-medium">© 2026 Thompson Finance. Внутренняя документация проекта Safina.</p>
        <div className="flex items-center gap-6 opacity-60 text-[11px]">
          <span className="flex items-center gap-2 underline decoration-primary/30 underline-offset-4 tracking-tight">
            <Calendar className="w-4 h-4" /> Обновлено: 25.03.2026
          </span>
          <span className="flex items-center gap-2 font-mono bg-muted px-2 py-1 rounded-full border">
            Версия системы v3.5-LITE-PRO
          </span>
        </div>
      </div>
    </div>
  );
};

// Вспомогательный компонент для иконок-галочек
const CheckIcon = ({ size = 16 }) => (
  <svg 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="3" 
    strokeLinecap="round" 
    strokeLinejoin="round"
  >
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

export default FAQ;
