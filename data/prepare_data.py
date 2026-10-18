
from itertools import islice
from pathlib import Path

import pandas as pd
from datasets import load_dataset


DATASET_ID = "Shifat2110724169/job-market-intel-corpus"
OUTPUT_PATH = Path("data/jobs.csv")
SAMPLE_SIZE = 5_000

KEEP_COLUMNS = [
    "source_job_id",
    "title_en",
    "source_name",
    "posting_date",
    "job_status",
    "employment_type",
    "location_raw",
    "salary_currency",
    "salary_annual_min_usd",
    "salary_annual_max_usd",
    "required_skills_text",
    "requirements",
    "description_en",
    "job_url",
    "data_quality_score",
]


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    dataset = load_dataset(
        DATASET_ID,
        split="train",
        streaming=True,
    )

    rows = list(islice(dataset, SAMPLE_SIZE))
    df = pd.DataFrame(rows)

    available_columns = [
        col for col in KEEP_COLUMNS if col in df.columns
    ]
    df = df[available_columns]

    if "job_status" in df.columns:
        df = df[
            df["job_status"].eq("active")
            | df["job_status"].isna()
        ]

    if "title_en" in df.columns:
        df = df[
            df["title_en"].notna()
            & df["title_en"].astype(str).str.strip().ne("")
        ]

    df = df.drop_duplicates(subset=["source_job_id"])

    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"Saved {len(df)} jobs to {OUTPUT_PATH}")
    print(f"Columns: {df.columns.tolist()}")
    print(df.head(3).to_string())


if __name__ == "__main__":
    main()
