# Debug Guide - Chat & Theme Issues

## 🐛 Vấn đề đã sửa

### 1. Theme Toggle không hoạt động
**Nguyên nhân:** ThemeProvider thiếu `storageKey` và `disableTransitionOnChange`

**Đã sửa trong:** `src/App.tsx`
```typescript
<ThemeProvider
  attribute="class"
  defaultTheme="dark"
  enableSystem
  storageKey="uit-ai-theme"  // ✅ Added
  disableTransitionOnChange   // ✅ Added
>
```

### 2. Gửi chat không hiển thị
**Có thể do:** State management hoặc localStorage issues

**Đã thêm debug logs** trong:
- `src/pages/chat.tsx` - handleSendMessage
- `src/components/chat-window.tsx` - useEffect

## 🔍 Cách Debug

### Bước 1: Xóa LocalStorage cũ
Mở DevTools Console và chạy:
```javascript
localStorage.clear()
location.reload()
```

### Bước 2: Kiểm tra Console Logs

Khi gửi message, bạn sẽ thấy logs theo thứ tự:

```
📤 handleSendMessage called with: "hello"
Current activeConversationId: "1234567890"
Current conversations: [...]
📝 Created user message: {...}
Previous conversations: [...]
✅ Updated conversation: {...}
New conversations state: [...]
💬 ChatWindow received messages: [...]
💬 Messages count: 1
🤖 Adding AI response: {...}
💬 ChatWindow received messages: [...]
💬 Messages count: 2
```

### Bước 3: Kiểm tra State

**Nếu không thấy logs "📤":**
- Button không gọi onSendMessage
- Check handleSubmit trong ChatWindow

**Nếu thấy "❌ No active conversation ID!":**
- State initialization failed
- Check useEffect load conversations

**Nếu conversations update nhưng messages không hiển thị:**
- Props passing issue
- Check ChatWindow props

### Bước 4: Kiểm tra Theme

**Test theme toggle:**
1. Click nút Sun/Moon icon
2. Mở DevTools → Application → LocalStorage
3. Xem key `uit-ai-theme` có thay đổi không
4. Xem class="dark" trên html element

**Nếu theme không đổi:**
```javascript
// Run in console
localStorage.getItem('uit-ai-theme')
document.documentElement.classList.contains('dark')
```

## 🚀 Test Lại

```bash
# Clear old data
rm -rf node_modules/.vite
pnpm dev
```

### Test Checklist:

- [ ] Login với test/test
- [ ] Gửi message → Thấy user message
- [ ] Đợi 1.5s → Thấy AI response
- [ ] Click theme toggle → Theme đổi
- [ ] Reload page → Messages vẫn còn
- [ ] Tạo new conversation
- [ ] Delete conversation
- [ ] Switch giữa conversations

## 🔧 Fix Thủ Công

### Nếu vẫn lỗi gửi chat:

**Option 1: Reset localStorage**
```javascript
localStorage.removeItem('uit-ai-conversations')
localStorage.removeItem('uit-ai-theme')
location.reload()
```

**Option 2: Check React DevTools**
1. Cài React DevTools extension
2. Vào Components tab
3. Tìm ChatPage component
4. Xem state: conversations, activeConversationId
5. Gửi message và xem state có update không

**Option 3: Hard reload**
```
Ctrl + Shift + R (Windows/Linux)
Cmd + Shift + R (Mac)
```

### Nếu theme không đổi:

**Option 1: Force theme**
```javascript
document.documentElement.classList.toggle('dark')
```

**Option 2: Check CSS**
- Mở DevTools → Elements
- Xem html tag có class="dark" không
- Xem CSS variables có apply không

## 📝 Common Issues

### Issue: "Cannot read property 'messages' of undefined"
**Fix:** activeConversation is null
```typescript
// Already fixed in code:
messages={activeConversation?.messages || []}
```

### Issue: Messages duplicate sau reload
**Fix:** UseEffect dependency issue
```typescript
// Already fixed with isInitialized flag
useEffect(() => {
  if (isInitialized && conversations.length > 0) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations))
  }
}, [conversations, isInitialized])
```

### Issue: Theme flashes on load
**Fix:** Added disableTransitionOnChange
```typescript
<ThemeProvider disableTransitionOnChange>
```

## 🎯 Expected Behavior

### Send Message Flow:
1. User types → clicks send
2. handleSendMessage called
3. User message added to state
4. ChatWindow re-renders with new message
5. Message appears in UI
6. After 1.5s → AI response added
7. ChatWindow re-renders again
8. AI message appears

### Theme Toggle Flow:
1. Click theme button
2. useTheme().setTheme() called
3. next-themes updates localStorage
4. next-themes toggles html class
5. CSS applies new theme colors
6. UI updates immediately

## 🆘 Nếu vẫn lỗi

Gửi thông tin sau:
1. Console logs (tất cả logs từ 📤 đến 🤖)
2. React DevTools screenshot của ChatPage state
3. Network tab (nếu có API calls)
4. LocalStorage contents:
   - uit-ai-conversations
   - uit-ai-theme
   - user
   - token
