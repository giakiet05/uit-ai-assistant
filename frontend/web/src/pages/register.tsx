import { useState } from "react"
import { apiClient } from "@/lib/api"
import { Link } from "react-router-dom"

type RegistrationStep = "email" | "verify" | "complete"

const USE_MOCK_AUTH = import.meta.env.VITE_AUTH_MODE === "mock"

export default function RegisterPage() {
  const [step, setStep] = useState<RegistrationStep>("email")
  const [email, setEmail] = useState("")
  const [otp, setOtp] = useState("")
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [verificationToken, setVerificationToken] = useState("")

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  // Step 1: Send Email Verification
  const handleSendEmail = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      if (USE_MOCK_AUTH) {
        await new Promise((resolve) => setTimeout(resolve, 800))
        // Mock: any @uit.edu.vn email
        if (email.endsWith("@uit.edu.vn")) {
          setStep("verify")
        } else {
          setError("Email phải có đuôi @uit.edu.vn")
        }
      } else {
        const response = await apiClient.sendEmailVerification(email)
        if (response.success) {
          setStep("verify")
        } else {
          setError(response.message || "Gửi email thất bại")
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Có lỗi xảy ra")
    } finally {
      setLoading(false)
    }
  }

  // Step 2: Verify OTP
  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      if (USE_MOCK_AUTH) {
        await new Promise((resolve) => setTimeout(resolve, 800))
        // Mock: any 6-digit OTP
        if (otp.length === 6) {
          setVerificationToken("mock-verification-token")
          setStep("complete")
        } else {
          setError("Mã OTP phải có 6 chữ số")
        }
      } else {
        const response = await apiClient.verifyEmailCode(email, otp)
        if (response.success && response.data) {
          setVerificationToken(response.data.verification_token)
          setStep("complete")
        } else {
          setError(response.message || "Mã OTP không đúng")
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Có lỗi xảy ra")
    } finally {
      setLoading(false)
    }
  }

  // Step 3: Complete Registration
  const handleCompleteRegistration = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    // Validate passwords
    if (password !== confirmPassword) {
      setError("Mật khẩu xác nhận không khớp")
      return
    }

    if (password.length < 6) {
      setError("Mật khẩu phải có ít nhất 6 ký tự")
      return
    }

    setLoading(true)

    try {
      if (USE_MOCK_AUTH) {
        await new Promise((resolve) => setTimeout(resolve, 800))
        const mockUser = {
          id: "1",
          username: username,
          email: email,
          full_name: username,
        }
        localStorage.setItem("user", JSON.stringify(mockUser))
        localStorage.setItem("accessToken", "mock-jwt-token")
        localStorage.setItem("refreshToken", "mock-refresh-token")
        window.location.href = "/chat"
      } else {
        const response = await apiClient.completeRegistration(verificationToken, username, password)
        if (response.success && response.data) {
          localStorage.setItem("user", JSON.stringify(response.data.user))
          localStorage.setItem("accessToken", response.data.access_token)
          localStorage.setItem("refreshToken", response.data.refresh_token)
          window.location.href = "/chat"
        } else {
          setError(response.message || "Đăng ký thất bại")
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Có lỗi xảy ra")
    } finally {
      setLoading(false)
    }
  }

  // Resend OTP
  const handleResendOTP = async () => {
    setError("")
    setLoading(true)

    try {
      if (!USE_MOCK_AUTH) {
        const response = await apiClient.resendOTP(email)
        if (response.success) {
          alert("Mã OTP mới đã được gửi đến email của bạn")
        } else {
          setError(response.message || "Gửi lại OTP thất bại")
        }
      } else {
        await new Promise((resolve) => setTimeout(resolve, 500))
        alert("Mã OTP mới đã được gửi (Mock mode)")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Có lỗi xảy ra")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-card/80 backdrop-blur-sm rounded-2xl shadow-2xl border border-border/50 p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent mb-2">
              Đăng ký tài khoản
            </h1>
            <p className="text-sm text-muted-foreground">
              {step === "email" && "Nhập email UIT của bạn"}
              {step === "verify" && "Xác thực email"}
              {step === "complete" && "Hoàn tất đăng ký"}
            </p>
          </div>

          {/* Step Indicator */}
          <div className="flex justify-center mb-6">
            <div className="flex items-center space-x-2">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step === "email" ? "bg-primary text-primary-foreground" : "bg-primary/20 text-primary"}`}>
                1
              </div>
              <div className={`w-12 h-0.5 ${step !== "email" ? "bg-primary" : "bg-border"}`} />
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step === "verify" ? "bg-primary text-primary-foreground" : step === "complete" ? "bg-primary/20 text-primary" : "bg-border text-muted-foreground"}`}>
                2
              </div>
              <div className={`w-12 h-0.5 ${step === "complete" ? "bg-primary" : "bg-border"}`} />
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step === "complete" ? "bg-primary text-primary-foreground" : "bg-border text-muted-foreground"}`}>
                3
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 rounded-lg bg-destructive/5 border border-destructive/20 p-3.5 flex items-start gap-3">
              <svg className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm text-destructive/90 font-medium">{error}</p>
            </div>
          )}

          {/* Step 1: Email */}
          {step === "email" && (
            <form onSubmit={handleSendEmail} className="space-y-5">
              <div className="space-y-2">
                <label htmlFor="email" className="block text-sm font-semibold text-foreground/90">
                  Email UIT
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full px-4 py-2.5 bg-background border border-border rounded-lg placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-200"
                  placeholder="example@uit.edu.vn"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 px-4 rounded-lg font-semibold text-primary-foreground bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.01] active:scale-[0.99] transition-all duration-200"
              >
                {loading ? "Đang gửi..." : "Gửi mã xác thực"}
              </button>
            </form>
          )}

          {/* Step 2: Verify OTP */}
          {step === "verify" && (
            <form onSubmit={handleVerifyOTP} className="space-y-5">
              <div className="space-y-2">
                <label htmlFor="otp" className="block text-sm font-semibold text-foreground/90">
                  Mã OTP
                </label>
                <input
                  id="otp"
                  type="text"
                  required
                  maxLength={6}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
                  className="block w-full px-4 py-2.5 bg-background border border-border rounded-lg placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-200 text-center text-2xl tracking-widest"
                  placeholder="000000"
                />
                <p className="text-xs text-muted-foreground text-center">
                  Mã OTP đã được gửi đến <span className="font-semibold">{email}</span>
                </p>
              </div>

              <button
                type="submit"
                disabled={loading || otp.length !== 6}
                className="w-full py-2.5 px-4 rounded-lg font-semibold text-primary-foreground bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.01] active:scale-[0.99] transition-all duration-200"
              >
                {loading ? "Đang xác thực..." : "Xác thực"}
              </button>

              <div className="flex justify-between items-center text-sm">
                <button
                  type="button"
                  onClick={() => setStep("email")}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  ← Đổi email
                </button>
                <button
                  type="button"
                  onClick={handleResendOTP}
                  disabled={loading}
                  className="text-primary hover:text-primary/80 font-medium transition-colors disabled:opacity-50"
                >
                  Gửi lại mã
                </button>
              </div>
            </form>
          )}

          {/* Step 3: Complete Registration */}
          {step === "complete" && (
            <form onSubmit={handleCompleteRegistration} className="space-y-5">
              <div className="space-y-2">
                <label htmlFor="username" className="block text-sm font-semibold text-foreground/90">
                  Tên đăng nhập
                </label>
                <input
                  id="username"
                  type="text"
                  required
                  minLength={3}
                  maxLength={20}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="block w-full px-4 py-2.5 bg-background border border-border rounded-lg placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-200"
                  placeholder="Nhập tên đăng nhập"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="password" className="block text-sm font-semibold text-foreground/90">
                  Mật khẩu
                </label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    required
                    minLength={6}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="block w-full px-4 py-2.5 pr-11 bg-background border border-border rounded-lg placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-200"
                    placeholder="Nhập mật khẩu"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-muted-foreground hover:text-foreground transition-colors duration-200"
                  >
                    {showPassword ? (
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                      </svg>
                    ) : (
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <label htmlFor="confirmPassword" className="block text-sm font-semibold text-foreground/90">
                  Xác nhận mật khẩu
                </label>
                <div className="relative">
                  <input
                    id="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    required
                    minLength={6}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="block w-full px-4 py-2.5 pr-11 bg-background border border-border rounded-lg placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-200"
                    placeholder="Nhập lại mật khẩu"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-muted-foreground hover:text-foreground transition-colors duration-200"
                  >
                    {showConfirmPassword ? (
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                      </svg>
                    ) : (
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 px-4 rounded-lg font-semibold text-primary-foreground bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.01] active:scale-[0.99] transition-all duration-200"
              >
                {loading ? "Đang đăng ký..." : "Hoàn tất đăng ký"}
              </button>
            </form>
          )}

          {/* Footer */}
          <div className="mt-6 text-center text-sm text-muted-foreground">
            Đã có tài khoản?{" "}
            <Link to="/login" className="text-primary hover:text-primary/80 font-semibold transition-colors">
              Đăng nhập
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
