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
  Cpu
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
      {/* Header Section */}
      <div className="text-center space-y-4 relative py-10">
        <div className="absolute inset-0 -z-10 bg-gradient-to-b from-primary/5 to-transparent rounded-3xl blur-3xl opacity-50" />
        <div className="inline-flex items-center justify-center p-4 bg-primary/10 rounded-3xl mb-4 backdrop-blur-sm border border-primary/20 shadow-lg animate-float">
          <BookOpen className="w-10 h-10 text-primary" />
        </div>
        <h1 className="text-5xl font-display font-bold text-foreground tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/70">
          Knowledge Base & FAQ
        </h1>
        <p className="text-muted-foreground text-xl max-w-2xl mx-auto leading-relaxed">
          The comprehensive guide to Thompson Finance / Safina Expense Tracker for administration and financiers.
        </p>
      </div>

      {/* Core Systems Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="glass-card overflow-hidden group hover:border-primary/50 transition-all duration-300">
          <CardHeader className="pb-2 space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center group-hover:bg-indigo-500/20 transition-colors">
              <Bot className="w-6 h-6 text-indigo-600" />
            </div>
            <CardTitle className="text-lg font-bold">Bot @safina_expense_bot</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground leading-relaxed">
            The mobile control center for field employees. Used for quick submissions, instant approvals, and real-time status notifications.
          </CardContent>
          <div className="h-1 bg-indigo-500/20 w-full mt-4" />
        </Card>
        
        <Card className="glass-card overflow-hidden group hover:border-primary/50 transition-all duration-300">
          <CardHeader className="pb-2 space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 flex items-center justify-center group-hover:bg-emerald-500/20 transition-colors">
              <Monitor className="w-6 h-6 text-emerald-600" />
            </div>
            <CardTitle className="text-lg font-bold">Web Dashboard</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground leading-relaxed">
            A powerful administrative interface for deep analytics, mass data processing, archiving, and financial reporting.
          </CardContent>
          <div className="h-1 bg-emerald-500/20 w-full mt-4" />
        </Card>

        <Card className="glass-card overflow-hidden group hover:border-primary/50 transition-all duration-300">
          <CardHeader className="pb-2 space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-amber-500/10 flex items-center justify-center group-hover:bg-amber-500/20 transition-colors">
              <ShieldCheck className="w-6 h-6 text-amber-600" />
            </div>
            <CardTitle className="text-lg font-bold">Accountability</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground leading-relaxed">
            Every action is digitally signed and logged in the immutable Timeline. Multi-stage approvals ensure transparency.
          </CardContent>
          <div className="h-1 bg-amber-500/20 w-full mt-4" />
        </Card>
      </div>

      <Accordion type="single" collapsible className="w-full space-y-6">
        
        {/* 1. System Ecosystem & Purpose */}
        <AccordionItem value="purpose" className="border-0 rounded-3xl px-6 bg-card/50 backdrop-blur-md shadow-sm border border-white/10">
          <AccordionTrigger className="hover:no-underline py-8">
            <div className="flex items-center gap-5 text-left">
              <div className="p-3 bg-blue-500/10 rounded-2xl border border-blue-500/20 shadow-inner">
                <Layers className="w-6 h-6 text-blue-600" />
              </div>
              <div className="space-y-1">
                <p className="font-bold text-xl tracking-tight">System Ecosystem & Purpose</p>
                <p className="text-sm font-normal text-muted-foreground">What goals does the platform solve?</p>
              </div>
            </div>
          </AccordionTrigger>
          <AccordionContent className="pb-8 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 px-2">
              <div className="space-y-4">
                <h4 className="font-bold text-md flex items-center gap-2 text-foreground">
                  <Cpu className="w-4 h-4 text-blue-600" /> Unified Workflow
                </h4>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  The system serves three primary organizational needs to replace manual paperwork:
                </p>
                <ul className="space-y-3">
                  <li className="flex gap-3 text-sm items-start">
                    <div className="mt-1 p-1 bg-blue-500/20 rounded text-blue-600"><CheckIcon size={12} /></div>
                    <span><strong className="text-foreground">Expense Accountability:</strong> Tracking procurement with 2-stage (CFO/CEO) approvals.</span>
                  </li>
                  <li className="flex gap-3 text-sm items-start">
                    <div className="mt-1 p-1 bg-blue-500/20 rounded text-blue-600"><CheckIcon size={12} /></div>
                    <span><strong className="text-foreground">Refund Management:</strong> Managing complex client refund lifecycles via Kanban.</span>
                  </li>
                  <li className="flex gap-3 text-sm items-start">
                    <div className="mt-1 p-1 bg-blue-500/20 rounded text-blue-600"><CheckIcon size={12} /></div>
                    <span><strong className="text-foreground">Document Automation:</strong> Auto-generating Word & Excel from digital data.</span>
                  </li>
                </ul>
              </div>
              <div className="bg-muted/30 p-5 rounded-2xl border border-dashed border-muted-foreground/20">
                <h4 className="font-bold text-sm mb-3">High-Level Architecture</h4>
                <div className="space-y-3 text-xs text-muted-foreground font-mono">
                  <div className="flex justify-between items-center bg-background/50 p-2 rounded border">
                    <span>Frontend</span>
                    <Badge variant="outline" className="text-[10px]">React SPA / Vite</Badge>
                  </div>
                  <div className="flex justify-between items-center bg-background/50 p-2 rounded border">
                    <span>Backend</span>
                    <Badge variant="outline" className="text-[10px]">FastAPI / Python</Badge>
                  </div>
                  <div className="flex justify-between items-center bg-background/50 p-2 rounded border">
                    <span>Real-time</span>
                    <Badge variant="outline" className="text-[10px]">Redis SSE / PubSub</Badge>
                  </div>
                  <div className="flex justify-between items-center bg-background/50 p-2 rounded border">
                    <span>Database</span>
                    <Badge variant="outline" className="text-[10px]">PostgreSQL / SQLAlchemy</Badge>
                  </div>
                </div>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* 2. Key User Roles & Approvals */}
        <AccordionItem value="roles" className="border-0 rounded-3xl px-6 bg-card/50 backdrop-blur-md shadow-sm border border-white/10">
          <AccordionTrigger className="hover:no-underline py-8">
            <div className="flex items-center gap-5 text-left">
              <div className="p-3 bg-purple-500/10 rounded-2xl border border-purple-500/20 shadow-inner">
                <Users className="w-6 h-6 text-purple-600" />
              </div>
              <div className="space-y-1">
                <p className="font-bold text-xl tracking-tight">User Roles & Access Control</p>
                <p className="text-sm font-normal text-muted-foreground">Who has access to what functions?</p>
              </div>
            </div>
          </AccordionTrigger>
          <AccordionContent className="pb-8 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 border rounded-2xl bg-gradient-to-br from-background to-blue-50/20">
                <Badge className="mb-2 bg-blue-500/10 text-blue-600 border-blue-500/20 hover:bg-blue-500/10">Initiator</Badge>
                <p className="text-sm font-bold mb-1">Field Employee</p>
                <p className="text-xs text-muted-foreground">Submits expenses and refunds via Telegram Bot.</p>
              </div>
              <div className="p-4 border rounded-2xl bg-gradient-to-br from-background to-purple-50/20">
                <Badge className="mb-2 bg-purple-500/10 text-purple-600 border-purple-500/20 hover:bg-purple-500/10">Financier / CFO</Badge>
                <p className="text-sm font-bold mb-1">Finance Team</p>
                <p className="text-xs text-muted-foreground">First-stage approval. Manages audits, tables, and archives.</p>
              </div>
              <div className="p-4 border rounded-2xl bg-gradient-to-br from-background to-amber-50/20">
                <Badge className="mb-2 bg-amber-500/10 text-amber-600 border-amber-500/20 hover:bg-amber-500/10">CEO / Admin</Badge>
                <p className="text-sm font-bold mb-1">Executive</p>
                <p className="text-xs text-muted-foreground">Final-stage approval. Global system configuration.</p>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* 3. Document Generation & Export */}
        <AccordionItem value="automation" className="border-0 rounded-3xl px-6 bg-card/50 backdrop-blur-md shadow-sm border border-white/10">
          <AccordionTrigger className="hover:no-underline py-8">
            <div className="flex items-center gap-5 text-left">
              <div className="p-3 bg-orange-500/10 rounded-2xl border border-orange-500/20 shadow-inner">
                <FileText className="w-6 h-6 text-orange-600" />
              </div>
              <div className="space-y-1">
                <p className="font-bold text-xl tracking-tight">Document Automation</p>
                <p className="text-sm font-normal text-muted-foreground">How PDF/Word forms are created</p>
              </div>
            </div>
          </AccordionTrigger>
          <AccordionContent className="pb-8 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <h4 className="font-bold text-sm text-foreground">Interactive Wizards</h4>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  The bot uses a <code className="bg-muted px-1 rounded">blank_wizard</code> to collect data. Once finished, it uses <code className="bg-muted px-1 rounded">docxtpl</code> to inject data into templates.
                </p>
                <div className="p-4 bg-muted/30 rounded-2xl border border-dashed flex flex-col items-center justify-center text-center space-y-2">
                  <Download className="w-8 h-8 text-muted-foreground/50" />
                  <p className="text-xs font-medium">Ready-to-use documents are mirrored directly in the Web Admin</p>
                </div>
              </div>
              <div className="space-y-4">
                <h4 className="font-bold text-sm text-foreground">Financial Exports</h4>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Use the <strong>"Archive"</strong> section to generate custom Excel reports. The system utilizes <code className="bg-muted px-1 rounded">openpyxl</code> to compile thousands of records in seconds.
                </p>
                <div className="p-4 bg-emerald-500/5 rounded-2xl border border-emerald-500/10 text-emerald-800 dark:text-emerald-400">
                  <p className="text-xs font-bold mb-1 flex items-center gap-1"><ArrowRight size={12} /> Pro-Tip:</p>
                  <p className="text-[11px] leading-relaxed opacity-80">Filter by project or date before exporting to get specific branch analytics.</p>
                </div>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* 4. Real-time Interactions */}
        <AccordionItem value="realtime" className="border-0 rounded-3xl px-6 bg-card/50 backdrop-blur-md shadow-sm border border-white/10">
          <AccordionTrigger className="hover:no-underline py-8">
            <div className="flex items-center gap-5 text-left">
              <div className="p-3 bg-rose-500/10 rounded-2xl border border-rose-500/20 shadow-inner">
                <Workflow className="w-6 h-6 text-rose-600" />
              </div>
              <div className="space-y-1">
                <p className="font-bold text-xl tracking-tight">Real-time Interaction Flow</p>
                <p className="text-sm font-normal text-muted-foreground">How notifications and approvals sync</p>
              </div>
            </div>
          </AccordionTrigger>
          <AccordionContent className="pb-8 space-y-4">
            <div className="relative p-6 bg-muted/20 border-l-2 border-rose-500 rounded-r-2xl space-y-4">
              <div className="flex gap-4 items-start">
                <div className="w-6 h-6 rounded-full bg-rose-500 text-white flex items-center justify-center text-[10px] font-bold shrink-0">1</div>
                <div>
                  <p className="text-sm font-bold">Submission</p>
                  <p className="text-xs text-muted-foreground italic">Employee submits request via @safina_expense_bot</p>
                </div>
              </div>
              <div className="flex gap-4 items-start">
                <div className="w-6 h-6 rounded-full bg-rose-500 text-white flex items-center justify-center text-[10px] font-bold shrink-0">2</div>
                <div>
                  <p className="text-sm font-bold">Persistence & Routing</p>
                  <p className="text-xs text-muted-foreground italic">FastAPI saves to DB → Redis pushes event via SSE</p>
                </div>
              </div>
              <div className="flex gap-4 items-start">
                <div className="w-6 h-6 rounded-full bg-rose-500 text-white flex items-center justify-center text-[10px] font-bold shrink-0">3</div>
                <div>
                  <p className="text-sm font-bold">Visual Update</p>
                  <p className="text-xs text-muted-foreground italic">Web UI pops up notification → Financier sees it instantly</p>
                </div>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

      </Accordion>

      {/* Best Practices for CFO */}
      <div className="glass-card p-10 rounded-[3rem] space-y-8 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-amber-500/5 rounded-full blur-3xl -mr-32 -mt-32" />
        <h3 className="text-2xl font-bold flex items-center gap-4">
          <div className="p-2 bg-amber-500/10 rounded-xl"><Lightbulb className="w-7 h-7 text-amber-500" /></div>
          Best Practices for CFO & Finance Team
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          <div className="flex gap-5">
            <div className="flex-shrink-0 w-10 h-10 rounded-2xl bg-primary text-primary-foreground flex items-center justify-center font-bold text-lg shadow-lg">1</div>
            <div>
              <p className="font-bold text-md mb-2 text-foreground">Daily Check Ritual</p>
              <p className="text-sm text-muted-foreground leading-relaxed">Start your morning by clicking "Check New Requests" in the bot. It ensures that critical payments are not bottlenecked.</p>
            </div>
          </div>
          <div className="flex gap-5">
            <div className="flex-shrink-0 w-10 h-10 rounded-2xl bg-primary text-primary-foreground flex items-center justify-center font-bold text-lg shadow-lg">2</div>
            <div>
              <p className="font-bold text-md mb-2 text-foreground">Comments Leave a Trace</p>
              <p className="text-sm text-muted-foreground leading-relaxed">Always document the reason for rejection. This audit trail is vital for year-end reviews and accountability.</p>
            </div>
          </div>
          <div className="flex gap-5">
            <div className="flex-shrink-0 w-10 h-10 rounded-2xl bg-primary text-primary-foreground flex items-center justify-center font-bold text-lg shadow-lg">3</div>
            <div>
              <p className="font-bold text-md mb-2 text-foreground">Internal Context vs Response</p>
              <p className="text-sm text-muted-foreground leading-relaxed">Use "Internal context" for private notes intended only for Safina or CEO. The initiator will NOT see these notes.</p>
            </div>
          </div>
          <div className="flex gap-5">
            <div className="flex-shrink-0 w-10 h-10 rounded-2xl bg-primary text-primary-foreground flex items-center justify-center font-bold text-lg shadow-lg">4</div>
            <div>
              <p className="font-bold text-md mb-2 text-foreground">Requisite Verification</p>
              <p className="text-sm text-muted-foreground leading-relaxed">For Refund requests, cross-reference card numbers and names meticulously. Mistakes here lead to irreversible data loss.</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Footer */}
      <div className="text-center text-muted-foreground text-sm flex flex-col items-center gap-4 border-t pt-10">
        <p className="font-medium">© 2026 Thompson Finance. Project Safina Internal Docs.</p>
        <div className="flex items-center gap-6 opacity-60">
          <span className="flex items-center gap-2 underline decoration-primary/30 underline-offset-4 tracking-tight">
            <Calendar className="w-4 h-4" /> Last Updated: 2026.03.25
          </span>
          <span className="flex items-center gap-2 font-mono text-[10px] bg-muted px-2 py-1 rounded-full border">
            System v3.5-LITE-PRO
          </span>
        </div>
      </div>
    </div>
  );
};

// Helper component for checklist icons
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
