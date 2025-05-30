from fpdf import FPDF
import pandas as pd
import os
import matplotlib.pyplot as plt
from datetime import datetime
from computations.attainment_logic import compute_attainment
# ADD - at the top of the file, after the imports
# Import clean_question_key function from attainment_logic if not already imported
try:
    from computations.attainment_logic import clean_question_key
except ImportError:
    # Define the function locally if import fails
    import re
    def clean_question_key(q):
        return re.sub(r'[^a-zA-Z0-9]', '', str(q).lower())


class ReportGenerator:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)
        
    def generate_comprehensive_report(self):
        """Generate a comprehensive report with question papers, marks and bell curves for all exams."""
        # Add cover page
        self.add_cover_page()
        
        # Process each exam type
        self.process_exam("Sessional 1", "m1_question_paper.xlsx", "minor1.xlsx", "minor1_bell.png")
        self.process_exam("Sessional 2", "m2_question_paper.xlsx", "minor2.xlsx", "minor2_bell.png")
        self.process_exam("Final Exam", "final_question_paper.xlsx", "final.xlsx", "final_bell.png")
        
        # Add new sections for overall student marks and bell curve
        self.add_students_overall_marks_page()
        self.add_students_overall_bell_curve_page()
        
        # Add CO attainment tables after final exam
        self.add_co_attainment_tables()

        # Add additional attainment pages
        self.add_additional_attainment_pages()
        
        # Generate report filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"comprehensive_report_{timestamp}.pdf"
        report_path = os.path.join(self.upload_folder, report_filename)
        
        # Save the PDF
        self.pdf.output(report_path)
        return report_filename
    
    def add_cover_page(self):
        """Add a cover page to the report."""
        self.pdf.add_page()
        self.pdf.set_font("Arial", "B", 24)
        
        # Add title
        self.pdf.cell(0, 60, "", ln=True)
        self.pdf.cell(0, 20, "Comprehensive Course Assessment Report", ln=True, align="C")
        
        # Add subtitle
        self.pdf.set_font("Arial", "I", 16)
        self.pdf.cell(0, 15, "CO Attainment Analysis", ln=True, align="C")
        
        # Add date
        self.pdf.set_font("Arial", "", 12)
        self.pdf.cell(0, 30, "", ln=True)
        self.pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%B %d, %Y')}", ln=True, align="C")
        
        # Add footer note
        self.pdf.set_y(-40)
        self.pdf.set_font("Arial", "I", 10)
        self.pdf.cell(0, 10, "This report includes question papers, student marks, and statistical analysis", align="C")
        self.pdf.set_y(-30)
        self.pdf.cell(0, 10, "for all examination components of the course.", align="C")

    # Fixed indentation for process_exam method
    def process_exam(self, exam_name, question_paper_file, marks_file, bell_curve_file):
        """Process a single exam by adding its question paper, marks and bell curve."""
        # Check if all required files exist
        question_paper_path = os.path.join(self.upload_folder, question_paper_file)
        marks_path = os.path.join(self.upload_folder, marks_file)
        bell_curve_path = os.path.join(self.upload_folder, bell_curve_file)
        
        # Define Bloom's taxonomy chart file based on exam type
        blooms_chart_file = ""
        if "Sessional 1" in exam_name:
            blooms_chart_file = "m1_question_paper_blooms_pie.png"
        elif "Sessional 2" in exam_name:
            blooms_chart_file = "m2_question_paper_blooms_pie.png"
        elif "Final Exam" in exam_name:
            blooms_chart_file = "final_question_paper_blooms_pie.png"
        
        if not all(os.path.exists(path) for path in [question_paper_path, marks_path, bell_curve_path]):
            self.add_missing_files_page(exam_name, question_paper_file, marks_file, bell_curve_file)
            return
        
        # Add question paper
        self.add_question_paper_page(exam_name, question_paper_path)
        
        # Add Bloom's taxonomy distribution chart after question paper
        if blooms_chart_file:
            self.add_blooms_taxonomy_page(exam_name, blooms_chart_file)
        
        # Add marks table
        self.add_marks_page(exam_name, marks_path)
        
        # Add CO-wise marks and percentages table
        self.add_co_wise_marks_page(exam_name, question_paper_path, marks_path)
        
        # Add bell curve
        self.add_bell_curve_page(exam_name, bell_curve_path)
    
    def add_missing_files_page(self, exam_name, question_paper_file, marks_file, bell_curve_file):
        """Add a page indicating missing files for an exam."""
        self.pdf.add_page()
        self.pdf.set_font("Arial", "B", 16)
        self.pdf.cell(0, 20, f"{exam_name} - Missing Files", ln=True, align="C")
        
        self.pdf.set_font("Arial", "", 12)
        self.pdf.cell(0, 10, "The following files are missing:", ln=True)
        
        files_to_check = [
            (question_paper_file, "Question Paper"),
            (marks_file, "Student Marks"),
            (bell_curve_file, "Bell Curve")
        ]
        
        for file, description in files_to_check:
            file_path = os.path.join(self.upload_folder, file)
            status = "Available" if os.path.exists(file_path) else "Missing"
            self.pdf.cell(0, 10, f"{description}: {file} - {status}", ln=True)
    
    def add_question_paper_page(self, exam_name, question_paper_path):
        """Add question paper to the report."""
        try:
            df = pd.read_excel(question_paper_path)
            
            self.pdf.add_page()
            self.pdf.set_font("Arial", "B", 16)
            self.pdf.cell(0, 15, f"{exam_name} - Question Paper", ln=True, align="C")
            
            # Add a note about CO mapping
            self.pdf.set_font("Arial", "I", 10)
            self.pdf.cell(0, 10, "Questions with Course Outcome (CO) mapping", ln=True)
            
            # Create table for question paper
            self.pdf.set_font("Arial", "B", 10)
            
            # Table header
            col_widths = [20, 90, 20, 20, 40]  # Width for each column
            headers = ["Q.No.", "Question", "Marks", "CO", "Bloom's Level"]
            
            # Draw header
            self.pdf.set_fill_color(200, 220, 255)
            for i, header in enumerate(headers):
                self.pdf.cell(col_widths[i], 10, header, border=1, fill=True, align="C")
            self.pdf.ln()
            
            # Draw data rows
            self.pdf.set_font("Arial", "", 9)
            for _, row in df.iterrows():
                # Get data from each column, handle potential NaN values
                q_no = str(row.get("Question Number", ""))
                question = str(row.get("Question", ""))
                marks = str(row.get("Marks", ""))
                co = str(row.get("CO", ""))
                bloom = str(row.get("Bloom's Taxonomy", ""))
                
                # Calculate needed height for wrapping text in question column
                text_height = max(10, self.calculate_text_height(question, col_widths[1]))
                
                # Print each cell
                self.pdf.cell(col_widths[0], text_height, q_no, border=1, align="C")
                
                # Multi-line cell for question text
                x_pos = self.pdf.get_x()
                y_pos = self.pdf.get_y()
                self.pdf.multi_cell(col_widths[1], 10, question, border=1)
                self.pdf.set_xy(x_pos + col_widths[1], y_pos)
                
                self.pdf.cell(col_widths[2], text_height, marks, border=1, align="C")
                self.pdf.cell(col_widths[3], text_height, co, border=1, align="C")
                self.pdf.cell(col_widths[4], text_height, bloom, border=1, align="C")
                self.pdf.ln()
        
        except Exception as e:
            self.pdf.add_page()
            self.pdf.set_font("Arial", "B", 16)
            self.pdf.cell(0, 15, f"{exam_name} - Question Paper", ln=True, align="C")
            self.pdf.set_font("Arial", "", 12)
            self.pdf.cell(0, 10, f"Error processing question paper: {str(e)}", ln=True)
    
    def add_marks_page(self, exam_name, marks_path):
        """Add student marks to the report."""
        try:
            # Read the Excel file
            df = pd.read_excel(marks_path)
            
            # Create a new page for marks
            self.pdf.add_page()
            self.pdf.set_font("Arial", "B", 16)
            self.pdf.cell(0, 15, f"{exam_name} - Student Marks", ln=True, align="C")
            
            # Find the Total column
            total_column = None
            possible_total_names = ['Total', 'Total Marks', 'Grand Total', 'Final Score']
            
            for col_name in possible_total_names:
                if col_name in df.columns:
                    total_column = col_name
                    break
            
            # Add summary statistics if Total column exists
            if total_column:
                self.pdf.set_font("Arial", "I", 10)
                total_marks = df[total_column].dropna()
                stats_text = (
                    f"Number of Students: {len(total_marks)}, "
                    f"Average: {total_marks.mean():.2f}, "
                    f"Highest: {total_marks.max():.2f}, "
                    f"Lowest: {total_marks.min():.2f}"
                )
                self.pdf.cell(0, 10, stats_text, ln=True)
            
            # Simplify column selection: take first 3 columns for student info + total column if found
            student_columns = df.columns[:3].tolist()
            column_headers = ["S.No", "Roll No.", "Student Name"]  # Fixed headers for first 3 columns
            
            # Add the total column if found
            if total_column:
                student_columns.append(total_column)
                column_headers.append("Total")
            
            filtered_df = df[student_columns]
                
            # Define fixed column widths
            col_widths = [20, 40, 80, 30]  # S.No, Roll No., Student Name, Total
            
            # Get total width of the table
            total_width = sum(col_widths[:len(column_headers)])
            
            # Calculate centering offset (to center the table on page)
            page_width = self.pdf.w - 2 * self.pdf.l_margin
            left_margin = self.pdf.l_margin + (page_width - total_width) / 2
            
            # Fixed number of students per page - as requested
            students_per_first_page = 29
            students_per_other_page = 30
            
            # Set up pagination variables
            total_students = len(filtered_df)
            current_student = 0
            first_page = True
            
            while current_student < total_students:
                # If not on the first iteration and we've filled a page, add a new page
                if current_student > 0:
                    self.pdf.add_page()
                    self.pdf.set_font("Arial", "B", 16)
                    self.pdf.cell(0, 15, f"{exam_name} - Student Marks (Continued)", ln=True, align="C")
                    first_page = False
                
                # Determine how many students to show on this page
                students_this_page = students_per_first_page if first_page else students_per_other_page
                end_student = min(current_student + students_this_page, total_students)
                
                # Draw header
                self.pdf.set_font("Arial", "B", 9)
                self.pdf.set_fill_color(200, 220, 255)
                
                # Set position to center the table
                self.pdf.set_x(left_margin)
                
                # Draw the header row
                for i, header in enumerate(column_headers):
                    self.pdf.cell(col_widths[i], 10, str(header), border=1, fill=True, align="C")
                self.pdf.ln()
                
                # Draw data rows
                self.pdf.set_font("Arial", "", 8)
                for i in range(current_student, end_student):
                    # Center the row
                    self.pdf.set_x(left_margin)
                    
                    row = filtered_df.iloc[i]
                    for j, col in enumerate(filtered_df.columns):
                        value = str(row[col]) if pd.notna(row[col]) else ""
                        # Center align all cells
                        self.pdf.cell(col_widths[j], 8, value, border=1, align="C")
                    self.pdf.ln()
                                            
                # Move to next batch
                current_student = end_student
        
        except Exception as e:
            self.pdf.add_page() 
            self.pdf.set_font("Arial", "B", 16)
            self.pdf.cell(0, 15, f"{exam_name} - Student Marks", ln=True, align="C")
            self.pdf.set_font("Arial", "", 12)
            self.pdf.cell(0, 10, f"Error processing marks: {str(e)}", ln=True)

    # Fixed indentation for add_co_wise_marks_page method 
    def add_co_wise_marks_page(self, exam_name, question_paper_path, marks_path):
        """Add CO-wise marks and percentages table for each student."""
        try:
            # Read Excel files
            qp_df = pd.read_excel(question_paper_path)
            marks_df = pd.read_excel(marks_path)
            
            # Create a new page
            self.pdf.add_page()
            self.pdf.set_font("Arial", "B", 16)
            self.pdf.cell(0, 15, f"{exam_name} - CO-wise Marks and Percentages", ln=True, align="C")
            
            self.pdf.set_font("Arial", "I", 10)
            self.pdf.cell(0, 10, "Step B & C: CO-wise Marks and % per Student", ln=True)
            
            # Normalize column names
            marks_df.columns = marks_df.columns.str.strip()
            
            # Step A: Map questions to COs
            question_to_co = {}
            co_max_marks = {}
            
            for _, row in qp_df.iterrows():
                q_raw = str(row['Question Number'])
                q_key = clean_question_key(q_raw)
                co = f"CO{int(row['CO'])}"
                marks = float(row['Marks'])
                question_to_co[q_key] = co
                co_max_marks[co] = co_max_marks.get(co, 0) + marks
            
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
                            print(f"{exam_name}: Score parsing error for {q_col} in {student['Roll No.']}: {e}")
                
                for co in sorted(co_max_marks):
                    obtained = float(co_scores.get(co, 0) or 0)
                    total = co_max_marks[co]
                    percent = (obtained / total) * 100 if total > 0 else 0
                    student[f"{co} Marks"] = round(obtained, 2)
                    student[f"{co} %"] = round(percent, 2)
                
                student_data.append(student)
            
            student_df = pd.DataFrame(student_data)
            student_df.fillna(0, inplace=True)
            
            # Define column names and widths for the table
            columns = list(student_df.columns)
            
            # Calculate column widths based on number of columns
            base_width = 190 / len(columns)  # 190mm is approximately the usable width in PDF
            col_widths = [base_width] * len(columns)
            
            # Adjust widths for student columns
            if 'Roll No.' in columns:
                roll_index = columns.index('Roll No.')
                col_widths[roll_index] = base_width * 1.0
            
            if 'Student Name' in columns:
                name_index = columns.index('Student Name')
                col_widths[name_index] = base_width * 1.5

            # Reduce width for CO Marks and CO % columns
            for i, col in enumerate(columns):
                if 'CO' in col and ('Marks' in col or '%' in col):
                    col_widths[i] = base_width * 0.9  #Reduce width for CO-related columns
                
            # Draw header
            self.pdf.set_font("Arial", "B", 9)
            self.pdf.set_fill_color(200, 220, 255)
            for i, col in enumerate(columns):
                self.pdf.cell(col_widths[i], 10, str(col), border=1, fill=True, align="C")
            self.pdf.ln()
            
            # Draw data rows
            self.pdf.set_font("Arial", "", 8)
            for _, row in student_df.iterrows():
                for i, col in enumerate(columns):
                    value = str(row[col]) if pd.notna(row[col]) else ""
                    self.pdf.cell(col_widths[i], 8, value, border=1, align="C")
                self.pdf.ln()
        
        except Exception as e:
            self.pdf.add_page()
            self.pdf.set_font("Arial", "B", 16)
            self.pdf.cell(0, 15, f"{exam_name} - CO-wise Marks and Percentages", ln=True, align="C")
            self.pdf.set_font("Arial", "", 12)
            self.pdf.cell(0, 10, f"Error processing CO-wise marks: {str(e)}", ln=True)
    
    def add_bell_curve_page(self, exam_name, bell_curve_path):
        """Add bell curve to the report."""
        try:
            self.pdf.add_page()
            self.pdf.set_font("Arial", "B", 16)
            self.pdf.cell(0, 15, f"{exam_name} - Score Distribution", ln=True, align="C")
            
            # Add description
            self.pdf.set_font("Arial", "I", 10)
            self.pdf.cell(0, 10, "Statistical distribution of student scores", ln=True)
            
            # Calculate optimal image placement
            page_width = self.pdf.w - 2 * self.pdf.l_margin
            image_width = page_width * 0.9  # 90% of page width
            
            # Add the image
            self.pdf.image(bell_curve_path, 
                         x=self.pdf.l_margin + (page_width - image_width) / 2, 
                         y=self.pdf.get_y() + 5,
                         w=image_width)
        
        except Exception as e:
            self.pdf.add_page()
            self.pdf.set_font("Arial", "B", 16) 
            self.pdf.cell(0, 15, f"{exam_name} - Score Distribution", ln=True, align="C")
            self.pdf.set_font("Arial", "", 12)
            self.pdf.cell(0, 10, f"Error adding bell curve: {str(e)}", ln=True)
    
    def add_blooms_taxonomy_page(self, exam_name, blooms_chart_file):
        """Add Bloom's taxonomy distribution chart to the report."""
        blooms_chart_path = os.path.join(self.upload_folder, blooms_chart_file)
        
        if not os.path.exists(blooms_chart_path):
            self._add_missing_file_page(f"{exam_name} - Bloom's Taxonomy Distribution", blooms_chart_file)
            return
        
        try:
            self.pdf.add_page()
            self.pdf.set_font("Arial", "B", 16)
            self.pdf.cell(0, 15, f"{exam_name} - Bloom's Taxonomy Distribution", ln=True, align="C")
            
            # Add description
            self.pdf.set_font("Arial", "I", 10)
            self.pdf.cell(0, 10, "Distribution of questions across Bloom's Taxonomy levels", ln=True)
            
            # Calculate optimal image placement
            page_width = self.pdf.w - 2 * self.pdf.l_margin
            image_width = page_width * 0.9  # 90% of page width
            
            # Add the image
            self.pdf.image(
                blooms_chart_path, 
                x=self.pdf.l_margin + (page_width - image_width) / 2, 
                y=self.pdf.get_y() + 5,
                w=image_width
            )
        
        except Exception as e:
            self.pdf.add_page()
            self.pdf.set_font("Arial", "B", 16) 
            self.pdf.cell(0, 15, f"{exam_name} - Bloom's Taxonomy Distribution", ln=True, align="C")
            self.pdf.set_font("Arial", "", 12)
            self.pdf.cell(0, 10, f"Error adding Bloom's taxonomy chart: {str(e)}", ln=True)
    
    def add_students_overall_marks_page(self):
        """Add students overall marks to the report."""
        students_marks_path = os.path.join(self.upload_folder, "students_marks.xlsx")
        
        if not os.path.exists(students_marks_path):
            self._add_missing_file_page("Students Overall Marks", "students_marks.xlsx")
            return
        
        try:
            # Read the Excel file
            df = pd.read_excel(students_marks_path)
            
            # Create a new page for overall marks
            self.pdf.add_page()
            self.pdf.set_font("Arial", "B", 16)
            self.pdf.cell(0, 15, "Students Overall Marks", ln=True, align="C")
            
            # Find the Total column
            total_column = None
            possible_total_names = ['Total', 'Total Marks', 'Grand Total', 'Final Score', 'Overall Total']
            
            for col_name in possible_total_names:
                if col_name in df.columns:
                    total_column = col_name
                    break
            
            # Add summary statistics if Total column exists
            if total_column:
                self.pdf.set_font("Arial", "I", 10)
                total_marks = df[total_column].dropna()
                stats_text = (
                    f"Number of Students: {len(total_marks)}, "
                    f"Average: {total_marks.mean():.2f}, "
                    f"Highest: {total_marks.max():.2f}, "
                    f"Lowest: {total_marks.min():.2f}"
                )
                self.pdf.cell(0, 10, stats_text, ln=True)
            
            # Simplify column selection: take first 3 columns for student info + total column if found
            student_columns = df.columns[:3].tolist()
            column_headers = ["S.No", "Roll No.", "Student Name"]  # Fixed headers for first 3 columns
            
            # Add the total column if found
            if total_column:
                student_columns.append(total_column)
                column_headers.append("Overall Total")
            
            filtered_df = df[student_columns]
                
            # Define fixed column widths
            col_widths = [20, 40, 80, 30]  # S.No, Roll No., Student Name, Overall Total
            
            # Get total width of the table
            total_width = sum(col_widths[:len(column_headers)])
            
            # Calculate centering offset (to center the table on page)
            page_width = self.pdf.w - 2 * self.pdf.l_margin
            left_margin = self.pdf.l_margin + (page_width - total_width) / 2
            
            # Fixed number of students per page
            students_per_first_page = 29
            students_per_other_page = 30
            
            # Set up pagination variables
            total_students = len(filtered_df)
            current_student = 0
            first_page = True
            
            while current_student < total_students:
                # If not on the first iteration and we've filled a page, add a new page
                if current_student > 0:
                    self.pdf.add_page()
                    self.pdf.set_font("Arial", "B", 16)
                    self.pdf.cell(0, 15, "Students Overall Marks (Continued)", ln=True, align="C")
                    first_page = False
                
                # Determine how many students to show on this page
                students_this_page = students_per_first_page if first_page else students_per_other_page
                end_student = min(current_student + students_this_page, total_students)
                
                # Draw header
                self.pdf.set_font("Arial", "B", 9)
                self.pdf.set_fill_color(200, 220, 255)
                
                # Set position to center the table
                self.pdf.set_x(left_margin)
                
                # Draw the header row
                for i, header in enumerate(column_headers):
                    self.pdf.cell(col_widths[i], 10, str(header), border=1, fill=True, align="C")
                self.pdf.ln()
                
                # Draw data rows
                self.pdf.set_font("Arial", "", 8)
                for i in range(current_student, end_student):
                    # Center the row
                    self.pdf.set_x(left_margin)
                    
                    row = filtered_df.iloc[i]
                    for j, col in enumerate(filtered_df.columns):
                        value = str(row[col]) if pd.notna(row[col]) else ""
                        # Center align all cells
                        self.pdf.cell(col_widths[j], 8, value, border=1, align="C")
                    self.pdf.ln()
                                            
                # Move to next batch
                current_student = end_student
        
        except Exception as e:
            self.pdf.add_page() 
            self.pdf.set_font("Arial", "B", 16)
            self.pdf.cell(0, 15, "Students Overall Marks", ln=True, align="C")
            self.pdf.set_font("Arial", "", 12)
            self.pdf.cell(0, 10, f"Error processing overall marks: {str(e)}", ln=True)
    
    def add_students_overall_bell_curve_page(self):
        """Add students overall marks bell curve to the report."""
        bell_curve_path = os.path.join(self.upload_folder, "students_marks_bell.png")
        
        if not os.path.exists(bell_curve_path):
            self._add_missing_file_page("Students Overall Bell Curve", "students_marks_bell.png")
            return
        
        try:
            self.pdf.add_page()
            self.pdf.set_font("Arial", "B", 16)
            self.pdf.cell(0, 15, "Students Overall Marks - Score Distribution", ln=True, align="C")
            
            # Add description
            self.pdf.set_font("Arial", "I", 10)
            self.pdf.cell(0, 10, "Statistical distribution of overall student scores", ln=True)
            
            # Calculate optimal image placement
            page_width = self.pdf.w - 2 * self.pdf.l_margin
            image_width = page_width * 0.9  # 90% of page width
            
            # Add the image
            self.pdf.image(
                bell_curve_path,
                x=self.pdf.l_margin + (page_width - image_width) / 2,
                y=self.pdf.get_y() + 5,
                w=image_width
            )
        
        except Exception as e:
            self.pdf.add_page()
            self.pdf.set_font("Arial", "B", 16)
            self.pdf.cell(0, 15, "Students Overall Marks - Score Distribution", ln=True, align="C")
            self.pdf.set_font("Arial", "", 12)
            self.pdf.cell(0, 10, f"Error adding overall bell curve: {str(e)}", ln=True)
    
    def add_attainment_charts_page(self):
        """Add both attainment charts to a single page in the report."""
        co_chart_path = os.path.join(self.upload_folder, "final_co_attainment_chart.png")
        po_chart_path = os.path.join(self.upload_folder, "overall_po_pso_attainment_chart.png")
        
        # Check if both files exist
        co_exists = os.path.exists(co_chart_path)
        po_exists = os.path.exists(po_chart_path)
        
        if not co_exists and not po_exists:
            self._add_missing_file_page("Attainment Charts", "final_co_attainment_chart.png and overall_po_pso_attainment_chart.png")
            return
        
        # Create a single page for both charts
        self.pdf.add_page()
        self.pdf.set_font("Arial", "B", 16)
        self.pdf.cell(0, 15, "Attainment Charts", ln=True, align="C")
        
        page_width = self.pdf.w - 2 * self.pdf.l_margin
        image_width = page_width * 0.9  # 90% of page width
        
        # Calculate appropriate height for charts to fit on one page
        # Page height minus margins and title space divided by 2 charts
        available_height = self.pdf.h - 40  # Subtracting title and margins
        image_height = available_height / 2.2  # Leave some space between charts
        
        y_position = self.pdf.get_y() + 5
        
        # Add CO attainment chart
        if co_exists:
            self.pdf.set_font("Arial", "B", 12)
            self.pdf.cell(0, 10, "1. CO Attainment Chart", ln=True)
            
            # Move the image slightly down after the heading
            y_position += 5
            
            self.pdf.image(co_chart_path, 
                        x=self.pdf.l_margin + (page_width - image_width) / 2, 
                        y=y_position,
                        w=image_width,
                        h=image_height)
            
            # Update y position for next chart
            y_position += image_height + 15
        else:
            self.pdf.set_font("Arial", "", 10)
            self.pdf.cell(0, 10, "CO Attainment Chart: File not found", ln=True)
            y_position += 15
        
        # Add PO-PSO attainment chart
        if po_exists:
            self.pdf.set_font("Arial", "B", 12)
            self.pdf.set_y(y_position)
            self.pdf.cell(0, 10, "2. PO-PSO Attainment Chart", ln=True)
            
            self.pdf.image(po_chart_path, 
                        x=self.pdf.l_margin + (page_width - image_width) / 2, 
                        y=self.pdf.get_y() + 5,
                        w=image_width,
                        h=image_height)
        else:
            self.pdf.set_font("Arial", "", 10)
            self.pdf.set_y(y_position)
            self.pdf.cell(0, 10, "PO-PSO Attainment Chart: File not found", ln=True)

    def add_co_attainment_tables(self):
        """Add CO attainment tables to the report."""
        try:
            # Compute attainment data
            attainment_data = compute_attainment()
                   
            # Process each tool's attainment summary (Minor1, Minor2, Final)
            for tool in attainment_data['tools']:
                self.add_tool_attainment_page(tool)
            
            # Add the weighted direct attainment details and final CO attainment on the same page
            self.add_weighted_attainment_page(attainment_data['step_g_details'])
            self.add_final_attainment_table(attainment_data['final_attainment'])
            
            # Optionally, add a separate fancy version of the final attainment page
            # self.add_separate_final_attainment_page(attainment_data['final_attainment'])
        
        except Exception as e:
            self.pdf.add_page()
            self.pdf.set_font("Arial", "B", 16)
            self.pdf.cell(0, 15, "CO Attainment Analysis", ln=True, align="C")
            self.pdf.set_font("Arial", "", 12)
            self.pdf.cell(0, 10, f"Error processing CO attainment data: {str(e)}", ln=True)
    
    def add_tool_attainment_page(self, tool):
        """Add a page for a specific tool's attainment summary."""
        self.pdf.add_page()
        self.pdf.set_font("Arial", "B", 16)
        self.pdf.cell(0, 15, f"{tool['tool']} - CO Attainment Summary", ln=True, align="C")
        
        # Add Question Mapping table
        if 'question_mapping' in tool and not tool['question_mapping'].empty:
            self.pdf.set_font("Arial", "B", 14)
            self.pdf.cell(0, 15, "Question to CO Mapping", ln=True,align="C")
            
            # Create table header
            self.pdf.set_font("Arial", "B", 10)
            col_widths = [60, 60]
            headers = ["Question Number", "Mapped CO"]

            # Calculate the total width of the table and center position
            total_width = sum(col_widths)
            page_width = self.pdf.w - 2 * self.pdf.l_margin
            left_margin = self.pdf.l_margin + (page_width - total_width) / 2
            
            # Draw header
            self.pdf.set_fill_color(200, 220, 255)
            self.pdf.set_x(left_margin)
            for i, header in enumerate(headers):
                self.pdf.cell(col_widths[i], 10, header, border=1, fill=True, align="C")
            self.pdf.ln()
            
            # Draw data rows
            self.pdf.set_font("Arial", "", 10)
            for _, row in tool['question_mapping'].iterrows():
                self.pdf.set_x(left_margin)
                self.pdf.cell(col_widths[0], 10, str(row['Question Number']), border=1, align="C")
                self.pdf.cell(col_widths[1], 10, str(row['CO']), border=1, align="C")
                self.pdf.ln()
            
            self.pdf.ln(5)
        
        # Add Attainment Summary table
        if 'attainment_summary' in tool and not tool['attainment_summary'].empty:
            self.pdf.set_font("Arial", "B", 14)
            self.pdf.cell(0, 15, "CO Attainment Summary", ln=True, align="C")
            
            # Create table header
            self.pdf.set_font("Arial", "B", 10)
            col_widths = [30, 40, 40, 40]
            headers = ["CO", "Threshold (%)", "% >= Threshold", "Attainment Level"]  # Changed '≥' to '>='
            
            # Draw header
            self.pdf.set_fill_color(200, 220, 255)
            self.pdf.set_x(left_margin)
            for i, header in enumerate(headers):
                self.pdf.cell(col_widths[i], 10, header, border=1, fill=True, align="C")
            self.pdf.ln()
            
            # Draw data rows
            self.pdf.set_font("Arial", "", 10)
            for _, row in tool['attainment_summary'].iterrows():
                self.pdf.set_x(left_margin)
                self.pdf.cell(col_widths[0], 10, str(row['CO']), border=1, align="C")
                self.pdf.cell(col_widths[1], 10, str(row['Threshold']), border=1, align="C")
                self.pdf.cell(col_widths[2], 10, str(row['% ≥ Threshold']).replace('≥', '>='), border=1, align="C")  # Replace '≥' with '>='
                self.pdf.cell(col_widths[3], 10, str(row['Attainment Level']), border=1, align="C")
                self.pdf.ln()
    
    def add_weighted_attainment_page(self, step_g_details):
        """Add the weighted direct attainment details table and final attainment table on a single page."""
        self.pdf.add_page()
        self.pdf.set_font("Arial", "B", 16)
        self.pdf.cell(0, 15, "Direct Attainment Analysis", ln=True, align="C")
        
        # --- First section: Weighted Direct Attainment Details ---
        self.pdf.set_font("Arial", "B", 12)
        self.pdf.cell(0, 10, "1. Weighted Direct Attainment Details", ln=True)
        
        self.pdf.set_font("Arial", "I", 10)
        self.pdf.cell(0, 6, "Combining Mid and Final exam results with appropriate weights", ln=True)
        
        # Create table header
        self.pdf.set_font("Arial", "B", 9)
        col_widths = [25, 25, 25, 40, 40, 40]
        headers = ["CO", "Mid Level", "Final Level", "Normalized Mid Weight", "Normalized Final Weight", "Weighted Direct Attainment"]
        
        # Draw header
        self.pdf.set_fill_color(200, 220, 255)
        for i, header in enumerate(headers):
            self.pdf.cell(col_widths[i], 10, header, border=1, fill=True, align="C")
        self.pdf.ln()
        
        # Draw data rows
        self.pdf.set_font("Arial", "", 9)
        for row in step_g_details:
            self.pdf.cell(col_widths[0], 10, str(row['CO']), border=1, align="C")
            self.pdf.cell(col_widths[1], 10, str(row['Mid Level']), border=1, align="C")
            self.pdf.cell(col_widths[2], 10, str(row['Final Level']), border=1, align="C")
            self.pdf.cell(col_widths[3], 10, str(row['Normalized Mid Weight']), border=1, align="C")
            self.pdf.cell(col_widths[4], 10, str(row['Normalized Final Weight']), border=1, align="C")
            self.pdf.cell(col_widths[5], 10, str(row['Weighted Direct Attainment']), border=1, align="C")
            self.pdf.ln()
            
        # Add space between tables
        self.pdf.ln(10)
        
    def add_final_attainment_table(self, final_attainment):
        """Add the final CO attainment table to the same page as weighted attainment."""
        # --- Second section: Direct Attainment Results ---
        self.pdf.set_font("Arial", "B", 12)
        self.pdf.cell(0, 10, "2. Direct Attainment Results", ln=True)
        
        self.pdf.set_font("Arial", "I", 10)
        self.pdf.cell(0, 6, "Final attainment levels for each Course Outcome", ln=True)
        
        # Create table header
        self.pdf.set_font("Arial", "B", 9)
        col_widths = [80, 80]
        headers = ["Course Outcome", "Direct Attainment Level"]
        
        # Calculate centering offset
        page_width = self.pdf.w - 2 * self.pdf.l_margin
        total_width = sum(col_widths)
        left_margin = self.pdf.l_margin + (page_width - total_width) / 2
        
        # Draw header with consistent styling
        self.pdf.set_x(left_margin)
        self.pdf.set_fill_color(200, 220, 255)
        for i, header in enumerate(headers):
            self.pdf.cell(col_widths[i], 10, header, border=1, fill=True, align="C")
        self.pdf.ln()
        
        # Draw data rows with consistent styling
        self.pdf.set_font("Arial", "", 9)
        for _, row in final_attainment.iterrows():
            self.pdf.set_x(left_margin)
            self.pdf.cell(col_widths[0], 10, str(row['CO']), border=1, align="C")
            self.pdf.cell(col_widths[1], 10, str(row['Final Attainment']), border=1, align="C")
            self.pdf.ln()
        
        # Add note about interpretation
        self.pdf.ln(5)
        self.pdf.set_font("Arial", "I", 9)
        self.pdf.set_x(left_margin)
        self.pdf.multi_cell(total_width, 6, 
            "Interpretation: Level 3 (>=2.5) indicates excellent attainment, Level 2 (>=1.5 and <2.5) " +
            "indicates satisfactory attainment, and Level 1 (<1.5) indicates that improvement is needed.", 
            align="L")
    
    def add_separate_final_attainment_page(self, final_attainment):
        """Add the final CO attainment table on a separate page with fancy styling."""
        self.pdf.add_page()
        self.pdf.set_font("Arial", "B", 16)
        
        # Create a special background for final results
        self.pdf.set_fill_color(67, 97, 238)  # Primary blue color from HTML
        self.pdf.rect(10, 10, self.pdf.w - 20, 30, "F")
        self.pdf.set_text_color(255, 255, 255)  # White text
        self.pdf.cell(0, 30, "Direct Attainment Results", ln=True, align="C")
        self.pdf.set_text_color(0, 0, 0)  # Reset to black text
        
        self.pdf.ln(10)
        
        # Create table header
        self.pdf.set_font("Arial", "B", 12)
        col_widths = [80, 80]
        headers = ["Course Outcome", "Direct Attainment Level"]  
        
        # Calculate centering offset
        page_width = self.pdf.w - 2 * self.pdf.l_margin
        total_width = sum(col_widths)
        left_margin = self.pdf.l_margin + (page_width - total_width) / 2
        
        # Draw header with special styling
        self.pdf.set_fill_color(76, 201, 240)  # Success color from HTML
        self.pdf.set_text_color(255, 255, 255)  # White text
        
        self.pdf.set_x(left_margin)
        for i, header in enumerate(headers):
            self.pdf.cell(col_widths[i], 12, header, border=1, fill=True, align="C")
        self.pdf.ln()
        
        # Draw data rows
        self.pdf.set_font("Arial", "B", 11)
        self.pdf.set_text_color(0, 0, 0)  # Reset to black text
        self.pdf.set_fill_color(240, 240, 240)  # Light gray background
        
        for _, row in final_attainment.iterrows():
            self.pdf.set_x(left_margin)
            self.pdf.cell(col_widths[0], 12, str(row['CO']), border=1, fill=True, align="C")
            self.pdf.cell(col_widths[1], 12, str(row['Final Attainment']), border=1, fill=True, align="C")
            self.pdf.ln()
        
        # Add note about interpretation
        self.pdf.ln(10)
        self.pdf.set_font("Arial", "I", 10)
        self.pdf.set_fill_color(255, 243, 224)  # Light warning color
        self.pdf.rect(left_margin, self.pdf.get_y(), total_width, 30, "F")
        self.pdf.set_xy(left_margin, self.pdf.get_y() + 5)
        self.pdf.multi_cell(total_width, 8, 
            "Interpretation: Level 3 (>=2.5) indicates excellent attainment, Level 2 (>=1.5 and <2.5) " +
            "indicates satisfactory attainment, and Level 1 (<1.5) indicates that improvement is needed.", 
            align="C")
    

    def add_additional_attainment_pages(self):
        """Add additional attainment pages for CO-PO mapping and overall attainment."""
        self.add_combined_co_po_direct_page()
        self.add_combined_indirect_attainment_page()
        self.add_combined_overall_final_attainment_page()
        self.add_attainment_charts_page()

    def add_combined_co_po_direct_page(self):
        """Add combined CO-PO mapping matrix and direct attainment mapping on a single page."""
        co_po_file = os.path.join(self.upload_folder, "co_po_mapping_matrix.xlsx")
        direct_file = os.path.join(self.upload_folder, "direct_attainment_mapping.xlsx")
        
        if not os.path.exists(co_po_file) or not os.path.exists(direct_file):
            # If either file is missing, revert to individual pages
            if not os.path.exists(co_po_file):
                self._add_missing_file_page("CO-PO Mapping Matrix", "co_po_mapping_matrix.xlsx")
            if not os.path.exists(direct_file):
                self._add_missing_file_page("Direct Attainment Mapping", "direct_attainment_mapping.xlsx")
            return
            
        try:
            co_po_df = pd.read_excel(co_po_file)
            direct_df = pd.read_excel(direct_file)
            
            # Create a new page
            self.pdf.add_page()
            
            # ----- First section: CO-PO Mapping Matrix -----
            self.pdf.set_font("Arial", "B", 16)
            self.pdf.cell(0, 15, "CO-PO Mapping and Direct Attainment", ln=True, align="C")
            
            # CO-PO Mapping Matrix subtitle
            self.pdf.set_font("Arial", "B", 12)
            self.pdf.cell(0, 10, "1. CO-PO Mapping Matrix", ln=True)
            
            self.pdf.set_font("Arial", "I", 9)
            self.pdf.cell(0, 6, "Correlation between Course Outcomes and Program Outcomes", ln=True)
            
            # Create table for CO-PO mapping
            cols = co_po_df.columns.tolist()
            col_widths = [20]  # Reduced width for CO column
            col_widths.extend([10] * (len(cols) - 1))  # Reduced width for all PO columns
            
            # Draw header
            self.pdf.set_font("Arial", "B", 8)
            self.pdf.set_fill_color(200, 220, 255)
            
            self.pdf.cell(col_widths[0], 8, cols[0], border=1, fill=True, align="C")
            for i, col in enumerate(cols[1:], 1):
                self.pdf.cell(col_widths[i], 8, str(col), border=1, fill=True, align="C")
            self.pdf.ln()
            
            # Draw data rows
            self.pdf.set_font("Arial", "", 8)
            for _, row in co_po_df.iterrows():
                self.pdf.cell(col_widths[0], 8, str(row[cols[0]]), border=1, align="C")
                for i, col in enumerate(cols[1:], 1):
                    value = str(row[col]) if pd.notna(row[col]) else "-"
                    self.pdf.cell(col_widths[i], 8, value, border=1, align="C")
                self.pdf.ln()
            
            # Add some space between tables
            self.pdf.ln(10)
            
            # ----- Second section: Direct Attainment Mapping -----
            self.pdf.set_font("Arial", "B", 12)
            self.pdf.cell(0, 10, "2. Direct Attainment Mapping", ln=True)
            
            self.pdf.set_font("Arial", "I", 9)
            self.pdf.cell(0, 6, "Mapping direct assessment tools to Program Outcomes", ln=True)
            
            # Create table for direct attainment mapping
            cols = direct_df.columns.tolist()
            # Adjust column widths: wider for the 1st column, reduced for others
            col_widths = [30] + [10] * (len(cols) - 1)  # 1st column wider, others reduced
            
            # If col_widths doesn't match number of columns, use default width
            if len(col_widths) != len(cols):
                col_widths = [180 / len(cols)] * len(cols)  # Adjusted total width to 180
            
            # Draw header
            self.pdf.set_font("Arial", "B", 8)
            self.pdf.set_fill_color(200, 220, 255)
            
            for i, col in enumerate(cols):
                self.pdf.cell(col_widths[i], 8, str(col), border=1, fill=True, align="C")
            self.pdf.ln()
            
            # Draw data rows
            self.pdf.set_font("Arial", "", 8)
            for _, row in direct_df.iterrows():
                for i, col in enumerate(cols):
                    value = str(row[col]) if pd.notna(row[col]) else "-"
                    # For description column, use multi_cell if needed
                    if i > 0 and "description" in cols[i].lower():
                        x_pos = self.pdf.get_x()
                        y_pos = self.pdf.get_y()
                        self.pdf.multi_cell(col_widths[i], 8, value, border=1)
                        self.pdf.set_xy(x_pos + col_widths[i], y_pos)
                    else:
                        self.pdf.cell(col_widths[i], 8, value, border=1, align="C")
                self.pdf.ln()
                
        except Exception as e:
            self.pdf.add_page()
            self.pdf.set_font("Arial", "B", 16)
            self.pdf.cell(0, 15, "CO-PO Mapping and Direct Attainment", ln=True, align="C")
            self.pdf.set_font("Arial", "", 12)
            self.pdf.cell(0, 10, f"Error processing data: {str(e)}", ln=True)

    def add_combined_indirect_attainment_page(self):
        """Add combined indirect attainment results and mapping on a single page."""
        results_file = os.path.join(self.upload_folder, "indirect_attainment.xlsx")
        mapping_file = os.path.join(self.upload_folder, "indirect_attainment_mapping.xlsx")
        
        if not os.path.exists(results_file) or not os.path.exists(mapping_file):
            # If either file is missing, revert to individual pages
            if not os.path.exists(results_file):
                self._add_missing_file_page("Indirect Attainment Results", "indirect_attainment.xlsx")
            if not os.path.exists(mapping_file):
                self._add_missing_file_page("Indirect Attainment Mapping", "indirect_attainment_mapping.xlsx")
            return
            
        try:
            results_df = pd.read_excel(results_file)
            mapping_df = pd.read_excel(mapping_file)
            
            # Create a new page
            self.pdf.add_page()
            
            # ----- First section: Indirect Attainment Results -----
            self.pdf.set_font("Arial", "B", 16)
            self.pdf.cell(0, 15, "Indirect Attainment Analysis", ln=True, align="C")
            
            # Indirect Attainment Results subtitle
            self.pdf.set_font("Arial", "B", 12)
            self.pdf.cell(0, 10, "1. Indirect Attainment Results", ln=True)
            
            self.pdf.set_font("Arial", "I", 9)
            self.pdf.cell(0, 6, "Survey and feedback-based attainment metrics", ln=True)
            
            # Create table for results
            cols = results_df.columns.tolist()
            col_widths = [190 / len(cols)] * len(cols)  # Equal width for all columns
            
            # Draw header
            self.pdf.set_font("Arial", "B", 8)
            self.pdf.set_fill_color(200, 220, 255)
            
            for i, col in enumerate(cols):
                self.pdf.cell(col_widths[i], 8, str(col), border=1, fill=True, align="C")
            self.pdf.ln()
            
            # Draw data rows
            self.pdf.set_font("Arial", "", 8)
            for _, row in results_df.iterrows():
                for i, col in enumerate(cols):
                    value = str(row[col]) if pd.notna(row[col]) else "-"
                    self.pdf.cell(col_widths[i], 8, value, border=1, align="C")
                self.pdf.ln()
            
            # Add some space between tables
            self.pdf.ln(10)
            
            # ----- Second section: Indirect Attainment Mapping -----
            self.pdf.set_font("Arial", "B", 12)
            self.pdf.cell(0, 10, "2. Indirect Attainment Mapping", ln=True)
            
            self.pdf.set_font("Arial", "I", 9)
            self.pdf.cell(0, 6, "Mapping indirect assessment methods to Program Outcomes", ln=True)
            
            # Create table for mapping
            cols = mapping_df.columns.tolist()
            col_widths = [190 / len(cols)] * len(cols)  # Equal width for all columns
            
            # Draw header
            self.pdf.set_font("Arial", "B", 8)
            self.pdf.set_fill_color(200, 220, 255)
            
            for i, col in enumerate(cols):
                self.pdf.cell(col_widths[i], 8, str(col), border=1, fill=True, align="C")
            self.pdf.ln()
            
            # Draw data rows
            self.pdf.set_font("Arial", "", 8)
            for _, row in mapping_df.iterrows():
                for i, col in enumerate(cols):
                    value = str(row[col]) if pd.notna(row[col]) else "-"
                    self.pdf.cell(col_widths[i], 8, value, border=1, align="C")
                self.pdf.ln()
                
        except Exception as e:
            self.pdf.add_page()
            self.pdf.set_font("Arial", "B", 16)
            self.pdf.cell(0, 15, "Indirect Attainment Analysis", ln=True, align="C")
            self.pdf.set_font("Arial", "", 12)
            self.pdf.cell(0, 10, f"Error processing data: {str(e)}", ln=True)

    def add_combined_overall_final_attainment_page(self):
        """Add combined overall PO-PSO attainment and final CO attainment details on a single page."""
        overall_file = os.path.join(self.upload_folder, "overall_attainment.xlsx")
        final_co_file = os.path.join(self.upload_folder, "final_co_attainment.xlsx")
        
        if not os.path.exists(overall_file) or not os.path.exists(final_co_file):
            # If either file is missing, revert to individual pages
            if not os.path.exists(overall_file):
                self._add_missing_file_page("Overall PO-PSO Attainment", "overall_attainment.xlsx")
            if not os.path.exists(final_co_file):
                self._add_missing_file_page("Final CO Attainment Details", "final_co_attainment.xlsx")
            return
            
        try:
            overall_df = pd.read_excel(overall_file)
            final_co_df = pd.read_excel(final_co_file)
            
            # Create a new page
            self.pdf.add_page()
            
            # ----- First section: Overall PO-PSO Attainment -----
            self.pdf.set_font("Arial", "B", 16)
            self.pdf.cell(0, 15, "Final Attainment Analysis", ln=True, align="C")
            
            # Overall PO-PSO Attainment subtitle
            self.pdf.set_font("Arial", "B", 12)
            self.pdf.cell(0, 10, "1. Overall PO-PSO Attainment", ln=True)
            
            self.pdf.set_font("Arial", "I", 9)
            self.pdf.cell(0, 6, "Combining direct and indirect assessment for final PO-PSO attainment", ln=True)
            # Create table for overall attainment
            cols = overall_df.columns.tolist()
            col_widths = [30] + [160 / (len(cols) - 1)] * (len(cols) - 1)  # Wider for 1st column, equal for others
            
            # Draw header
            self.pdf.set_font("Arial", "B", 8)
            self.pdf.set_fill_color(200, 220, 255)
            
            for i, col in enumerate(cols):
                self.pdf.cell(col_widths[i], 8, str(col), border=1, fill=True, align="C")
            self.pdf.ln()
            
            # Draw data rows
            self.pdf.set_font("Arial", "", 8)
            for _, row in overall_df.iterrows():
                for i, col in enumerate(cols):
                    value = str(row[col]) if pd.notna(row[col]) else "-"
                    self.pdf.cell(col_widths[i], 8, value, border=1, align="C")
                self.pdf.ln()
            
            # Add some space between tables
            self.pdf.ln(10)
            
            # ----- Second section: Final CO Attainment Details -----
            self.pdf.set_font("Arial", "B", 12)
            self.pdf.cell(0, 10, "2. Detailed Final CO Attainment", ln=True)
            
            self.pdf.set_font("Arial", "I", 9)
            self.pdf.cell(0, 6, "Comprehensive breakdown of CO attainment with component weights", ln=True)
            
            # Create table for final CO attainment
            cols = final_co_df.columns.tolist()
            col_widths = [190 / len(cols)] * len(cols)  # Match column widths to Indirect Attainment Mapping
            
            # Draw header
            self.pdf.set_font("Arial", "B", 8)
            self.pdf.set_fill_color(200, 220, 255)
            
            for i, col in enumerate(cols):
                self.pdf.cell(col_widths[i], 8, str(col), border=1, fill=True, align="C")
            self.pdf.ln()
            
            # Draw data rows
            self.pdf.set_font("Arial", "", 8)
            for _, row in final_co_df.iterrows():
                for i, col in enumerate(cols):
                    value = str(row[col]) if pd.notna(row[col]) else "-"
                    self.pdf.cell(col_widths[i], 8, value, border=1, align="C")
                self.pdf.ln()
                
        except Exception as e:
            self.pdf.add_page()
            self.pdf.set_font("Arial", "B", 16)
            self.pdf.cell(0, 15, "Final Attainment Analysis", ln=True, align="C")
            self.pdf.set_font("Arial", "", 12)
            self.pdf.cell(0, 10, f"Error processing data: {str(e)}", ln=True)

    
    
    def calculate_text_height(self, text, cell_width):
        """Calculate height needed for text in a cell."""
        if not text:
            return 10
            
        # Rough estimation for text height
        font_size = 9  # Text font size
        char_width = font_size / 2  # Approximate character width
        chars_per_line = int(cell_width / char_width)
        
        lines = len(text) / chars_per_line if chars_per_line > 0 else 1
        return max(10, 10 * (int(lines) + 1))
    
    

    def _add_missing_file_page(self, description, filename):
        """Helper method to add a page indicating a missing file."""
        self.pdf.add_page()
        self.pdf.set_font("Arial", "B", 16)
        self.pdf.cell(0, 15, f"{description} - File Not Found", ln=True, align="C")
        
        self.pdf.set_font("Arial", "", 12)
        self.pdf.cell(0, 10, f"The file '{filename}' could not be found in the upload folder.", ln=True)
        self.pdf.cell(0, 10, "Please ensure the file is uploaded correctly.", ln=True)

    def _add_error_page(self, description, error_message):
        """Helper method to add a page indicating an error processing a file."""
        self.pdf.add_page()
        self.pdf.set_font("Arial", "B", 16)
        self.pdf.cell(0, 15, f"{description} - Processing Error", ln=True, align="C")
        
        self.pdf.set_font("Arial", "", 12)
        self.pdf.cell(0, 10, f"Error processing file: {error_message}", ln=True)