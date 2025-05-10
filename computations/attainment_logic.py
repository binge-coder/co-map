import pandas as pd
import re
import os

UPLOAD_FOLDER = "uploads"


def parse_range(r):
    try:
        return tuple(map(int, str(r).strip().split('-')))
    except:
        raise ValueError(f"Invalid range format: {r}. Use format like '40-60'.")


def clean_question_key(q):
    return re.sub(r'[^a-zA-Z0-9]', '', str(q).lower())


def process_tool(tool_name, qp_filename, marks_filename, co_thresholds, co_levels):
    qp_path = os.path.join(UPLOAD_FOLDER, qp_filename)
    marks_path = os.path.join(UPLOAD_FOLDER, marks_filename)

    try:
        qp_df = pd.read_excel(qp_path)
        marks_df = pd.read_excel(marks_path)
    except FileNotFoundError as e:
        raise RuntimeError(f"Missing required file: {e.filename}")
    except Exception as e:
        raise RuntimeError(f"Error loading Excel files for {tool_name}: {e}")

    # Normalize column names
    marks_df.columns = marks_df.columns.str.strip()
    required_cols = ['Roll No.', 'Student Name']
    for col in required_cols:
        if col not in marks_df.columns:
            raise ValueError(f"{tool_name}: Missing required column: {col}")

    # Step A: Map questions to COs
    question_to_co = {}
    co_max_marks = {}
    question_mapping_table = []

    for _, row in qp_df.iterrows():
        q_raw = str(row['Question Number'])
        q_key = clean_question_key(q_raw)
        co = f"CO{int(row['CO'])}"
        marks = float(row['Marks'])
        question_to_co[q_key] = co
        co_max_marks[co] = co_max_marks.get(co, 0) + marks
        question_mapping_table.append({'Question Number': q_raw, 'CO': co})

    # Step B & C: Compute CO-wise marks and % for each student
    student_data = []

    for _, row in marks_df.iterrows():
        student = {
            'Roll No.': row.get('Roll No.', 'Unknown'),
            'Student Name': row.get('Student Name', 'Unknown')
        }
        co_scores = {}

        for q_col in marks_df.columns:
            q_key = clean_question_key(q_col)
            if q_key in question_to_co:
                co = question_to_co[q_key]
                try:
                    score = row.get(q_col, 0)
                    score = 0 if pd.isna(score) else float(score)
                    co_scores[co] = co_scores.get(co, 0) + score
                except Exception as e:
                    print(f"{tool_name}: Score parsing error for {q_col} in {student['Roll No.']}: {e}")

        for co in sorted(co_max_marks):
            obtained = float(co_scores.get(co, 0) or 0)
            total = co_max_marks[co]
            percent = (obtained / total) * 100 if total > 0 else 0
            student[f"{co} Marks"] = round(obtained, 2)
            student[f"{co} %"] = round(percent, 2)

        student_data.append(student)

    student_df = pd.DataFrame(student_data)
    student_df.fillna(0, inplace=True)

    # Step D–F: Threshold check and Attainment level calculation
    attainment_summary = []
    total_students = len(student_df)
    co_used = set(question_to_co.values())

    for co in sorted(co_max_marks):
        if co not in co_used:
            continue
        threshold = co_thresholds.get(co, 50)
        above_threshold = student_df[student_df[f"{co} %"] >= threshold]
        percent_above = (len(above_threshold) / total_students) * 100

        level_range = co_levels[co]
        if level_range['level1'][0] <= percent_above <= level_range['level1'][1]:
            level = 1
        elif level_range['level2'][0] <= percent_above <= level_range['level2'][1]:
            level = 2
        elif level_range['level3'][0] <= percent_above <= level_range['level3'][1]:
            level = 3
        else:
            level = 0

        attainment_summary.append({
            'CO': co,
            'Threshold': threshold,
            '% ≥ Threshold': round(percent_above, 2),
            'Attainment Level': level
        })

    summary_df = pd.DataFrame(attainment_summary)

    return {
        'tool': tool_name,
        'student_results': student_df,
        'attainment_summary': summary_df,
        'question_mapping': pd.DataFrame(question_mapping_table)
    }


def compute_attainment():
    tools_output = []

    # Load CO config
    config_path = os.path.join(UPLOAD_FOLDER, 'co_config.xlsx')
    try:
        config_df = pd.read_excel(config_path)
    except FileNotFoundError:
        raise RuntimeError("co_config.xlsx not found in uploads/ folder.")

    # Parse config
    co_thresholds = {}
    co_levels = {}

    for _, row in config_df.iterrows():
        co = str(row['CO'])
        co_thresholds[co] = float(row['Threshold (%)'])
        co_levels[co] = {
            'level1': parse_range(row['Level 1 Range']),
            'level2': parse_range(row['Level 2 Range']),
            'level3': parse_range(row['Level 3 Range'])
        }

    # Process Mid1 and Mid2
    mid1 = process_tool("Minor1", "m1_question_paper.xlsx", "minor1.xlsx", co_thresholds, co_levels)
    mid2 = process_tool("Minor2", "m2_question_paper.xlsx", "minor2.xlsx", co_thresholds, co_levels)
    final = process_tool("Final Exam", "final_question_paper.xlsx", "final.xlsx", co_thresholds, co_levels)

    tools_output.extend([mid1, mid2, final])

    # Merge Mid1 and Mid2 into "Mid" by taking max level per CO
    co_levels_mid = {}
    for row in mid1['attainment_summary'].to_dict('records'):
        co = row['CO']
        co_levels_mid[co] = row['Attainment Level']

    for row in mid2['attainment_summary'].to_dict('records'):
        co = row['CO']
        prev = co_levels_mid.get(co, 0)
        co_levels_mid[co] = max(prev, row['Attainment Level'])

    # Final levels from TEE
    co_levels_final = {row['CO']: row['Attainment Level'] for row in final['attainment_summary'].to_dict('records')}

    # Tool weights (assignment excluded from CO attainment)
    TOOL_WEIGHTS = {"Mid": 30, "Final Exam": 50}

    # Final CO attainment computation
    final_attainment = []
    all_cos = set(co_levels_mid) | set(co_levels_final)

    for co in sorted(all_cos):
        levels = []
        weights = []

        if co in co_levels_mid:
            levels.append(co_levels_mid[co])
            weights.append(TOOL_WEIGHTS['Mid'])

        if co in co_levels_final:
            levels.append(co_levels_final[co])
            weights.append(TOOL_WEIGHTS['Final Exam'])

        total_weight = sum(weights)
        weighted_avg = sum(l * w for l, w in zip(levels, weights)) / total_weight if total_weight else 0

        final_attainment.append({
            'CO': co,
            'Final Attainment': round(weighted_avg, 2)
        })

    final_df = pd.DataFrame(final_attainment)

    # Step G: Weighted Direct Attainment Details
    step_g_details = []
    for co in sorted(all_cos):
        mid_level = co_levels_mid.get(co, 0)
        final_level = co_levels_final.get(co, 0)

        mid_weight_norm = TOOL_WEIGHTS['Mid'] / (TOOL_WEIGHTS['Mid'] + TOOL_WEIGHTS['Final Exam']) if co in co_levels_mid and co in co_levels_final else (1 if co in co_levels_mid else 0)
        final_weight_norm = TOOL_WEIGHTS['Final Exam'] / (TOOL_WEIGHTS['Mid'] + TOOL_WEIGHTS['Final Exam']) if co in co_levels_mid and co in co_levels_final else (1 if co in co_levels_final else 0)

        weighted_attainment = round(mid_level * mid_weight_norm + final_level * final_weight_norm, 2)

        step_g_details.append({
            'CO': co,
            'Mid Level': mid_level,
            'Final Level': final_level,
            'Normalized Mid Weight': round(mid_weight_norm, 2),
            'Normalized Final Weight': round(final_weight_norm, 2),
            'Weighted Direct Attainment': weighted_attainment
        })

    return {
        'tools': tools_output,
        'final_attainment': final_df,
        'step_g_details': step_g_details
    }
