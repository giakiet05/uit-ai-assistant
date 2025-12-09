import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useForm } from "react-hook-form"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { Loader2, ArrowLeft, Save } from "lucide-react"
import { AvatarUpload } from "@/components/avatar-upload"
import { ChangePasswordDialog } from "@/components/change-password-dialog"
import { useUserProfile, useUpdateProfile } from "@/hooks/useUserProfile"
import type { UpdateProfileRequest } from "@/lib/api"

export default function ProfilePage() {
  const navigate = useNavigate()
  const { user, loading, refetch } = useUserProfile()
  const { updateProfile, loading: updating } = useUpdateProfile()
  const [isEditing, setIsEditing] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<UpdateProfileRequest>({
    values: {
      username: user?.username || "",
    },
  })

  const onSubmit = async (data: UpdateProfileRequest) => {
    try {
      await updateProfile(data)
      await refetch()
      setIsEditing(false)
    } catch (error) {
      // Error is handled by the hook
    }
  }

  const handleCancel = () => {
    reset()
    setIsEditing(false)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>Failed to load profile</p>
      </div>
    )
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    })
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

        <div className="space-y-6">
        <Card className="border-2">
          <CardHeader className="border-b bg-muted/50">
            <CardTitle className="text-2xl">Profile</CardTitle>
            <CardDescription>Manage your account information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6 pt-6">
            <div className="flex flex-col items-center py-4">
              <AvatarUpload
                avatarUrl={user.avatar?.url}
                username={user.username}
                onAvatarChange={refetch}
              />
            </div>

            <Separator className="my-6" />

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              <div className="grid gap-3">
                <Label htmlFor="username" className="text-base font-semibold">Username</Label>
                {isEditing ? (
                  <>
                    <Input
                      id="username"
                      {...register("username", {
                        required: "Username is required",
                        minLength: {
                          value: 3,
                          message: "Username must be at least 3 characters",
                        },
                      })}
                      disabled={updating}
                    />
                    {errors.username && (
                      <p className="text-sm text-red-500">{errors.username.message}</p>
                    )}
                  </>
                ) : (
                  <p className="text-base px-3 py-2 rounded-md bg-muted/50">{user.username}</p>
                )}
              </div>

              <div className="grid gap-3">
                <Label className="text-base font-semibold">Email</Label>
                <p className="text-base px-3 py-2 rounded-md bg-muted/50">{user.email}</p>
              </div>

              <div className="grid gap-3">
                <Label className="text-base font-semibold">Role</Label>
                <div>
                  <Badge variant={user.role === "admin" ? "default" : "secondary"}>
                    {user.role}
                  </Badge>
                </div>
              </div>

              <div className="grid gap-3">
                <Label className="text-base font-semibold">Provider</Label>
                <div>
                  <Badge variant="outline" className="text-sm">{user.provider}</Badge>
                </div>
              </div>

              <div className="grid gap-3">
                <Label className="text-base font-semibold">Account Status</Label>
                <div className="flex gap-2">
                  <Badge variant={user.is_verified ? "default" : "secondary"} className="text-sm">
                    {user.is_verified ? "Verified" : "Not Verified"}
                  </Badge>
                  <Badge variant={user.is_active ? "default" : "destructive"} className="text-sm">
                    {user.is_active ? "Active" : "Inactive"}
                  </Badge>
                </div>
              </div>

              <div className="grid gap-3">
                <Label className="text-base font-semibold">Member Since</Label>
                <p className="text-base px-3 py-2 rounded-md bg-muted/50">{formatDate(user.created_at)}</p>
              </div>

              <Separator className="my-6" />

              {isEditing ? (
                <div className="flex gap-2 pt-2">
                  <Button type="submit" disabled={updating} size="lg">
                    {updating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    <Save className="mr-2 h-4 w-4" />
                    Save Changes
                  </Button>
                  <Button type="button" variant="outline" size="lg" onClick={handleCancel} disabled={updating}>
                    Cancel
                  </Button>
                </div>
              ) : (
                <Button type="button" size="lg" onClick={() => setIsEditing(true)}>
                  Edit Profile
                </Button>
              )}
            </form>
          </CardContent>
        </Card>

        {user.provider === "local" && (
          <Card className="border-2">
            <CardHeader className="border-b bg-muted/50">
              <CardTitle className="text-2xl">Security</CardTitle>
              <CardDescription>Manage your password and security settings</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-lg border-2 bg-muted/20">
                  <div>
                    <p className="font-semibold text-base">Password</p>
                    <p className="text-sm text-muted-foreground">
                      Change your account password
                    </p>
                  </div>
                  <ChangePasswordDialog />
                </div>
              </div>
            </CardContent>
          </Card>
        )}
        </div>
      </div>
    </div>
  )
}
