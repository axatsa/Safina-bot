import { authService } from "./services/auth";
import { projectsService } from "./services/projects";
import { teamService } from "./services/team";
import { expensesService } from "./services/expenses";
import { analyticsService } from "./services/analytics";
import { rbac } from "./rbac";

/**
 * The 'store' object is now a facade that aggregates modular services.
 * This ensures backward compatibility while the rest of the app is refactored.
 */
export const store = {
  // Auth & RBAC
  ...authService,
  ...rbac,

  // Projects
  ...projectsService,

  // Team
  ...teamService,

  // Expenses
  ...expensesService,

  // Analytics
  ...analyticsService,
};

