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
  Calendar
} from "lucide-react";
import { 
  Accordion, 
  AccordionContent, 
  AccordionItem, 
  AccordionTrigger 
} from "@/components/ui/accordion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const FAQ = () => {
  return (
    <div className="p-6 max-w-4xl mx-auto space-y-8 animate-fade-in pb-20">
      <div className="text-center space-y-3 border-b pb-8">
        <div className="inline-flex items-center justify-center p-3 bg-primary/10 rounded-2xl mb-2">
          <BookOpen className="w-8 h-8 text-primary" />
        </div>
        <h1 className="text-4xl font-display font-bold text-foreground tracking-tight">База знаний и FAQ</h1>
        <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
          Полное руководство по использованию системы Thompson Finance для финансистов и администрации.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-0 shadow-sm bg-indigo-50/50 dark:bg-indigo-950/20">
          <CardHeader className="pb-2">
            <Bot className="w-5 h-5 text-indigo-600" />
            <CardTitle className="text-sm font-bold">Бот @safina_expense_bot</CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground">
            Ваш мобильный пульт управления для быстрых одобрений и уведомлений.
          </CardContent>
        </Card>
        <Card className="border-0 shadow-sm bg-emerald-50/50 dark:bg-emerald-950/20">
          <CardHeader className="pb-2">
            <Monitor className="w-5 h-5 text-emerald-600" />
            <CardTitle className="text-sm font-bold">Веб-админка</CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground">
            Полноценный дашборд для глубокого анализа, работы с таблицами и архивом.
          </CardContent>
        </Card>
        <Card className="border-0 shadow-sm bg-amber-50/50 dark:bg-amber-950/20">
          <CardHeader className="pb-2">
            <ShieldCheck className="w-5 h-5 text-amber-600" />
            <CardTitle className="text-sm font-bold">Безопасность</CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground">
            Все действия логируются в Timeline. Каждое решение имеет цифровую подпись.
          </CardContent>
        </Card>
      </div>

      <Accordion type="single" collapsible className="w-full space-y-4">
        
        {/* 1. Начало работы */}
        <AccordionItem value="start" className="border rounded-2xl px-6 bg-card shadow-sm">
          <AccordionTrigger className="hover:no-underline py-6">
            <div className="flex items-center gap-4 text-left">
              <div className="p-2 bg-blue-100 rounded-lg"><HelpCircle className="w-5 h-5 text-blue-600" /></div>
              <div>
                <p className="font-bold text-lg">🚀 С чего начать?</p>
                <p className="text-sm font-normal text-muted-foreground">Первый вход в бот и админку</p>
              </div>
            </div>
          </AccordionTrigger>
          <AccordionContent className="pb-6 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <h4 className="font-bold text-sm flex items-center gap-2"><Bot className="w-4 h-4 text-primary" /> Telegram-бот</h4>
                <ul className="text-sm space-y-2 text-muted-foreground list-disc pl-4">
                  <li>Найдите <b>@safina_expense_bot</b> в поиске.</li>
                  <li>Введите <b>логин и пароль</b> (выдает Сафина).</li>
                  <li>Используйте кнопку <b>«Проверить новые заявки»</b> для работы.</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h4 className="font-bold text-sm flex items-center gap-2"><Monitor className="w-4 h-4 text-primary" /> Веб-интерфейс</h4>
                <ul className="text-sm space-y-2 text-muted-foreground list-disc pl-4">
                  <li>Зайдите под своим логином в админку.</li>
                  <li>Вы сразу попадете в раздел <b>«Согласование»</b>.</li>
                  <li>Доступ к <b>Статистике</b> и <b>Архиву</b> доступен из бокового меню.</li>
                </ul>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* 2. Типы заявок */}
        <AccordionItem value="types" className="border rounded-2xl px-6 bg-card shadow-sm">
          <AccordionTrigger className="hover:no-underline py-6">
            <div className="flex items-center gap-4 text-left">
              <div className="p-2 bg-purple-100 rounded-lg"><FileText className="w-5 h-5 text-purple-600" /></div>
              <div>
                <p className="font-bold text-lg">📌 Типы заявок</p>
                <p className="text-sm font-normal text-muted-foreground">Разница между инвестицией, возвратом и бланком</p>
              </div>
            </div>
          </AccordionTrigger>
          <AccordionContent className="pb-6 space-y-4">
            <div className="space-y-4">
              <div className="p-4 bg-muted/50 rounded-xl border-l-4 border-primary">
                <p className="font-bold text-sm mb-1">Инвестиция (Investment)</p>
                <p className="text-sm text-muted-foreground text-balance">Стандартный запрос на ТМЦ или услуги. Требует спецификации позиций и цен.</p>
              </div>
              <div className="p-4 bg-muted/50 rounded-xl border-l-4 border-rose-500">
                <p className="font-bold text-sm mb-1">Возврат (Refund)</p>
                <p className="text-sm text-muted-foreground text-balance">Заявление на возврат денег клиенту. Важно тщательно проверять банковские реквизиты.</p>
              </div>
              <div className="p-4 bg-muted/50 rounded-xl border-l-4 border-amber-500">
                <p className="font-bold text-sm mb-1">Бланк (Blank / LAND / Drujba)</p>
                <p className="text-sm text-muted-foreground text-balance">Служебные записки по готовым шаблонам. Автоматически превращаются в Word/PDF документы.</p>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* 3. Аналитика */}
        <AccordionItem value="analytics" className="border rounded-2xl px-6 bg-card shadow-sm">
          <AccordionTrigger className="hover:no-underline py-6">
            <div className="flex items-center gap-4 text-left">
              <div className="p-2 bg-emerald-100 rounded-lg"><BarChart3 className="w-5 h-5 text-emerald-600" /></div>
              <div>
                <p className="font-bold text-lg">📊 Аналитика и Отчеты</p>
                <p className="text-sm font-normal text-muted-foreground">Как следить за бюджетом и выгружать данные</p>
              </div>
            </div>
          </AccordionTrigger>
          <AccordionContent className="pb-6 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 border rounded-xl space-y-2">
                <p className="font-bold text-sm flex items-center gap-2"><DollarSign className="w-4 h-4 text-emerald-600" /> Валютный учет</p>
                <p className="text-sm text-muted-foreground">Система сама пересчитывает USD в UZS по курсу на день создания заявки для корректности графиков.</p>
              </div>
              <div className="p-4 border rounded-xl space-y-2">
                <p className="font-bold text-sm flex items-center gap-2"><Download className="w-4 h-4 text-blue-600" /> Экспорт данных</p>
                <p className="text-sm text-muted-foreground">Используйте раздел <b>«Архив»</b> для выгрузки Excel-отчётов за любой период по всем филиалам.</p>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* 4. Troubleshooting */}
        <AccordionItem value="trouble" className="border rounded-2xl px-6 bg-card shadow-sm">
          <AccordionTrigger className="hover:no-underline py-6">
            <div className="flex items-center gap-4 text-left">
              <div className="p-2 bg-rose-100 rounded-lg"><AlertTriangle className="w-5 h-5 text-rose-600" /></div>
              <div>
                <p className="font-bold text-lg">🛠 Решение проблем</p>
                <p className="text-sm font-normal text-muted-foreground">Если что-то пошло не так</p>
              </div>
            </div>
          </AccordionTrigger>
          <AccordionContent className="pb-6 space-y-3">
             <div className="space-y-4">
                <div className="space-y-1">
                  <p className="font-bold text-sm">Бот не присылает уведомления?</p>
                  <p className="text-sm text-muted-foreground">Проверьте статус авторизации командой <b>/start</b> или убедитесь, что бот не стоит в режиме «Без звука».</p>
                </div>
                <div className="space-y-1">
                  <p className="font-bold text-sm">Ошибка «Недостаточно прав»?</p>
                  <p className="text-sm text-muted-foreground">Ваша роль в системе должна быть <b>senior_financier</b> или <b>admin</b>. Обратитесь к Сафине для проверки ваших настроек в разделе «Команда».</p>
                </div>
             </div>
          </AccordionContent>
        </AccordionItem>

      </Accordion>

      <div className="bg-muted p-8 rounded-3xl space-y-6">
        <h3 className="text-xl font-bold flex items-center gap-3">
          <Lightbulb className="w-6 h-6 text-amber-500" /> Лучшие практики для CFO
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-sm">1</div>
            <div>
              <p className="font-semibold text-sm mb-1 text-foreground">Ежедневный ритуал</p>
              <p className="text-xs text-muted-foreground leading-relaxed">Начинайте день с кнопки «Проверить новые заявки» в боте. Это занимает 30 секунд, но предотвращает «заторы» в оплатах.</p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-sm">2</div>
            <div>
              <p className="font-semibold text-sm mb-1 text-foreground">Комментарии — это след</p>
              <p className="text-xs text-muted-foreground leading-relaxed">Всегда пишите причину отклонения. В архиве это поможет понять, почему трата была заблокирована спустя полгода.</p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-sm">3</div>
            <div>
              <p className="font-semibold text-sm mb-1 text-foreground">Внутренний чат</p>
              <p className="text-xs text-muted-foreground leading-relaxed">Используйте <b>"Internal context"</b> в админке для переписки с Сафиной. Сотрудник-инициатор эти комментарии не увидит.</p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-sm">4</div>
            <div>
              <p className="font-semibold text-sm mb-1 text-foreground">Проверка реквизитов</p>
              <p className="text-xs text-muted-foreground leading-relaxed">Для возвратов всегда сверяйте номер карты и ФИО. Ошибка здесь приведет к потере денег.</p>
            </div>
          </div>
        </div>
      </div>
      
      <div className="text-center text-muted-foreground text-sm flex flex-col items-center gap-2 pb-10">
        <p>© 2026 Thompson Finance. Все права защищены.</p>
        <p className="flex items-center gap-4">
          <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> Обновлено: 25.03.2026</span>
          <span className="flex items-center gap-1 font-mono text-[10px] opacity-50">v3.0-CLEAN</span>
        </p>
      </div>
    </div>
  );
};

export default FAQ;
