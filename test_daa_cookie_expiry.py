#!/usr/bin/env python3
"""
Test DAA cookie expiry behavior.

Mục đích: Xác định DAA có absolute timeout hay chỉ idle timeout.

Cách dùng:
1. Login vào DAA trên browser
2. Copy cookie SESS... từ DevTools
3. Chạy script này với cookie đó
4. Script sẽ ping DAA mỗi 5 phút
5. Theo dõi xem cookie có expire sau X ngày không

Nếu cookie vẫn valid sau 7-30 ngày → chỉ có idle timeout → keep-alive works!
Nếu cookie expire đúng X ngày dù có ping → có absolute timeout → keep-alive fails
"""

import asyncio
import httpx
from datetime import datetime, timedelta
import json


class CookieExpiryTester:
    def __init__(self, cookie: str):
        """
        Args:
            cookie: Full cookie string từ browser
                    Example: "SSESS123=abc; student_id=21520001"
        """
        self.cookie = cookie
        self.test_url = "https://daa.uit.edu.vn"
        self.ping_interval = 5 * 60  # 5 phút
        self.results = []
        self.start_time = datetime.now()

    async def check_cookie_valid(self) -> bool:
        """Ping DAA để check cookie còn valid không."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.test_url,
                    headers={"Cookie": self.cookie},
                    follow_redirects=True,
                    timeout=30.0
                )

                # Check nếu redirect về login page
                if "user/login" in response.url.path:
                    return False

                # Check nếu có text "đăng xuất" (logged in)
                if "đăng xuất" in response.text.lower() or "logout" in response.text.lower():
                    return True

                return False

        except Exception as e:
            print(f"❌ Error checking cookie: {e}")
            return False

    async def ping_loop(self):
        """Loop: ping mỗi 5 phút để keep cookie alive."""
        test_count = 0

        while True:
            test_count += 1
            elapsed = datetime.now() - self.start_time

            print(f"\n{'='*60}")
            print(f"Test #{test_count} - Elapsed: {elapsed}")
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")

            is_valid = await self.check_cookie_valid()

            result = {
                "test_number": test_count,
                "timestamp": datetime.now().isoformat(),
                "elapsed_seconds": elapsed.total_seconds(),
                "cookie_valid": is_valid
            }

            self.results.append(result)

            if is_valid:
                print("✅ Cookie VALID - Session still active")
                print(f"   Cookie đã tồn tại: {elapsed}")
            else:
                print("❌ Cookie EXPIRED - Session died")
                print(f"   Cookie chết sau: {elapsed}")

                # Cookie expired → kết luận
                self.print_conclusion()
                break

            # Save results
            self.save_results()

            # Sleep 5 phút
            print(f"\n⏳ Sleeping {self.ping_interval}s until next ping...")
            await asyncio.sleep(self.ping_interval)

    def save_results(self):
        """Save kết quả ra file."""
        with open("daa_cookie_test_results.json", "w") as f:
            json.dump({
                "start_time": self.start_time.isoformat(),
                "current_time": datetime.now().isoformat(),
                "total_tests": len(self.results),
                "results": self.results
            }, f, indent=2)

    def print_conclusion(self):
        """In kết luận sau khi cookie expire."""
        elapsed = datetime.now() - self.start_time
        days = elapsed.days
        hours = elapsed.seconds // 3600

        print("\n" + "="*60)
        print("🎯 KẾT LUẬN")
        print("="*60)
        print(f"Cookie expired sau: {days} ngày {hours} giờ")
        print(f"Số lần ping: {len(self.results)}")

        if days >= 7:
            print("\n✅ KẾT LUẬN: DAA có ABSOLUTE TIMEOUT")
            print(f"   → Cookie expire sau ~{days} ngày bất kể có ping")
            print(f"   → Keep-alive ping KHÔNG HIỆU QUẢ")
            print(f"   → PHẢI dùng credentials để re-login")
        elif days >= 1:
            print("\n⚠️  KẾT LUẬN: Cần test thêm")
            print(f"   → Cookie expire sau {days} ngày")
            print(f"   → Có thể là absolute hoặc idle timeout")
        else:
            print("\n⚠️  KẾT LUẬN: Cookie expire quá nhanh")
            print(f"   → Có thể cookie đã gần expire khi bắt đầu test")
            print(f"   → Hoặc có vấn đề khác")

        print("="*60)


async def main():
    print("="*60)
    print("DAA Cookie Expiry Test")
    print("="*60)

    # Nhập cookie
    print("\n📝 Hướng dẫn lấy cookie:")
    print("1. Mở Chrome/Firefox")
    print("2. Vào https://daa.uit.edu.vn và đăng nhập")
    print("3. Mở DevTools (F12) → Tab Application → Cookies")
    print("4. Copy TẤT CẢ cookies thành chuỗi: 'name1=value1; name2=value2'")
    print()

    cookie = input("Paste cookie vào đây: ").strip()

    if not cookie:
        print("❌ Cookie không được để trống!")
        return

    print("\n🚀 Bắt đầu test...")
    print("⏰ Script sẽ ping DAA mỗi 5 phút")
    print("📊 Kết quả lưu vào: daa_cookie_test_results.json")
    print("\n💡 TIP: Chạy script này trong tmux/screen để không bị ngắt")
    print()

    tester = CookieExpiryTester(cookie)
    await tester.ping_loop()


if __name__ == "__main__":
    asyncio.run(main())
