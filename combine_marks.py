import pandas as pd
import numpy as np
import os
from pathlib import Path

def process_student_marks(uploads_folder="uploads", output_filename="students_marks.xlsx"):
    try:
        file_paths = {
            'minor1': os.path.join(uploads_folder, "minor1.xlsx"),
            'minor2': os.path.join(uploads_folder, "minor2.xlsx"),
            'final': os.path.join(uploads_folder, "final.xlsx"),
            'assignment': os.path.join(uploads_folder, "assignment.xlsx"),
        }

        # Check files
        for key, path in file_paths.items():
            if not os.path.exists(path):
                return False, f"Missing file: {key}.xlsx"

        # Load DataFrames
        dfs = {key: pd.read_excel(path) for key, path in file_paths.items()}
        for df in dfs.values():
            df.columns = df.columns.str.strip()

        # Validate columns
        required = ['S.No', 'Roll No.', 'Student Name', 'Total']
        for col in required:
            if col not in dfs['minor1'].columns:
                return False, f"Missing column '{col}' in minor1.xlsx"

        result_df = dfs['minor1'][required].copy()
        result_df.rename(columns={'Total': 'minor1'}, inplace=True)

        # Merge each component
        merge_fields = {
            'minor2': 'Total',
            'final': 'Total',
            'assignment': 'Assignment',
        }

        for key, total_col in merge_fields.items():
            df = dfs[key]
            if total_col not in df.columns:
                return False, f"Missing column '{total_col}' in {key}.xlsx"
            temp = df[required[:-1] + [total_col]].copy()
            temp.rename(columns={total_col: key}, inplace=True)
            result_df = pd.merge(result_df, temp, on=['S.No', 'Roll No.', 'Student Name'], how='left')

        # Replace NaNs
        for col in ['minor1', 'minor2', 'final', 'assignment']:
            result_df[col] = result_df[col].fillna(0)

        # Calculate Total
        result_df['Total'] = np.round(
            np.maximum(result_df['minor1'], result_df['minor2']) +
            result_df['final'] +
            result_df['assignment']
        ).astype(int)

        # Reorder
        final_columns = ['S.No', 'Roll No.', 'Student Name', 'minor1', 'minor2', 'final', 'assignment', 'Total']
        result_df = result_df[final_columns]

        # Save
        output_path = os.path.join(uploads_folder, output_filename)
        result_df.to_excel(output_path, index=False)

        return True, result_df

    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, str(e)
