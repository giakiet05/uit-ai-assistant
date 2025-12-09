import { useRef, useState, useEffect } from "react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Upload, Trash2, Loader2 } from "lucide-react"
import { useUploadAvatar, useDeleteAvatar } from "@/hooks/useAvatar"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"

interface AvatarUploadProps {
  avatarUrl?: string
  username: string
  onAvatarChange?: () => void
}

export function AvatarUpload({ avatarUrl, username, onAvatarChange }: AvatarUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [previewUrl, setPreviewUrl] = useState<string | undefined>(avatarUrl)
  const { uploadAvatar, loading: uploading } = useUploadAvatar()
  const { deleteAvatar, loading: deleting } = useDeleteAvatar()

  // Sync previewUrl with avatarUrl prop changes
  useEffect(() => {
    setPreviewUrl(avatarUrl)
  }, [avatarUrl])

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.type.startsWith("image/")) {
      alert("Please select an image file")
      return
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert("File size must be less than 5MB")
      return
    }

    try {
      const imageData = await uploadAvatar(file)
      if (imageData) {
        setPreviewUrl(imageData.url)
        onAvatarChange?.()
      }
    } catch (error) {
      console.error("Upload failed:", error)
    }

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  const handleDelete = async () => {
    console.log("🗑️ Delete avatar called")
    try {
      const success = await deleteAvatar()
      console.log("✅ Delete result:", success)
      if (success) {
        setPreviewUrl(undefined)
        // Small delay to ensure DB is updated
        await new Promise(resolve => setTimeout(resolve, 500))
        onAvatarChange?.()
      }
    } catch (error) {
      console.error("❌ Delete failed:", error)
    }
  }

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2)
  }

  const isLoading = uploading || deleting

  return (
    <div className="flex flex-col items-center gap-4">
      <Avatar className="h-24 w-24">
        <AvatarImage src={previewUrl} alt={username} />
        <AvatarFallback className="text-2xl">{getInitials(username)}</AvatarFallback>
      </Avatar>

      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleUploadClick}
          disabled={isLoading}
        >
          {uploading ? (
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
          ) : (
            <Upload className="h-4 w-4 mr-2" />
          )}
          Upload
        </Button>

        {previewUrl && (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                disabled={isLoading}
              >
                {deleting ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <Trash2 className="h-4 w-4 mr-2" />
                )}
                Remove
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete Avatar</AlertDialogTitle>
                <AlertDialogDescription>
                  Are you sure you want to delete your avatar? This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleDelete}>Delete</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileSelect}
        className="hidden"
      />
    </div>
  )
}
