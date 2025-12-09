# UIT AI Assistant - Browser Extension

Extension hỗ trợ sync cookies từ các trang web của UIT (DAA, Portal, E-Learning) để sử dụng cho các tính năng tra cứu điểm, thời khóa biểu.

## 🚀 Features

- ✅ Sync cookies từ DAA (daa.uit.edu.vn)
- ✅ Sync cookies từ Portal (student.uit.edu.vn)
- ✅ Sync cookies từ E-Learning (elearning.uit.edu.vn)
- ✅ Auto-detect login status
- ✅ Secure cookie transmission đến backend
- ✅ Beautiful UI với Svelte 5 + TailwindCSS
- ✅ Dark mode support

## 📦 Tech Stack

- **Svelte 5** - Reactive UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **webextension-polyfill** - Cross-browser compatibility

## 🛠️ Development

### Prerequisites

- Node.js >= 18
- pnpm (hoặc npm/yarn)

### Install Dependencies

```bash
cd frontend/extension
pnpm install
```

### Build Extension

**Development mode (with watch):**
```bash
pnpm dev
```

**Production build:**
```bash
pnpm build
```

Build output sẽ nằm trong folder `dist/`.

### Load Extension vào Chrome

1. Build extension: `pnpm build`
2. Mở Chrome và vào `chrome://extensions`
3. Bật **Developer mode** (góc trên bên phải)
4. Click **Load unpacked**
5. Chọn folder `frontend/extension/dist`

Extension sẽ xuất hiện trong thanh toolbar.

## 📁 Project Structure

```
frontend/extension/
├── public/
│   ├── manifest.json          # Extension manifest (Manifest V3)
│   └── icon*.png              # Extension icons
├── src/
│   ├── background/
│   │   ├── index.ts           # Background service worker
│   │   └── cookie-manager.ts  # Cookie extraction logic
│   ├── popup/
│   │   └── components/        # Svelte UI components
│   ├── stores/
│   │   └── cookie.svelte.ts   # Svelte 5 stores (state management)
│   ├── lib/
│   │   ├── api-client.ts      # Backend API calls
│   │   ├── storage.ts         # Chrome storage wrapper
│   │   └── logger.ts          # Logging utility
│   ├── types/
│   │   └── index.ts           # TypeScript type definitions
│   ├── App.svelte             # Main popup component
│   └── main.ts                # Entry point
├── vite.config.ts             # Vite config
├── tailwind.config.js         # TailwindCSS config
└── package.json
```

## 🔧 Usage

### 1. Login to UIT Sites

Trước khi sync cookies, hãy đăng nhập vào các trang web:
- DAA: https://daa.uit.edu.vn
- Portal: https://student.uit.edu.vn
- E-Learning: https://elearning.uit.edu.vn

### 2. Open Extension Popup

Click vào icon extension trên toolbar Chrome.

### 3. Sync Cookies

- **Sync từng source**: Click nút "Sync DAA", "Sync Portal", hoặc "Sync E-Learning"
- **Sync tất cả**: Click "Sync All Enabled Sources"

### 4. Toggle Sources

Bật/tắt từng source bằng toggle switch bên cạnh tên source.

## 🔐 Security

- Cookies được truyền qua HTTPS
- Cookies được lưu trong **Redis với TTL** (không lưu trong MongoDB)
- Cần **auth token** từ web app để sync cookies
- Extension chỉ có quyền đọc cookies từ các domain cụ thể

## 🐛 Troubleshooting

### Extension không load được

**Giải pháp:**
1. Check console errors: Right-click extension icon → Inspect popup
2. Rebuild: `pnpm build`
3. Reload extension: Click reload icon trong chrome://extensions

### Sync failed: "No auth token found"

**Nguyên nhân:** Extension chưa có auth token từ web app.

**Giải pháp:**
1. Login vào web app (http://localhost:8080)
2. Web app sẽ tự động gửi auth token cho extension
3. Thử sync lại

### Sync failed: "Not logged in to DAA"

**Nguyên nhân:** Chưa đăng nhập vào DAA.

**Giải pháp:**
1. Mở tab mới: https://daa.uit.edu.vn
2. Đăng nhập
3. Quay lại extension và sync

### Backend connection failed

**Nguyên nhân:** Backend chưa chạy hoặc URL sai.

**Giải pháp:**
1. Check backend đang chạy: http://localhost:8080/api/health
2. Check CORS config trong backend
3. Check `VITE_BACKEND_URL` trong `.env`

## 🔗 Backend Integration

Extension gọi backend API endpoint:

```
POST /api/sync-daa-cookie
Headers:
  Authorization: Bearer <auth_token>
  Content-Type: application/json
Body:
  {
    "source": "daa" | "portal" | "elearning",
    "cookie": "cookie_string_here"
  }
```

Backend cần implement endpoint này để nhận cookies và lưu vào Redis.

## 📝 TODO

- [ ] Thay placeholder icons bằng icons thật
- [ ] Implement auto-sync khi cookie thay đổi
- [ ] Add settings page cho cấu hình
- [ ] Support Firefox extension
- [ ] Add notification khi cookie gần expire
- [ ] Implement cookie encryption trước khi gửi backend

## 📄 License

MIT
