# --- Configuration Paths ---
import os

ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
RAW_DATA_DIR = os.path.join(ROOT_DIR, 'data', 'raw', 'daa')
downloads_path = os.path.join(os.getcwd(), "my_downloads")  # Custom download path

URL_GROUPS = {
    "daa": [
        "https://daa.uit.edu.vn/"
        # "https://daa.uit.edu.vn/01-quyet-dinh-ve-viec-ban-hanh-quy-che-dao-tao-theo-hoc-che-tin-chi"
        # "https://daa.uit.edu.vn/thong-bao-chung",
        # "https://daa.uit.edu.vn/quydinh",
        # "https://daa.uit.edu.vn/qui-che-qui-dinh-qui-trinh",
        # "https://daa.uit.edu.vn/quy-che-quy-dinh-dao-tao-dai-hoc-cua-dhqg-hcm",
        # "https://daa.uit.edu.vn/quy-che-quy-dinh-dao-tao-dai-hoc-cua-bo-gddt",
        # "https://daa.uit.edu.vn/sites/daa/files/uploads/53_qd_dhcntt_19_2_2019scan.pdf",
        # "https://daa.uit.edu.vn/content/quy-dinh-dao-tao-ngan-han",
        # "https://daa.uit.edu.vn/content/quy-trinh-danh-cho-can-bo-giang-day",
        # "https://daa.uit.edu.vn/mot-so-quy-trinh-danh-cho-sinh-vien",
        # "https://daa.uit.edu.vn/thongbao/huong-dan-tra-cuu-va-xac-minh-van-bang-tot-nghiep-dai-hoc",
        # "https://daa.uit.edu.vn/content/huong-dan-sinh-vien-dai-hoc-he-chinh-quy-thuc-hien-cac-quy-dinh-ve-chuan-qua-trinh-va-chuan",
        # "https://daa.uit.edu.vn/thongbao/huong-dan-trien-khai-day-va-hoc-qua-mang-trong-thoi-gian-phong-chong-dich-covid-19",
        # "https://daa.uit.edu.vn/kehoachnam",
        # "https://daa.uit.edu.vn/content/cong-thong-tin-dao-tao",
        # "https://daa.uit.edu.vn/content/chuc-nang-nhiem-vu-cua-phong-dao-tao-dai-hoc"
        #
        #

    ],
    # "course": [
    #     "https://course.uit.edu.vn/course-category/khoa-hoc-may-tinh",
    #     "https://course.uit.edu.vn/course-category/mang-may-tinh"
    # ],
    # # Sau này thêm nhóm mới cực dễ!
    # "tuyensinh": [
    #     "https://tuyensinh.uit.edu.vn/thong-tin-tuyen-sinh-dai-hoc"
    # ]
}