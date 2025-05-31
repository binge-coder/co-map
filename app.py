from flask import Flask, render_template, request, redirect, send_from_directory, session, url_for
import pandas as pd
import os
from fpdf import FPDF
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from scipy.stats import norm
from flask import jsonify
from report_generator import ReportGenerator
from combine_marks import process_student_marks

app = Flask(__name__)
app.secret_key = 'secret'  # Needed for session
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def home():
    config_exists = os.path.exists(os.path.join(UPLOAD_FOLDER, 'co_config.xlsx'))
    mapping_exists = os.path.exists(os.path.join(UPLOAD_FOLDER, 'co_po_mapping_matrix.xlsx'))
    return render_template('home.html', config_exists=config_exists, mapping_exists=mapping_exists)

@app.route('/minor1')
def minor1():
    return render_template('choose_entry_mode.html', exam='minor1')

@app.route('/minor2')
def minor2():
    if not os.path.exists(os.path.join(UPLOAD_FOLDER, 'minor1.xlsx')):
        return "<h3>Please complete Minor-1 entry first.</h3><a href='/minor1'>⬅ Back to Minor-1</a>"
    return render_template('choose_entry_mode.html', exam='minor2')

@app.route('/final')
def final():
    if not os.path.exists(os.path.join(UPLOAD_FOLDER, 'minor2.xlsx')):
        return "<h3>Please complete Minor-2 entry first.</h3><a href='/minor2'>⬅ Back to Minor-2</a>"
    return render_template('choose_entry_mode.html', exam='final')

@app.route('/assignment')
def assignment():
    if not os.path.exists(os.path.join(UPLOAD_FOLDER, 'final.xlsx')):
        return "<h3>Please complete Final exam entry first.</h3><a href='/final'>⬅ Back to Final</a>"
    return render_template('choose_entry_mode.html', exam='assignment')

@app.route('/manual/<exam>', methods=['GET', 'POST'])
def manual_entry(exam):
    if request.method == 'POST':
        action = request.form.get('action')
        row_count = int(request.form.get('row_count', 0))
        data = []
        for i in range(1, row_count + 1):
            row = [request.form.get(f'{field}_{i}') for field in
                   ["name", "roll", "q1", "q2", "q3", "q4", "q5", "q6", "total"]]
            data.append(row)

        df = pd.DataFrame(data, columns=["Student's Name", "Roll_No", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Total"])
        filename = f"{exam}.xlsx"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        if action == "preview":
            df.to_excel(filepath, index=False)
            table_html = df.to_html(classes="table table-bordered", index=False)

            # Generate bell curve using the saved Excel file
            generate_bell_curve(filepath, exam)

            return render_template('display.html', table=table_html, filename=filename, exam=exam, preview_mode=True)

        elif action == "submit":
            return render_template('success.html', exam=exam, now=datetime.now())

    return render_template('manual_entry.html', exam=exam, now=datetime.now())


from combine_marks import process_student_marks  # ✅ At top of app.py

@app.route('/upload/<exam>', methods=['POST'])
def upload_file(exam):
    file = request.files['file']
    if file:
        filename = f"{exam}.xlsx"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        df = pd.read_excel(filepath)
        df.fillna('', inplace=True)
        table_html = df.to_html(classes="table table-bordered", index=False)

        generate_bell_curve(filepath, exam)

        # ✅ Generate Bloom's pie chart for question papers
        if exam in ['m1_question_paper', 'm2_question_paper', 'final_question_paper']:
            generate_blooms_pie_chart(filepath, exam)

        # ✅ Trigger student_marks.xlsx generation after assignment upload
        if exam == 'assignment':
            success, result = process_student_marks()
            if not success:
                return f"<h3 class='text-danger'>Error: {result}</h3>"
            print("✅ student_marks.xlsx generated.")

            # ✅ Also generate bell curve for the combined marks
            generate_bell_curve(os.path.join(app.config['UPLOAD_FOLDER'], 'students_marks.xlsx'), 'students_marks')

        return render_template('display.html', table=table_html, filename=filename, exam=exam, preview_mode=True, uploaded=True)

@app.route('/submit/<exam>', methods=['POST'])
def submit_uploaded(exam):
    if exam == 'minor2':
        return redirect('/final')
    elif exam == 'final':
        return redirect('/assignment')
    elif exam == 'assignment':
        return redirect('/co-config')
    return render_template('success.html', exam=exam, now=datetime.now())


@app.route('/m1-question-paper', methods=['GET', 'POST'])
def m1_question_paper():
    return handle_question_paper('m1_question_paper', next_url='/m2-question-paper')

@app.route('/m2-question-paper', methods=['GET', 'POST'])
def m2_question_paper():
    return handle_question_paper('m2_question_paper', next_url='/final-question-paper')

@app.route('/final-question-paper', methods=['GET', 'POST'])
def final_question_paper():
    if request.method == 'POST':
        # Handle the question paper submission first
        row_count = int(request.form.get('row_count', 0))
        data = []
        for i in range(1, row_count + 1):
            row = [request.form.get(f'{field}_{i}') for field in
                   ["qno", "question", "marks", "co", "bloom"]]
            data.append(row)

        df = pd.DataFrame(data, columns=["Question Number", "Question", "Marks", "CO", "Bloom's Taxonomy"])
        filepath = os.path.join(UPLOAD_FOLDER, f"final_question_paper.xlsx")
        df.to_excel(filepath, index=False)
        
        # Generate all 3 Bloom's pie charts after final question paper submission
        question_papers = [
            ('m1_question_paper', 'M1 Question Paper'),
            ('m2_question_paper', 'M2 Question Paper'), 
            ('final_question_paper', 'Final Question Paper')
        ]
        
        for paper_name, display_name in question_papers:
            paper_filepath = os.path.join(UPLOAD_FOLDER, f"{paper_name}.xlsx")
            if os.path.exists(paper_filepath):
                generate_blooms_pie_chart(paper_filepath, paper_name)
                print(f"✅ Generated Bloom's pie chart for {display_name}")
            else:
                print(f"⚠️ File not found: {paper_filepath}")
        
        return redirect('/minor1')
    else:
        return render_template('question_paper.html', paper='final_question_paper')

def handle_question_paper(name, next_url):
    if request.method == 'POST':
        row_count = int(request.form.get('row_count', 0))
        data = []
        for i in range(1, row_count + 1):
            row = [request.form.get(f'{field}_{i}') for field in
                   ["qno", "question", "marks", "co", "bloom"]]
            data.append(row)

        df = pd.DataFrame(data, columns=["Question Number", "Question", "Marks", "CO", "Bloom's Taxonomy"])
        filepath = os.path.join(UPLOAD_FOLDER, f"{name}.xlsx")
        df.to_excel(filepath, index=False)
       
        return redirect(next_url)

    return render_template('question_paper.html', paper=name)

@app.route('/downloads')
def downloads():
    files = []
    for fname in os.listdir(UPLOAD_FOLDER):
        if fname.endswith(('.xlsx', '.pdf', '.png')):
            files.append(fname)
    return render_template('downloads.html', files=files)

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/download_pdf/<filename>')
def download_pdf(filename):
    excel_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(excel_path):
        return "File not found", 404

    df = pd.read_excel(excel_path)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.set_fill_color(230, 230, 230)

    for col in df.columns:
        pdf.cell(25, 10, str(col), border=1, fill=True)
    pdf.ln()

    for index, row in df.iterrows():
        for value in row:
            pdf.cell(25, 10, str(value), border=1)
        pdf.ln()

    pdf_filename = filename.replace('.xlsx', '.pdf')
    pdf_output = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
    pdf.output(pdf_output)

    return send_from_directory(app.config['UPLOAD_FOLDER'], pdf_filename, as_attachment=True)


@app.route('/co-config', methods=['GET', 'POST'])
def co_config():
    if request.method == 'POST':
        co_count = int(request.form.get('co_count', 0))
        data = []

        for i in range(1, co_count + 1):
            data.append({
                'CO': request.form.get(f'co_{i}'),
                'Threshold (%)': request.form.get(f'threshold_{i}'),
                'Level 1 Range': request.form.get(f'level1_{i}'),
                'Level 2 Range': request.form.get(f'level2_{i}'),
                'Level 3 Range': request.form.get(f'level3_{i}'),
            })

        df = pd.DataFrame(data)
        df.to_excel(os.path.join(UPLOAD_FOLDER, 'co_config.xlsx'), index=False)

        return render_template('success.html', exam='CO Attainment Configuration', now=datetime.now())

    return render_template('co_config.html')

@app.route('/co-attainment')
def co_attainment():
    from computations.attainment_logic import compute_attainment

    try:
        result = compute_attainment()
        tools = result.get('tools', [])

        # Convert DataFrames to JSON-like dicts
        for tool in tools:
            tool['student_results'] = tool['student_results'].to_dict(orient='records')
            tool['attainment_summary'] = tool['attainment_summary'].to_dict(orient='records')
            tool['question_mapping'] = tool['question_mapping'].to_dict(orient='records')

        result['final_attainment'] = result['final_attainment'].to_dict(orient='records')    

        # Show fallback message if no tools found
        if not tools:
            return "<h4 class='text-danger'>No data available. Check input files or logs.</h4>"

        return render_template("co_attainment_result.html", **result)

    except Exception as e:
        return f"<h4 class='text-danger'>Error computing CO Attainment: {str(e)}</h4>"
    
@app.route("/co-po-pso-mapping")
def copopso_mapping():
    from computations.attainment_logic import compute_attainment
    
    try:
        # Get the final attainment data
        result = compute_attainment()
        final_attainment = result.get('final_attainment', pd.DataFrame()).to_dict(orient='records')
        
        return render_template("copopso_mapping.html", final_attainment=final_attainment)
    except Exception as e:
        return f"<h4 class='text-danger'>Error getting CO Attainment data: {str(e)}</h4>"


def generate_bell_curve(file_path, base_name):
    try:
        df = pd.read_excel(file_path)
        if 'Total' not in df.columns:
            return

        scores = df['Total'].dropna().astype(float).tolist()

        if not scores:
            print(f"No valid scores found in {base_name}.xlsx.")
            return

        # Compute statistics
        mean = np.mean(scores)
        std = np.std(scores)

        # Generate x and y values for the bell curve
        x = np.linspace(0, max(30, max(scores)), 1000)
        y = norm.pdf(x, mean, std)

        # Plot setup
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(10, 6))

        # Bell curve
        ax.plot(x, y, color='#1f77b4', linewidth=3, label='Normal Distribution')
        ax.fill_between(x, y, color='#1f77b4', alpha=0.3)

        # Mean line
        ax.axvline(mean, color='red', linestyle='--', linewidth=2, label=f'Mean = {mean:.2f}')

        # Title and labels
        ax.set_title(f'Bell Curve of {base_name.capitalize()} Total Scores', fontsize=18, fontweight='bold')
        ax.set_xlabel('Total Score', fontsize=14)
        ax.set_ylabel('Probability Density', fontsize=14)

        # Axes and grid styling
        ax.set_xlim(0, max(30, max(scores)))
        ax.spines[['top', 'right']].set_visible(False)
        ax.tick_params(axis='both', labelsize=12)
        ax.grid(axis='y', linestyle='--', alpha=0.4)

        # Add legend
        ax.legend(loc='upper right', fontsize=12, frameon=True)

        # Summary stats
        ax.text(1, max(y) * 0.9, f'N = {len(scores)}\nMean = {mean:.2f}\nStd Dev = {std:.2f}',
                fontsize=12, bbox=dict(boxstyle="round,pad=0.3", edgecolor='gray',
                                       facecolor='white', alpha=0.8))

        # Save with consistent name
        image_path = os.path.join(UPLOAD_FOLDER, f"{base_name}_bell.png")
        pdf_path = os.path.join(UPLOAD_FOLDER, f"{base_name}_bell.pdf")

        plt.tight_layout()
        plt.savefig(image_path, dpi=300)
        plt.savefig(pdf_path)
        plt.close()

    except Exception as e:
        print(f"Error generating refined bell curve for {base_name}: {e}")


@app.route('/save-mapping', methods=['POST'])
def save_mapping():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data received'})
            
        # Create DataFrame for mapping matrix
        mapping_data = []
        for co_entry in data['co_po_mapping']:
            row_data = {'CO': co_entry['CO']}
            for i, col in enumerate(data['columns']):
                row_data[col] = co_entry['values'][i]
            mapping_data.append(row_data)
            
        mapping_df = pd.DataFrame(mapping_data)
        
        # Save to Excel
        mapping_df.to_excel(os.path.join(UPLOAD_FOLDER, 'co_po_mapping.xlsx'), index=False)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/save-all-data', methods=['POST'])
def save_all_data():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data received'})
            
        # Save mapping matrix
        if 'mappingMatrix' in data and 'directAttainment' in data:
            # Create DataFrame for mapping matrix - similar to save-mapping
            columns = ['PO1', 'PO 2', 'PO 3', 'PO 4', 'PO 5', 'PO 6', 'PO 7', 
                'PO 8', 'PO 9', 'PO 10', 'PO 11', 'PO 12', 'PSO 1', 'PSO 12']
                
            mapping_data = []
            for i, co_entry in enumerate(data['directAttainment']):
                row_data = {'CO': co_entry['CO']}
                for j, col in enumerate(columns):
                    if i < len(data['mappingMatrix']):
                        row_data[col] = data['mappingMatrix'][i][j]
                mapping_data.append(row_data)
                
            mapping_df = pd.DataFrame(mapping_data)
            mapping_df.to_excel(os.path.join(UPLOAD_FOLDER, 'co_po_mapping_matrix.xlsx'), index=False)
        
        # Save calculated data tables
        calculated_data = data.get('calculatedData', {})
        
        # Direct Mapping Calculation
        if 'directMappingData' in calculated_data:
            direct_df = pd.DataFrame(calculated_data['directMappingData'])
            direct_df.to_excel(os.path.join(UPLOAD_FOLDER, 'direct_attainment_mapping.xlsx'), index=False)
            
        # Indirect Attainment
        if 'indirectAttainmentData' in calculated_data:
            indirect_df = pd.DataFrame(calculated_data['indirectAttainmentData'])
            indirect_df.to_excel(os.path.join(UPLOAD_FOLDER, 'indirect_attainment.xlsx'), index=False)
            
        # Indirect Mapping Calculation
        if 'indirectMappingData' in calculated_data:
            indirect_mapping_df = pd.DataFrame(calculated_data['indirectMappingData'])
            indirect_mapping_df.to_excel(os.path.join(UPLOAD_FOLDER, 'indirect_attainment_mapping.xlsx'), index=False)
            
        # Overall Attainment
        if 'overallAttainmentData' in calculated_data:
            overall_df = pd.DataFrame(calculated_data['overallAttainmentData'])
            overall_df.to_excel(os.path.join(UPLOAD_FOLDER, 'overall_attainment.xlsx'), index=False)
            
        # Final CO Attainment
        if 'finalCOAttainmentData' in calculated_data:
            final_co_df = pd.DataFrame(calculated_data['finalCOAttainmentData'])
            final_co_df.to_excel(os.path.join(UPLOAD_FOLDER, 'final_co_attainment.xlsx'), index=False)
            
        # Generate and save charts as images
        generate_attainment_charts(data)
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def generate_attainment_charts(data):
    try:
        # Final CO Attainment Chart
        # Final CO Attainment Chart with Max Level Comparison
        if 'calculatedData' in data and 'finalCOAttainmentData' in data['calculatedData']:
            final_co_data = data['calculatedData']['finalCOAttainmentData']
            
            labels = [row.get('CO', f"CO{i+1}") for i, row in enumerate(final_co_data)]
            values = [float(row.get('Attainment', 0)) for row in final_co_data]
            max_values = [3.0] * len(values)  # Max level for each CO

            x = np.arange(len(labels))  # label locations
            width = 0.3  # thinner bars

            plt.figure(figsize=(12, 6))
            fig, ax = plt.subplots(figsize=(12, 6))
            
            bars1 = ax.bar(x - width/2, values, width, label='Attainment', color='#4361ee')
            bars2 = ax.bar(x + width/2, max_values, width, label='Max Level', color='#f77f00')

            ax.set_title('Final CO Attainment vs Max Level', fontsize=16, fontweight='bold')
            ax.set_xlabel('Course Outcomes', fontsize=14)
            ax.set_ylabel('Attainment Level', fontsize=14)
            ax.set_xticks(x)
            ax.set_xticklabels(labels)
            ax.set_ylim(0, 4)
            ax.grid(axis='y', linestyle='--', alpha=0.7)

            # Add values on top of bars
            for bars in [bars1, bars2]:
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                            f'{height:.2f}', ha='center', fontsize=10)

            ax.legend(loc='upper right', fontsize=12)
            plt.tight_layout()
            plt.savefig(os.path.join(UPLOAD_FOLDER, 'final_co_attainment_chart.png'), dpi=300)
            plt.close()
            
        # Overall PO-PSO Attainment Chart
        if 'calculatedData' in data and 'overallAttainmentData' in data['calculatedData']:
            overall_data = data['calculatedData']['overallAttainmentData']
            
            if overall_data and len(overall_data) > 0:
                # First row should be the overall attainment
                row = overall_data[0]
                
                # Extract column names and values, skipping the first column (label)
                columns = ['PO1', 'PO 2', 'PO 3', 'PO 4', 'PO 5', 'PO 6', 'PO 7', 
                          'PO 8', 'PO 9', 'PO 10', 'PO 11', 'PO 12', 'PSO 1', 'PSO 12']
                values = []
                
                # Extract values from the row data
                for col in columns:
                    if col in row:
                        values.append(float(row[col]))
                    else:
                        # If the column name isn't found directly, look for it by index
                        for key, val in row.items():
                            if key.startswith(col) or key.endswith(col):
                                values.append(float(val))
                                break
                        else:
                            values.append(0)  # Default if no match
                
                plt.figure(figsize=(16, 8))
                bars = plt.bar(columns, values, color='#4cc9f0')
                plt.title('Overall PO-PSO Attainment', fontsize=16)
                plt.xlabel('Program Outcomes & Program Specific Outcomes', fontsize=14)
                plt.ylabel('Attainment Level', fontsize=14)
                plt.grid(axis='y', linestyle='--', alpha=0.7)
                plt.xticks(rotation=45)
                
                # Add values on top of bars
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                            f'{height:.2f}', ha='center', fontsize=10)
                            
                plt.tight_layout()
                plt.savefig(os.path.join(UPLOAD_FOLDER, 'overall_po_pso_attainment_chart.png'), dpi=300)
                plt.close()
    
    except Exception as e:
        print(f"Error generating attainment charts: {e}")

@app.route('/generate-report')
def generate_report():
    try:
        report_gen = ReportGenerator(UPLOAD_FOLDER)
        report_filename = report_gen.generate_comprehensive_report()
        return redirect(url_for('download', filename=report_filename))
    except Exception as e:
        return f"<h4 class='text-danger'>Error generating report: {str(e)}</h4>"

@app.route('/report-details', methods=['GET', 'POST'])
def report_details():
    if request.method == 'POST':
        professor = request.form.get('professor')
        department = request.form.get('department')
        year = request.form.get('year')
        semester = request.form.get('semester')
        subject = request.form.get('subject')
        course_code = request.form.get('course_code')

        # Save to Excel
        data = {
            'Professor': [professor],
            'Department': [department],
            'Academic Year': [year],
            'Semester': [semester],
            'Subject Name': [subject],
            'Course Code': [course_code]
        }

        df = pd.DataFrame(data)
        df.to_excel(os.path.join(UPLOAD_FOLDER, 'report_metadata.xlsx'), index=False)

        # Proceed to generate report
        return redirect('/generate-report')

    return render_template('report_details_form.html')


   
def generate_blooms_pie_chart(file_path, output_name):
    try:
        df = pd.read_excel(file_path)
        if "Bloom's Taxonomy" not in df.columns:
            print(f"'Bloom's Taxonomy' column missing in {output_name}")
            return

        blooms_data = df["Bloom's Taxonomy"].dropna().value_counts()
        
        if blooms_data.empty:
            print(f"No Bloom's taxonomy data found in {output_name}")
            return

        # Plotting
        plt.figure(figsize=(8, 8))
        plt.pie(blooms_data, labels=blooms_data.index, autopct='%1.1f%%',
                colors=plt.cm.Dark2.colors, startangle=140, textprops={'fontsize': 12})
        plt.title(f"{output_name.replace('_', ' ').replace('-', ' ').title()} - Bloom's Taxonomy Distribution", fontsize=14)

        # Ensure output goes to uploads folder
        chart_path = os.path.join(UPLOAD_FOLDER, f"{output_name}_blooms_pie.png")
        plt.tight_layout()
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Bloom's pie chart saved: {chart_path}")

    except Exception as e:
        print(f"Error generating Bloom's pie chart for {output_name}: {e}")
    
    
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)