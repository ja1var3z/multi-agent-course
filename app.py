import streamlit as st
import pandas as pd
import json
import csv
import io
from pathlib import Path
import openai
from typing import Dict, Any, List, Optional
import traceback
import sys
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
import contextlib

# Configure page
st.set_page_config(
    page_title="Smart Data Analyzer",
    page_icon="📊",
    layout="wide"
)

class CodeExecutor:
    def __init__(self):
        self.allowed_imports = [
            'pandas', 'numpy', 'matplotlib.pyplot', 'seaborn', 'plotly.express', 
            'plotly.graph_objects', 'datetime', 'math', 'statistics', 'json'
        ]
        
    def execute_code(self, code: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Safely execute Python code with the dataframe"""
        # Create a safe execution environment
        safe_globals = {
            '__builtins__': {
                'len': len, 'str': str, 'int': int, 'float': float, 'bool': bool,
                'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
                'min': min, 'max': max, 'sum': sum, 'abs': abs, 'round': round,
                'sorted': sorted, 'enumerate': enumerate, 'zip': zip,
                'range': range, 'print': print
            },
            'pd': pd,
            'np': np,
            'plt': plt,
            'sns': sns,
            'px': px,
            'go': go,
            'df': df,
            'json': json
        }
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        result = {
            'success': False,
            'output': '',
            'error': '',
            'plots': [],
            'dataframes': {}
        }
        
        try:
            # Execute the code
            exec_locals = {}
            exec(code, safe_globals, exec_locals)
            
            # Capture any printed output
            result['output'] = captured_output.getvalue()
            
            # Check for any dataframes created
            for key, value in exec_locals.items():
                if isinstance(value, pd.DataFrame):
                    result['dataframes'][key] = value
            
            # Check for matplotlib figures
            if plt.get_fignums():
                result['plots'] = ['matplotlib']
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            result['traceback'] = traceback.format_exc()
        
        finally:
            sys.stdout = old_stdout
        
        return result

class DataProcessor:
    def __init__(self):
        self.original_data = None
        self.processed_data = None
        self.file_type = None
        self.transformation_applied = None
    
    def read_file(self, uploaded_file) -> Optional[pd.DataFrame]:
        """Read file based on extension"""
        file_extension = Path(uploaded_file.name).suffix.lower()
        self.file_type = file_extension
        
        try:
            if file_extension == '.csv':
                return self._read_csv(uploaded_file)
            elif file_extension == '.json':
                return self._read_json(uploaded_file)
            elif file_extension == '.tsv':
                return self._read_tsv(uploaded_file)
            else:
                st.error(f"Unsupported file format: {file_extension}")
                return None
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            return None
    
    def _read_csv(self, uploaded_file) -> pd.DataFrame:
        """Read CSV file"""
        return pd.read_csv(uploaded_file)
    
    def _read_json(self, uploaded_file) -> pd.DataFrame:
        """Read JSON file - handle both array of objects and nested JSON"""
        content = uploaded_file.read().decode('utf-8')
        json_data = json.loads(content)
        
        if isinstance(json_data, list):
            # Array of objects
            return pd.DataFrame(json_data)
        elif isinstance(json_data, dict):
            # Single object or nested structure
            return pd.json_normalize(json_data)
        else:
            # Fallback - create DataFrame with single column
            return pd.DataFrame({'data': [json_data]})
    
    def _read_tsv(self, uploaded_file) -> pd.DataFrame:
        """Read TSV file using the specified method"""
        # Save uploaded file temporarily to read with the specified method
        temp_file_path = f"temp_{uploaded_file.name}"
        
        # Write uploaded file content to temporary file
        with open(temp_file_path, 'wb') as f:
            f.write(uploaded_file.getvalue())
        
        try:
            # Use the exact method specified
            all_rows = []
            with open(temp_file_path) as fd:
                rd = csv.reader(fd, delimiter="\t", quotechar='"')
                for row in rd:
                    all_rows.append(row)
            
            # Process the rows
            if not all_rows:
                return pd.DataFrame()
            
            # Check if we have JSON data in the first column
            if len(all_rows[0]) == 1 and self._is_json_string(all_rows[0][0]):
                return self._process_tsv_rows_with_json(all_rows)
            else:
                # Regular TSV processing
                return self._process_regular_tsv_rows(all_rows)
                
        finally:
            # Clean up temporary file
            try:
                import os
                os.remove(temp_file_path)
            except:
                pass
    
    def _is_json_string(self, value: str) -> bool:
        """Check if a string contains JSON data"""
        try:
            json.loads(value)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    def _process_tsv_rows_with_json(self, rows: List[List[str]]) -> pd.DataFrame:
        """Process TSV rows where first column contains JSON"""
        all_records = []
        
        for i, row in enumerate(rows):
            if row and row[0]:  # Skip empty rows
                try:
                    # Parse JSON from first column
                    json_data = json.loads(row[0])
                    
                    # Flatten the JSON data
                    flattened = pd.json_normalize(json_data)
                    if not flattened.empty:
                        record = flattened.to_dict('records')[0]
                        record['original_row'] = i
                        all_records.append(record)
                    
                except json.JSONDecodeError as e:
                    st.warning(f"Could not parse JSON in row {i}: {str(e)}")
                    # Fall back to treating as regular data
                    record = {f'column_{j}': val for j, val in enumerate(row)}
                    record['original_row'] = i
                    all_records.append(record)
        
        return pd.DataFrame(all_records) if all_records else pd.DataFrame()
    
    def _process_regular_tsv_rows(self, rows: List[List[str]]) -> pd.DataFrame:
        """Process regular TSV rows"""
        if not rows:
            return pd.DataFrame()
        
        # Determine if first row is header
        first_row = rows[0]
        
        # Simple heuristic: if first row contains non-numeric values, treat as header
        likely_header = any(not self._is_numeric(cell) for cell in first_row if cell.strip())
        
        if likely_header and len(rows) > 1:
            # Use first row as columns
            columns = first_row
            data_rows = rows[1:]
        else:
            # Generate column names
            max_cols = max(len(row) for row in rows) if rows else 0
            columns = [f'column_{i}' for i in range(max_cols)]
            data_rows = rows
        
        # Create DataFrame
        data = []
        for row in data_rows:
            # Pad row to match number of columns
            padded_row = row + [''] * (len(columns) - len(row))
            data.append(padded_row[:len(columns)])  # Truncate if too long
        
        return pd.DataFrame(data, columns=columns)
    
    def _is_numeric(self, value: str) -> bool:
        """Check if a string represents a numeric value"""
        try:
            float(value.strip())
            return True
        except (ValueError, AttributeError):
            return False

class LLMAnalyzer:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
    
    def analyze_data_structure(self, df: pd.DataFrame, file_type: str) -> Dict[str, Any]:
        """Analyze data structure and suggest transformations"""
        
        # Prepare data sample for analysis
        sample_info = self._prepare_data_sample(df)
        
        prompt = f"""
        I have a {file_type} file with the following structure:
        
        Columns: {list(df.columns)}
        Data types: {df.dtypes.to_dict()}
        Shape: {df.shape}
        
        Sample data from first 2 columns:
        {sample_info}
        
        Please analyze this data and provide:
        1. Whether any transformations are needed (Yes/No)
        2. What specific transformations would be helpful
        3. Brief reasoning for the transformations
        4. Suggested new column names if applicable
        
        Focus on:
        - Nested JSON structures that need flattening
        - Date/time fields that need parsing
        - Monetary values that need normalization (if no decimal point, divide by 100)
        - Text fields that could be split or cleaned
        - Any obvious data quality issues
        
        Respond in JSON format:
        {{
            "needs_transformation": true/false,
            "transformations": [
                {{
                    "type": "transformation_type",
                    "column": "column_name",
                    "description": "what to do",
                    "reasoning": "why needed"
                }}
            ],
            "overall_assessment": "brief summary"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {
                "needs_transformation": False,
                "transformations": [],
                "overall_assessment": f"Error analyzing data: {str(e)}"
            }
    
    def generate_analysis_code(self, df: pd.DataFrame, question: str) -> Dict[str, str]:
        """Generate Python code to analyze the data and answer the question"""
        
        data_summary = self._prepare_data_summary(df)
        
        prompt = f"""
        I have a dataset with the following structure:
        {data_summary}
        
        Question: {question}
        
        Please generate Python code to analyze this data and answer the question. The dataframe is available as 'df'.
        
        Requirements:
        1. Use pandas, numpy, matplotlib, seaborn, or plotly for analysis
        2. Include appropriate visualizations if relevant
        3. Print clear results and explanations
        4. Handle any potential errors (missing values, etc.)
        5. Make the code readable with comments
        6. For monetary values, check if they need normalization (no decimal = divide by 100)
        
        Available libraries: pandas (pd), numpy (np), matplotlib.pyplot (plt), seaborn (sns), plotly.express (px), plotly.graph_objects (go)
        
        Provide your response in this JSON format:
        {{
            "code": "python code here",
            "explanation": "explanation of what the code does",
            "expected_output": "description of expected results"
        }}
        
        Example code structure:
        ```python
        # Data analysis for: {question}
        print("Analysis Results:")
        
        # Your analysis code here
        # Include calculations, grouping, filtering as needed
        # Add visualizations if appropriate
        
        print("Summary of findings:")
        # Print key insights
        ```
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {
                "code": f"print('Error generating code: {str(e)}')",
                "explanation": f"Error: {str(e)}",
                "expected_output": "Error message"
            }
    
    def _prepare_data_sample(self, df: pd.DataFrame) -> str:
        """Prepare sample data for LLM analysis"""
        if df.empty:
            return "No data available"
        
        # Get first 2 columns and first 5 rows
        sample_cols = df.columns[:2].tolist()
        sample_data = df[sample_cols].head(5)
        
        return sample_data.to_string()
    
    def _prepare_data_summary(self, df: pd.DataFrame) -> str:
        """Prepare comprehensive data summary for analysis"""
        if df.empty:
            return "Dataset is empty"
        
        summary = []
        summary.append(f"Dataset shape: {df.shape[0]} rows, {df.shape[1]} columns")
        summary.append(f"Columns: {list(df.columns)}")
        
        # Data types
        summary.append("\nData types:")
        for col, dtype in df.dtypes.items():
            summary.append(f"  {col}: {dtype}")
        
        # Statistical summary for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            summary.append(f"\nNumeric columns summary:")
            summary.append(df[numeric_cols].describe().to_string())
        
        # Sample data (first 3 rows)
        summary.append(f"\nFirst 3 rows:")
        summary.append(df.head(3).to_string())
        
        # Missing values
        missing = df.isnull().sum()
        if missing.sum() > 0:
            summary.append(f"\nMissing values:")
            for col, count in missing.items():
                if count > 0:
                    summary.append(f"  {col}: {count}")
        
        return "\n".join(summary)

def apply_transformations(df: pd.DataFrame, transformations: List[Dict]) -> pd.DataFrame:
    """Apply suggested transformations to the dataframe"""
    transformed_df = df.copy()
    
    for transform in transformations:
        try:
            transform_type = transform.get('type', '').lower()
            column = transform.get('column', '')
            
            if transform_type == 'normalize_monetary' and column in transformed_df.columns:
                # Normalize monetary values
                def normalize_money(val):
                    if pd.isna(val):
                        return val
                    val_str = str(val).strip()
                    if '.' not in val_str and val_str.replace('-', '').isdigit():
                        return float(val_str) / 100
                    return float(val_str) if val_str.replace('.', '').replace('-', '').isdigit() else val
                
                transformed_df[column + '_normalized'] = transformed_df[column].apply(normalize_money)
            
            elif transform_type == 'parse_date' and column in transformed_df.columns:
                # Parse date columns
                transformed_df[column + '_parsed'] = pd.to_datetime(transformed_df[column], errors='coerce')
            
            elif transform_type == 'flatten_json' and column in transformed_df.columns:
                # Flatten JSON columns (basic implementation)
                json_df = pd.json_normalize(transformed_df[column].apply(lambda x: json.loads(x) if isinstance(x, str) else x))
                transformed_df = pd.concat([transformed_df.drop(columns=[column]), json_df], axis=1)
            
        except Exception as e:
            st.warning(f"Could not apply transformation {transform_type} to {column}: {str(e)}")
    
    return transformed_df

def main():
    st.title("📊 Smart Data Analyzer with Code Execution")
    st.markdown("Upload your data file and let AI generate and execute Python code for analysis!")
    
    # Sidebar for API key
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("OpenAI API Key", type="password")
        
        if not api_key:
            st.warning("Please enter your OpenAI API key to use AI features")
        
        st.header("Analysis Options")
        show_code = st.checkbox("Show generated code", value=True)
        auto_execute = st.checkbox("Auto-execute safe code", value=False)
        
        st.header("TSV Processing Info")
        st.info("TSV files are read using:\n```python\nwith open(.tsv) as fd:\n    rd = csv.reader(fd, delimiter='\\t', quotechar='\"')\n    for row in rd:\n        print(row)\n```")
    
    # Initialize session state
    if 'processor' not in st.session_state:
        st.session_state.processor = DataProcessor()
    if 'analyzer' not in st.session_state and api_key:
        st.session_state.analyzer = LLMAnalyzer(api_key)
    if 'executor' not in st.session_state:
        st.session_state.executor = CodeExecutor()
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['csv', 'json', 'tsv'],
        help="Upload a CSV, JSON, or TSV file"
    )
    
    if uploaded_file is not None:
        # Read file
        with st.spinner("Reading file..."):
            df = st.session_state.processor.read_file(uploaded_file)
        
        if df is not None:
            st.session_state.processor.original_data = df
            
            # Show basic file info
            st.success(f"✅ File loaded successfully!")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows", df.shape[0])
            with col2:
                st.metric("Columns", df.shape[1])
            with col3:
                st.metric("File Type", st.session_state.processor.file_type)
            
            # Show data preview
            with st.expander("📋 Data Preview", expanded=True):
                st.dataframe(df.head(10), use_container_width=True)
            
            # Show raw data structure for TSV files
            if st.session_state.processor.file_type == '.tsv':
                with st.expander("🔍 TSV Reading Details"):
                    st.write("**File processed using specified TSV reading method:**")
                    st.code("""with open(.tsv) as fd:
    rd = csv.reader(fd, delimiter="\\t", quotechar='"')
    for row in rd:
        print(row)""")
                    
                    if len(df.columns) > 0:
                        st.write(f"**Detected columns:** {list(df.columns)}")
                        st.write(f"**Data shape:** {df.shape}")
                        
                        # Check if JSON was detected
                        json_cols = [col for col in df.columns if 'json' in col.lower() or any(df[col].astype(str).str.contains(r'^\s*[\{\[]', na=False))]
                        if json_cols:
                            st.info(f"JSON data detected in columns: {json_cols}")
            
            # AI Analysis (if API key provided)
            if api_key and 'analyzer' in st.session_state:
                st.subheader("🤖 AI Data Structure Analysis")
                
                if st.button("Analyze Data Structure"):
                    with st.spinner("AI is analyzing your data structure..."):
                        analysis = st.session_state.analyzer.analyze_data_structure(
                            df, st.session_state.processor.file_type
                        )
                    
                    st.json(analysis)
                    
                    # Apply transformations if suggested
                    if analysis.get('needs_transformation', False):
                        if st.button("Apply Suggested Transformations"):
                            with st.spinner("Applying transformations..."):
                                transformed_df = apply_transformations(df, analysis.get('transformations', []))
                                st.session_state.processor.processed_data = transformed_df
                                st.success("Transformations applied!")
                                st.dataframe(transformed_df.head(10), use_container_width=True)
            
            # Use processed data if available, otherwise original
            current_df = st.session_state.processor.processed_data if st.session_state.processor.processed_data is not None else df
            
            # Quick Analysis Section
            st.subheader("⚡ Quick Analysis")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("📊 Data Summary"):
                    st.write("**Data Summary:**")
                    st.write(current_df.describe(include='all'))
            
            with col2:
                if st.button("🔍 Missing Values"):
                    missing = current_df.isnull().sum()
                    missing_df = pd.DataFrame({'Column': missing.index, 'Missing Count': missing.values})
                    missing_df = missing_df[missing_df['Missing Count'] > 0]
                    if missing_df.empty:
                        st.success("No missing values found!")
                    else:
                        st.dataframe(missing_df)
            
            with col3:
                if st.button("📋 Data Types"):
                    types_df = pd.DataFrame({'Column': current_df.dtypes.index, 'Data Type': current_df.dtypes.values})
                    st.dataframe(types_df)
            
            with col4:
                if st.button("📈 Basic Stats"):
                    numeric_cols = current_df.select_dtypes(include=['number']).columns
                    if len(numeric_cols) > 0:
                        st.write("**Numeric Columns Statistics:**")
                        st.write(current_df[numeric_cols].describe())
                    else:
                        st.info("No numeric columns found for statistics")
            
            # AI-Powered Code Generation and Execution
            if api_key and 'analyzer' in st.session_state:
                st.subheader("💬 AI Data Analysis with Code Execution")
                
                # Predefined analysis options
                st.markdown("**Quick Analysis Questions:**")
                analysis_options = [
                    "Show me the distribution of values in numeric columns",
                    "What are the top 10 most frequent values in categorical columns?",
                    "Create visualizations to understand the data patterns",
                    "Identify any outliers in the numeric data",
                    "Show correlation between numeric variables",
                    "Analyze trends over time (if date columns exist)",
                    "Normalize and analyze monetary values (handle decimal formatting)"
                ]
                
                selected_analysis = st.selectbox("Choose a quick analysis:", ["Custom Question"] + analysis_options)
                
                if selected_analysis != "Custom Question":
                    question = selected_analysis
                else:
                    question = st.text_area("Ask a custom question about your data:", 
                                           placeholder="e.g., What are the trends in sales over time? Which products are most popular? Create a visualization showing...")
                
                if st.button("🚀 Generate & Execute Analysis") and question:
                    with st.spinner("AI is generating analysis code..."):
                        code_response = st.session_state.analyzer.generate_analysis_code(current_df, question)
                    
                    if show_code:
                        st.subheader("📝 Generated Code")
                        st.code(code_response.get('code', ''), language='python')
                        
                        st.subheader("💡 Code Explanation")
                        st.write(code_response.get('explanation', ''))
                    
                    # Execute the code
                    execute_button = st.button("▶️ Execute Code") if not auto_execute else True
                    
                    if execute_button:
                        with st.spinner("Executing analysis code..."):
                            execution_result = st.session_state.executor.execute_code(
                                code_response.get('code', ''), current_df
                            )
                        
                        if execution_result['success']:
                            st.success("✅ Code executed successfully!")
                            
                            # Show output
                            if execution_result['output']:
                                st.subheader("📊 Analysis Results")
                                st.text(execution_result['output'])
                            
                            # Show any created dataframes
                            if execution_result['dataframes']:
                                st.subheader("📋 Generated DataFrames")
                                for name, df_result in execution_result['dataframes'].items():
                                    st.write(f"**{name}:**")
                                    st.dataframe(df_result)
                            
                            # Show plots
                            if execution_result['plots']:
                                st.subheader("📈 Generated Visualizations")
                                st.pyplot(plt.gcf())
                                plt.close('all')  # Clean up plots
                        
                        else:
                            st.error("❌ Code execution failed!")
                            st.error(execution_result['error'])
                            if 'traceback' in execution_result:
                                with st.expander("Show detailed error"):
                                    st.code(execution_result['traceback'])
                
                # Manual code execution
                st.subheader("🔧 Manual Code Editor")
                manual_code = st.text_area("Write your own Python code (dataframe is available as 'df'):", 
                                         placeholder="# Example:\nprint(df.head())\nprint(df.describe())")
                
                if st.button("Execute Manual Code") and manual_code:
                    with st.spinner("Executing manual code..."):
                        execution_result = st.session_state.executor.execute_code(manual_code, current_df)
                    
                    if execution_result['success']:
                        st.success("✅ Manual code executed successfully!")
                        if execution_result['output']:
                            st.text(execution_result['output'])
                        if execution_result['plots']:
                            st.pyplot(plt.gcf())
                            plt.close('all')
                    else:
                        st.error("❌ Manual code execution failed!")
                        st.error(execution_result['error'])
            
            # Data Export
            st.subheader("💾 Export Data")
            if current_df is not None:
                csv_data = current_df.to_csv(index=False)
                st.download_button(
                    label="Download Processed Data as CSV",
                    data=csv_data,
                    file_name=f"processed_{uploaded_file.name.split('.')[0]}.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    main()