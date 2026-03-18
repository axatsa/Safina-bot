import React, { Component, ErrorInfo, ReactNode } from "react";
import { Button } from "./ui/button";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(_: Error): State {
    return { hasError: true };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  private handleReload = () => {
    window.location.reload();
  };

  private handleLogout = () => {
    localStorage.removeItem("safina_token");
    localStorage.removeItem("safina_role");
    localStorage.removeItem("safina_user");
    localStorage.removeItem("safina_projectId");
    window.location.href = "/";
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
          <div className="max-w-md w-full space-y-8 p-8 bg-card rounded-xl border shadow-lg text-center">
            <h2 className="text-2xl font-bold text-foreground">Что-то пошло не так</h2>
            <p className="text-muted-foreground">
              Произошла непредвиденная ошибка. Попробуйте обновить страницу или выйти из аккаунта.
            </p>
            <div className="flex flex-col gap-4 pt-4">
              <Button onClick={this.handleReload} variant="default" className="w-full">
                Перезагрузить страницу
              </Button>
              <Button onClick={this.handleLogout} variant="outline" className="w-full">
                Выйти
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
