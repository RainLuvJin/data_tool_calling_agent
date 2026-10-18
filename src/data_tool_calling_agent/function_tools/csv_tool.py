from pathlib import Path
import pandas as pd
# inspect_dataset：先学会读取 CSV 并检查数据。

def inspect_dataset(df, action="head", n=5):

    if action == "columns":
        return df.columns.tolist()

    elif action == "head":
        return df.head(n)

    elif action == "random":
        return df.sample(n=min(n, len(df)))

    else:
        raise ValueError(f"Unsupported action: {action}")


# filter_jobs：学习如何把自然语言需求转换成筛选参数。

def filter_jobs(
    df,
    location=None,
    skill=None,
    employment_type=None,
    min_salary_usd=None,
):
    # 初始状态：每一行都暂时符合条件
    mask = pd.Series(True, index=df.index)

    # 1. 按地点筛选
    if location:
        mask &= df["location_raw"].str.contains(
            location, case=False, na=False, regex=False
        )

    # 2. 按技能筛选
    if skill:
        text = (
            df["title_en"].fillna("") + " "
            + df["required_skills_text"].fillna("") + " "
            + df["description_en"].fillna("")
        )

        mask &= text.str.contains(
            skill, case=False, na=False, regex=False
        )

    # 3. 按工作类型筛选
    if employment_type:
        mask &= df["employment_type"].str.contains(
            employment_type, case=False, na=False, regex=False
        )

    # 4. 按最低年薪筛选
    if min_salary_usd is not None:
        salary = pd.to_numeric(
            df["salary_annual_min_usd"], errors="coerce"
        )
        mask &= salary >= min_salary_usd

    return df.loc[mask].copy()

# analyze_salary：学习如何做统计，并处理缺失薪资。

def analyze_salary(df, group_by=None):
    """
    统计年薪数据。

    参数：
        df: 完整的岗位 DataFrame，不要传只包含前 20 行的预览数据。
        group_by: 可选的分组字段，例如 "employment_type" 或 "location_raw"。

    返回：
        一个字典，包含整体统计和可选的分组统计。
    """

    # 1. 检查必要的薪资字段是否存在
    salary_columns = [
        "salary_annual_min_usd",
        "salary_annual_max_usd",
    ]

    missing_columns = [
        col for col in salary_columns if col not in df.columns
    ]

    # 如果缺少必要字段，就明确报错，而不是静默返回错误结果
    if missing_columns:
        raise ValueError(f"Missing salary columns: {missing_columns}")

    # 2. 如果指定了分组字段，检查它是否存在
    if group_by is not None and group_by not in df.columns:
        raise ValueError(f"Unknown grouping column: {group_by}")

    # 3. 复制薪资列，避免修改调用者传入的原始 DataFrame
    salary_df = df[salary_columns].copy()

    # 4. 转换为数值；空字符串、无效文本等会变成 NaN
    for col in salary_columns:
        salary_df[col] = pd.to_numeric(
            salary_df[col], errors="coerce"
        )

    # 5. 标记每条记录是否至少有一个有效薪资数值
    # 例如：只有最低薪资有效、最高薪资缺失，也算一条有效记录
    salary_df["_has_salary"] = salary_df[
        salary_columns
    ].notna().any(axis=1)

    # 6. 计算整体统计结果
    overall = {
        "total_records": len(salary_df),
        "valid_salary_records": int(
            salary_df["_has_salary"].sum()
        ),
        "valid_min_salary_records": int(
            salary_df["salary_annual_min_usd"].count()
        ),
        "valid_max_salary_records": int(
            salary_df["salary_annual_max_usd"].count()
        ),
        "min_salary_mean": salary_df[
            "salary_annual_min_usd"
        ].mean(),
        "min_salary_median": salary_df[
            "salary_annual_min_usd"
        ].median(),
        "min_salary_lowest": salary_df[
            "salary_annual_min_usd"
        ].min(),
        "min_salary_highest": salary_df[
            "salary_annual_min_usd"
        ].max(),
        "max_salary_mean": salary_df[
            "salary_annual_max_usd"
        ].mean(),
        "max_salary_median": salary_df[
            "salary_annual_max_usd"
        ].median(),
        "max_salary_lowest": salary_df[
            "salary_annual_max_usd"
        ].min(),
        "max_salary_highest": salary_df[
            "salary_annual_max_usd"
        ].max(),
    }

    # 7. 先组装返回结果
    result = {"overall": overall}

    # 8. 如果没有指定分组字段，只返回整体统计
    if group_by is None:
        return result

    # 9. 把分组字段放进临时 DataFrame
    # 这样不会修改原始 df
    grouped_df = salary_df.copy()
    grouped_df[group_by] = df[group_by]

    # 10. 按指定字段分组，并计算每组的统计指标
    grouped_stats = (
        grouped_df
        .groupby(group_by, dropna=False)
        .agg(
            valid_salary_records=("_has_salary", "sum"),
            valid_min_salary_records=(
                "salary_annual_min_usd", "count"
            ),
            valid_max_salary_records=(
                "salary_annual_max_usd", "count"
            ),
            min_salary_mean=("salary_annual_min_usd", "mean"),
            min_salary_median=("salary_annual_min_usd", "median"),
            min_salary_lowest=("salary_annual_min_usd", "min"),
            min_salary_highest=("salary_annual_min_usd", "max"),
            max_salary_mean=("salary_annual_max_usd", "mean"),
            max_salary_median=("salary_annual_max_usd", "median"),
            max_salary_lowest=("salary_annual_max_usd", "min"),
            max_salary_highest=("salary_annual_max_usd", "max"),
        )
        .reset_index()
    )

    # 11. 把分组统计表放入结果字典
    result["group_by"] = group_by
    result["groups"] = grouped_stats

    return result