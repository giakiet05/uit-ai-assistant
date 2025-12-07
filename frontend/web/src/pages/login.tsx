import LoginForm from "@/components/login-form"

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 py-8">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,var(--border)_1px,transparent_1px),linear-gradient(to_bottom,var(--border)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black_100%)] opacity-30"></div>
      </div>

      <div className="w-full max-w-sm relative z-10">
        <div className="bg-card border border-border rounded-xl shadow-lg p-8 space-y-6">
          <div className="space-y-3 text-center">
            <div className="flex justify-center">
              <div className="w-14 h-14 bg-primary/10 rounded-lg flex items-center justify-center">
                <svg className="w-7 h-7 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">UIT AI Assistant</h1>
              <p className="text-sm text-muted-foreground mt-1">Đăng nhập để trải nghiệm trợ lý AI</p>
            </div>
          </div>

          <LoginForm />
        </div>

        <p className="text-center text-xs text-muted-foreground mt-6">
          Powered by <span className="font-semibold text-foreground">UIT AI Team</span>
        </p>
      </div>
    </div>
  )
}
