import streamlit as st
import pandas as pd
import docx
import PyPDF2
import openai
from PIL import Image
import io
import os
from dotenv import load_dotenv

os.environ["OPENAI_API_KEY"] = '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'

# Load environment variables
load_dotenv()

# Configure OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

# Define valid access codes
VALID_CODES = ["5510", "3388", "4567"]

def check_password():
    """Returns `True` if the user had the correct access code."""

    def password_entered():
        """Checks whether an access code entered by the user is correct."""
        if st.session_state["password"] in VALID_CODES:
            st.session_state["password_correct"] = True
            st.session_state["access_code"] = st.session_state["password"]  # Store the used code
            del st.session_state["password"]  # Clear password
        else:
            st.session_state["password_correct"] = False

    # First run or not yet logged in
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    # Show input for password
    st.write("## Welcome to File Analysis Assistant")
    st.write("Please enter one of the valid access codes to continue:")
    password = st.text_input(
        "Access Code:", 
        type="password", 
        on_change=password_entered, 
        key="password"
    )

    if not st.session_state["password_correct"]:
        if password:
            st.error("😕 Incorrect access code")
        return False
    
    return True

def main():
    if not check_password():
        return

    # Display which access code was used
    st.success(f"Access granted with code: {st.session_state.get('access_code', '')}")
    
    st.title("File Analysis Assistant")
    st.write("Upload your files for AI-powered analysis")

    # Add logout button
    if st.sidebar.button("Logout"):
        st.session_state["password_correct"] = False
        st.experimental_rerun()

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a file", 
        type=['txt', 'pdf', 'docx', 'csv', 'xlsx', 'png', 'jpg', 'jpeg']
    )

    if uploaded_file is not None:
        file_type = uploaded_file.type
        file_content = None

        # Process different file types
        try:
            if file_type == 'text/plain':
                file_content = uploaded_file.read().decode()
                st.write("### Text Content:")
                st.write(file_content[:1000] + "..." if len(file_content) > 1000 else file_content)

            elif file_type == 'application/pdf':
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                file_content = ""
                for page in pdf_reader.pages:
                    file_content += page.extract_text()
                st.write("### PDF Content:")
                st.write(file_content[:1000] + "..." if len(file_content) > 1000 else file_content)

            elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                doc = docx.Document(uploaded_file)
                file_content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                st.write("### Document Content:")
                st.write(file_content[:1000] + "..." if len(file_content) > 1000 else file_content)

            elif file_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
                df = pd.read_excel(uploaded_file)
                file_content = df.to_string()
                st.write("### Excel Content:")
                st.dataframe(df)

            elif file_type == 'text/csv':
                df = pd.read_csv(uploaded_file)
                file_content = df.to_string()
                st.write("### CSV Content:")
                st.dataframe(df)

            elif file_type in ['image/png', 'image/jpeg', 'image/jpg']:
                image = Image.open(uploaded_file)
                st.write("### Image Preview:")
                st.image(image, caption='Uploaded Image')
                # Convert image to bytes for OpenAI
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format=image.format)
                img_byte_arr = img_byte_arr.getvalue()
                file_content = "Image analysis will be performed using OpenAI's vision model"

            # AI Analysis Section
            if file_content:
                st.write("---")
                st.write("### AI Analysis")
                
                analysis_type = st.selectbox(
                    "What would you like to analyze?",
                    ["Summarize content", "Check grammar and style", "Extract key information", "Analyze sentiment"]
                )

                if st.button("Analyze"):
                    with st.spinner("Analyzing..."):
                        try:
                            if file_type in ['image/png', 'image/jpeg', 'image/jpg']:
                                # Use GPT-4 Vision for image analysis
                                response = openai.chat.completions.create(
                                    model="gpt-4-vision-preview",
                                    messages=[
                                        {
                                            "role": "user",
                                            "content": [
                                                {"type": "text", "text": f"Please {analysis_type.lower()} for this image:"},
                                                {"type": "image_url", "image_url": {"url": f"data:image/{file_type.split('/')[-1]};base64,{img_byte_arr}"}}
                                            ]
                                        }
                                    ]
                                )
                            else:
                                # Use GPT-4 for text analysis
                                response = openai.chat.completions.create(
                                    model="gpt-4-turbo-preview",
                                    messages=[
                                        {"role": "system", "content": f"You are an expert at {analysis_type.lower()}. Analyze the following content:"},
                                        {"role": "user", "content": file_content}
                                    ]
                                )
                            
                            st.write("#### Analysis Results:")
                            st.write(response.choices[0].message.content)
                            
                        except Exception as e:
                            st.error(f"Error during analysis: {str(e)}")

        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()
