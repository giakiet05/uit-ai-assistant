def clean_daa_content(content: str) -> str:
    """Strategy 2: Remove template/navigation content using patterns"""
    lines = content.split('\n')
    cleaned_lines = []
    skip_section = False

    # Patterns to identify template content
    skip_patterns = [
        'Skip to content', 'Skip to navigation', 'Navigation menu',
        'Tìm kiếm', 'Đăng Nhập', 'Liên kết', 'Back to top',
        '--------- Liên kết website -------', 'Website trường',
        'PHÒNG ĐÀO TẠO ĐẠI HỌC', 'Khu phố 34, Phường Linh Xuân'
    ]

    # Navigation menu indicators
    nav_indicators = [
        '* [Home]', '* [Giới thiệu]', '* [Thông báo]',
        '* [Quy định - Hướng dẫn]', '* [Kế hoạch năm]',
        '* [Chương trình đào tạo]', '* [Lịch]'
    ]

    for line in lines:
        line = line.strip()

        # Skip empty lines at the beginning
        if not line and not cleaned_lines:
            continue

        # Check if this line starts a section to skip
        if any(pattern in line for pattern in skip_patterns):
            skip_section = True
            continue

        # Check for navigation menu items
        if any(nav in line for nav in nav_indicators):
            skip_section = True
            continue

        # Check if we've reached the main content (starts with heading)
        if line.startswith('# ') and 'Thông báo' in line:
            skip_section = False
            cleaned_lines.append(line)
            continue

        # Check for other content indicators that end the template
        if line.startswith('## ') and any(word in line.lower() for word in ['tìm kiếm', 'đăng nhập', 'liên kết', 'trang']):
            skip_section = True
            continue

        # If we're not skipping and have some content, add the line
        if not skip_section and line:
            cleaned_lines.append(line)

        # Stop skipping after "Back to top" or contact info
        if 'Back to top' in line or 'Email:' in line:
            break

    # Remove pagination and related articles from the end
    final_lines = []
    for line in cleaned_lines:
        if 'Bài viết liên quan' in line or 'Trang' in line and '[2]' in line:
            break
        final_lines.append(line)

    return '\n'.join(final_lines).strip()

