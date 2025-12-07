# Changelog - Chat Feature Improvements

## [v0.0.2] - 2025-12-05

### ✨ New Features

#### 1. **Chat Header với User Info & Logout**
- ✅ Hiển thị thông tin user đang đăng nhập
- ✅ Button đăng xuất với confirmation
- ✅ Theme toggle button (dark/light mode)
- ✅ Modern header design

#### 2. **Typing Animation**
- ✅ Loading indicator khi AI đang trả lời
- ✅ Animated dots bouncing effect
- ✅ Smooth transitions

#### 3. **Conversation Management**
- ✅ **Messages đồng bộ với conversation**: Sửa lỗi messages không được lưu vào conversation
- ✅ **Auto-generate title**: Tự động tạo title từ tin nhắn đầu tiên
- ✅ **Delete conversation**: Xóa cuộc trò chuyện với UI feedback
- ✅ **Persist to localStorage**: Lưu tất cả conversations, reload không mất dữ liệu

#### 4. **Enhanced Chat UI**
- ✅ Timestamp cho mỗi tin nhắn
- ✅ Improved message bubbles với shadow
- ✅ User messages: Primary color background
- ✅ AI messages: Plain with timestamp
- ✅ Better spacing và padding
- ✅ Smooth scroll to bottom
- ✅ Responsive design

#### 5. **Keyboard Shortcuts**
- ✅ **Enter**: Gửi tin nhắn
- ✅ **Shift + Enter**: Xuống dòng
- ✅ **Ctrl/Cmd + Enter**: Gửi tin nhắn (alternative)
- ✅ Tooltip hints cho user

#### 6. **Better UX**
- ✅ Loading spinner trong send button khi đang gửi
- ✅ Disable input khi đang loading
- ✅ Auto-resize textarea (max 120px)
- ✅ Empty state với instructions
- ✅ Smooth animations (fade-in, scale)
- ✅ Better error handling

### 🐛 Bug Fixes

1. **Messages State Management**
   - Trước: Messages state riêng biệt, không đồng bộ với conversation
   - Sau: Messages được lưu trực tiếp vào conversation.messages

2. **Conversation Switching**
   - Trước: Chuyển conversation nhưng messages vẫn giữ nguyên
   - Sau: Messages cập nhật đúng theo conversation được chọn

3. **Data Persistence**
   - Trước: Reload page mất hết dữ liệu
   - Sau: Tất cả conversations được lưu trong localStorage

4. **Delete Functionality**
   - Trước: Delete conversation chưa được implement
   - Sau: Hoàn toàn functional với edge cases handling

### 📁 New Files Created

```
src/components/
├── chat-header.tsx         # Header component với user info & logout
├── typing-indicator.tsx    # Loading animation component
└── theme-toggle.tsx        # Updated with next-themes
```

### 🔄 Updated Files

```
src/pages/
└── chat.tsx               # Complete rewrite với state management

src/components/
├── chat-window.tsx        # Added header, keyboard shortcuts, better UI
└── chat-sidebar.tsx       # No changes needed
```

### 🎨 UI/UX Improvements

1. **Better Visual Hierarchy**
   - Clear separation giữa header, messages, và input
   - Consistent spacing và padding
   - Better color contrast

2. **Animations**
   - Fade in cho messages mới
   - Smooth scroll
   - Button hover effects
   - Loading states

3. **Accessibility**
   - Keyboard shortcuts
   - Clear button states
   - Tooltips và hints
   - Proper ARIA labels

### 🚀 Performance

- Efficient state updates
- Proper React memoization points
- LocalStorage debouncing
- Optimized re-renders

### 📝 Technical Details

**State Management:**
```typescript
- Conversations stored in localStorage với key "uit-ai-conversations"
- Auto-save on every conversation update
- Auto-load on mount
- Date serialization handled properly
```

**Message Flow:**
```
User types → handleSendMessage() → Update conversation state → 
LocalStorage save → Simulate AI response → Update conversation again
```

### 🎯 What's Next?

Để kết nối với backend AI thật:

1. Cấu hình `.env`:
```env
VITE_API_URL=http://localhost:8000
```

2. Implement API call trong `chat.tsx`:
```typescript
const response = await fetch(`${API_URL}/api/chat`, {
  method: 'POST',
  body: JSON.stringify({ message: content, conversationId }),
})
```

3. Replace mock response với real AI response

---

## Testing

```bash
# Development
pnpm dev

# Production build
pnpm build
pnpm preview
```

## Demo Credentials

- Username: `test`
- Password: `test`
