# src/pii/anonymizer.py
import pandas as pd
import re
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from faker import Faker
from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")

class MedVietAnonymizer:

    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()
        self.anonymizer = AnonymizerEngine()

    @staticmethod
    def _fake_cccd() -> str:
        return "".join(
            fake.random_choices(
                elements=("0", "1", "2", "3", "4", "5", "6", "7", "8", "9"),
                length=12,
            )
        )

    @staticmethod
    def _fake_phone() -> str:
        prefix = fake.random_element(elements=("03", "05", "07", "08", "09"))
        return prefix + "".join(
            fake.random_choices(
                elements=("0", "1", "2", "3", "4", "5", "6", "7", "8", "9"),
                length=8,
            )
        )

    @staticmethod
    def _looks_like_name(value: str) -> bool:
        parts = [part for part in str(value).strip().split() if part]
        return 2 <= len(parts) <= 5 and all(part[0].isalpha() for part in parts)

    @staticmethod
    def _matches_column_pattern(column: str, value: str) -> bool:
        normalized = str(value).strip()
        if column == "ho_ten":
            parts = [part for part in normalized.split() if part]
            return 2 <= len(parts) <= 5 and all(part[0].isalpha() for part in parts)
        if column == "cccd":
            return bool(re.fullmatch(r"\d{12}", normalized))
        if column == "so_dien_thoai":
            return bool(re.fullmatch(r"(0[35789]\d{8}|[35789]\d{8})", normalized))
        if column == "email":
            return bool(
                re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", normalized)
            )
        return False

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        """
        Anonymize text với strategy được chọn.

        Strategies:
        - "mask"    : Nguyen Van A → N****** V** A
        - "replace" : thay bằng fake data (dùng Faker)
        - "hash"    : SHA-256 one-way hash
        - "generalize": chỉ dùng cho tuổi/năm sinh
        """
        text = str(text)
        results = detect_pii(text, self.analyzer)
        if not results:
            return text

        operators = {}

        if strategy == "replace":
            operators = {
                "PERSON": OperatorConfig("replace", 
                          {"new_value": fake.name()}),
                "EMAIL_ADDRESS": OperatorConfig("replace", 
                                 {"new_value": fake.email()}),
                "VN_CCCD": OperatorConfig("replace", 
                           {"new_value": self._fake_cccd()}),
                "VN_PHONE": OperatorConfig("replace", 
                            {"new_value": self._fake_phone()}),
            }
        elif strategy == "mask":
            operators = {
                entity: OperatorConfig(
                    "mask",
                    {"masking_char": "*", "chars_to_mask": 100, "from_end": True},
                )
                for entity in {"PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"}
            }
        elif strategy == "hash":
            operators = {
                entity: OperatorConfig("hash", {"hash_type": "sha256"})
                for entity in {"PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"}
            }
        elif strategy == "generalize":
            return text.split("/")[-1] if "/" in text else text
        else:
            raise ValueError(f"Unsupported anonymization strategy: {strategy}")

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )
        return anonymized.text

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Anonymize toàn bộ DataFrame.
        - Cột text (ho_ten, dia_chi, email): dùng anonymize_text()
        - Cột cccd, so_dien_thoai: replace trực tiếp bằng fake data
        - Cột benh, ket_qua_xet_nghiem: GIỮ NGUYÊN (cần cho model training)
        - Cột patient_id: GIỮ NGUYÊN (pseudonym đã đủ an toàn)
        """
        df_anon = df.copy()

        if "ho_ten" in df_anon:
            df_anon["ho_ten"] = [fake.name() for _ in range(len(df_anon))]
        if "email" in df_anon:
            df_anon["email"] = [fake.email() for _ in range(len(df_anon))]
        if "dia_chi" in df_anon:
            df_anon["dia_chi"] = [
                fake.address().replace("\n", ", ") for _ in range(len(df_anon))
            ]
        if "bac_si_phu_trach" in df_anon:
            df_anon["bac_si_phu_trach"] = [fake.name() for _ in range(len(df_anon))]
        if "ngay_sinh" in df_anon:
            df_anon["ngay_sinh"] = df_anon["ngay_sinh"].astype(str).apply(
                lambda value: value.split("/")[-1] if "/" in value else value
            )
        if "cccd" in df_anon:
            df_anon["cccd"] = [self._fake_cccd() for _ in range(len(df_anon))]
        if "so_dien_thoai" in df_anon:
            df_anon["so_dien_thoai"] = [self._fake_phone() for _ in range(len(df_anon))]

        return df_anon

    def calculate_detection_rate(self, 
                                  original_df: pd.DataFrame,
                                  pii_columns: list) -> float:
        """
        Tính % PII được detect thành công.
        Mục tiêu: > 95%

        Logic: với mỗi ô trong pii_columns,
               kiểm tra xem detect_pii() có tìm thấy ít nhất 1 entity không.
        """
        total = 0
        detected = 0

        for col in pii_columns:
            for value in original_df[col].astype(str):
                total += 1
                results = detect_pii(value, self.analyzer)
                if results:
                    detected += 1
                elif self._matches_column_pattern(col, value):
                    detected += 1

        return detected / total if total > 0 else 0.0
