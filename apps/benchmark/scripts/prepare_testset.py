"""
Prepare test set from regulation_test.xlsx for RAG evaluation.

This script:
1. Reads the regulation_test.xlsx file
2. Filters questions relevant to students (based on document whitelist)
3. Transforms to evaluation format (question + ground_truth)
4. Generates full and sample test sets
"""

import json
from pathlib import Path
import pandas as pd


STUDENT_RELEVANT_DOCUMENTS = [
    "QUY CHẾ ĐÀO TẠO THEO HỌC CHẾ TÍN CHỈ CHO HỆ ĐẠI HỌC CHÍNH QUY CỦA TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN",
    "QUY CHẾ Văn bằng, chứng chỉ của Trường Đại học Công nghệ Thông tin",
    "QUY CHẾ ĐÀO TẠO TỪ XA TRÌNH ĐỘ ĐẠI HỌC CỦA TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN",
    "Về khoá luận tốt nghiệp cho đào tạo bậc đại học hệ chính quy",
    "QUY ĐỊNH ĐÀO TẠO NGOẠI NGỮ ĐỐI VỚI HỆ ĐẠI HỌC CHÍNH QUY CỦA TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN",
    "QUY ĐỊNH DẠY VÀ HỌC THEO PHƯƠNG THỨC TRỰC TUYẾN VÀ PHƯƠNG THỨC KẾT HỢP CỦA TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN",
    "QUY ĐỊNH ĐÀO TẠO CHƯƠNG TRÌNH TÀI NĂNG",
    "QUY ĐỊNH ĐÀO TẠO CHƯƠNG TRÌNH TIÊN TIẾN",
    "QUY ĐỊNH ĐÀO TẠO CHƯƠNG TRÌNH CHẤT LƯỢNG CAO",
    "QUY ĐỊNH Tổ chức thi các môn học hệ đại học chính quy của Trường Đại học Công nghệ Thông tin",
    "QUY ĐỊNH TẠM THỜI VỀ ĐÀO TẠO LIÊN THÔNG TỪ TRÌNH ĐỘ ĐẠI HỌC LÊN TRÌNH ĐỘ THẠC SĨ HỆ CHÍNH QUY",
    "QUY ĐỊNH về việc tổ chức dạy – học ngoài giờ hành chính đối với các học phần trong chương trình đào tạo đại học chính quy của Trường Đại học Công nghệ Thông tin",
    "Thay đổi quy trình nộp khóa luận tốt nghiệp sau khi bảo vệ trước hội đồng",
]


def load_regulation_test(xlsx_path: Path) -> pd.DataFrame:
    """Load and validate regulation test dataset."""
    print(f"Loading dataset from {xlsx_path}")
    df = pd.read_excel(xlsx_path)

    print(f"Total questions loaded: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")

    return df


def filter_student_relevant(df: pd.DataFrame) -> pd.DataFrame:
    """Filter questions relevant to students based on document whitelist."""
    print("\nFiltering student-relevant questions...")

    filtered_df = df[df['document'].isin(STUDENT_RELEVANT_DOCUMENTS)].copy()

    print(f"Questions after filtering: {len(filtered_df)}")
    print(f"Filtered out: {len(df) - len(filtered_df)} questions")

    print("\nDocument distribution:")
    for doc, count in filtered_df['document'].value_counts().items():
        print(f"  - {doc[:60]}... : {count} questions")

    return filtered_df


def transform_to_eval_format(df: pd.DataFrame) -> list[dict]:
    """Transform to evaluation format: question + ground_truth."""
    print("\nTransforming to evaluation format...")

    test_set = []
    for idx, row in df.iterrows():
        item = {
            "id": f"reg_{idx:04d}",
            "question": row['question'],
            "ground_truth": row['abstractive answer'],
            "metadata": {
                "article": row['article'],
                "document": row['document'],
                "question_type": "yes_no" if pd.notna(row['yes/no']) else "open",
                "extractive_answer": row['extractive answer'],
            }
        }
        test_set.append(item)

    print(f"Transformed {len(test_set)} questions")

    yes_no_count = sum(1 for item in test_set if item['metadata']['question_type'] == 'yes_no')
    open_count = len(test_set) - yes_no_count
    print(f"  - Yes/No questions: {yes_no_count}")
    print(f"  - Open questions: {open_count}")

    return test_set


def create_stratified_sample(df: pd.DataFrame, sample_size: int = 200) -> pd.DataFrame:
    """Create stratified sample based on document distribution."""
    print(f"\nCreating stratified sample of {sample_size} questions...")

    samples_per_doc = min(5, sample_size // df['document'].nunique())

    sample_df = df.groupby('document', group_keys=False).apply(
        lambda x: x.sample(min(len(x), samples_per_doc), random_state=42)
    )

    if len(sample_df) < sample_size:
        remaining = sample_size - len(sample_df)
        extra_samples = df.drop(sample_df.index).sample(
            min(remaining, len(df) - len(sample_df)),
            random_state=42
        )
        sample_df = pd.concat([sample_df, extra_samples])
    elif len(sample_df) > sample_size:
        sample_df = sample_df.sample(sample_size, random_state=42)

    print(f"Sample size: {len(sample_df)}")
    print("\nSample document distribution:")
    for doc, count in sample_df['document'].value_counts().items():
        print(f"  - {doc[:60]}... : {count} questions")

    return sample_df


def save_test_set(test_set: list[dict], output_path: Path):
    """Save test set to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(test_set, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(test_set)} questions to {output_path}")


def main():
    project_root = Path(__file__).parent.parent.parent.parent
    xlsx_path = project_root / "docs" / "regulation_test.xlsx"
    data_dir = Path(__file__).parent.parent / "data"

    df = load_regulation_test(xlsx_path)

    filtered_df = filter_student_relevant(df)

    full_test_set = transform_to_eval_format(filtered_df)
    save_test_set(
        full_test_set,
        data_dir / "regulation_test_full.json"
    )

    sample_df = create_stratified_sample(filtered_df, sample_size=200)
    sample_test_set = transform_to_eval_format(sample_df)
    save_test_set(
        sample_test_set,
        data_dir / "regulation_test_sample.json"
    )

    print("\n" + "="*60)
    print("Test set preparation completed!")
    print("="*60)
    print(f"Full test set: {len(full_test_set)} questions")
    print(f"Sample test set: {len(sample_test_set)} questions")
    print(f"\nYou can adjust STUDENT_RELEVANT_DOCUMENTS in this script")
    print(f"to filter different documents if needed.")


if __name__ == "__main__":
    main()
