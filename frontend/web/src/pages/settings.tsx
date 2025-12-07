import { useNavigate } from "react-router-dom"
import { useForm } from "react-hook-form"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Loader2, ArrowLeft, Save } from "lucide-react"
import { useSettings, useUpdateSettings } from "@/hooks/useSettings"
import type { UpdateSettingsRequest } from "@/lib/api"
import { useTheme } from "next-themes"

export default function SettingsPage() {
  const navigate = useNavigate()
  const { settings, loading, refetch } = useSettings()
  const { updateSettings, loading: updating } = useUpdateSettings()
  const { setTheme } = useTheme()

  const {
    register,
    handleSubmit,
    setValue,
    watch,
  } = useForm<UpdateSettingsRequest>({
    values: {
      language: settings?.language || "en",
      theme: settings?.theme || "dark",
      notify_new_features: settings?.notify_new_features || false,
    },
  })

  const currentTheme = watch("theme")
  const currentLanguage = watch("language")
  const notifyNewFeatures = watch("notify_new_features")

  const onSubmit = async (data: UpdateSettingsRequest) => {
    try {
      const result = await updateSettings(data)

      // Apply theme change immediately
      if (data.theme) {
        setTheme(data.theme)
      }

      await refetch()
    } catch (error) {
      // Error is handled by the hook
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  if (!settings) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>Failed to load settings</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container max-w-4xl mx-auto py-8 px-4">
        <div className="mb-6">
          <Button variant="ghost" onClick={() => navigate(-1)}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-6">
            <Card className="border-2">
              <CardHeader className="border-b bg-muted/50">
                <CardTitle className="text-2xl">Appearance</CardTitle>
                <CardDescription>Customize how the app looks</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 pt-6">
              <div className="flex items-center justify-between p-4 rounded-lg border-2 bg-muted/20">
                <div className="space-y-1">
                  <Label htmlFor="theme" className="text-base font-semibold">Theme</Label>
                  <p className="text-sm text-muted-foreground">
                    Choose your preferred color scheme
                  </p>
                </div>
                <Select
                  value={currentTheme}
                  onValueChange={(value: "light" | "dark") => {
                    setValue("theme", value)
                  }}
                >
                  <SelectTrigger className="w-[180px]" id="theme">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">Light</SelectItem>
                    <SelectItem value="dark">Dark</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <Card className="border-2">
            <CardHeader className="border-b bg-muted/50">
              <CardTitle className="text-2xl">Language</CardTitle>
              <CardDescription>Choose your preferred language</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 pt-6">
              <div className="flex items-center justify-between p-4 rounded-lg border-2 bg-muted/20">
                <div className="space-y-1">
                  <Label htmlFor="language" className="text-base font-semibold">Interface Language</Label>
                  <p className="text-sm text-muted-foreground">
                    Select the language for the interface
                  </p>
                </div>
                <Select
                  value={currentLanguage}
                  onValueChange={(value: "vi" | "en") => {
                    setValue("language", value)
                  }}
                >
                  <SelectTrigger className="w-[180px]" id="language">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="vi">Tiếng Việt</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <Card className="border-2">
            <CardHeader className="border-b bg-muted/50">
              <CardTitle className="text-2xl">Notifications</CardTitle>
              <CardDescription>Manage your notification preferences</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 pt-6">
              <div className="flex items-center justify-between p-4 rounded-lg border-2 bg-muted/20">
                <div className="space-y-1">
                  <Label htmlFor="notify_new_features" className="text-base font-semibold">New Features</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive notifications about new features
                  </p>
                </div>
                <Switch
                  id="notify_new_features"
                  checked={notifyNewFeatures}
                  onCheckedChange={(checked) => {
                    setValue("notify_new_features", checked)
                  }}
                />
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-end pt-4">
            <Button type="submit" disabled={updating} size="lg">
              {updating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              <Save className="mr-2 h-4 w-4" />
              Save Changes
            </Button>
          </div>
          </div>
        </form>
      </div>
    </div>
  )
}
