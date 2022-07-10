import streamlit as st
import pandas as pd
import base64
import time,datetime
from pyresparser import ResumeParser
import pymysql
import re



def get_table_download_link(df,filename,text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    # href = f'<a href="data:file/csv;base64,{b64}">Download Report</a>'
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    # pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf">'
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def show_doc(file_path):
    doc_display = F'<iframe src="//view.officeapps.live.com/op/view.aspx?src={file_path}" width="700" height="1000"></iframe>'
    st.markdown(doc_display, unsafe_allow_html=True)

connection = pymysql.connect(host='localhost',user='root',password='Erw9jujw5er69rt!!',db='sra')
cursor = connection.cursor()

def insert_data(name,email,timestamp, no_of_pages, skills):
    DB_table_name = 'user_data'
    insert_sql = "insert into " + DB_table_name + """
    values (0,%s,%s,%s,%s,%s)"""
    rec_values = (name, email, timestamp, str(no_of_pages), skills)
    cursor.execute(insert_sql, rec_values)
    connection.commit()




st.set_page_config(
   page_title="Smart Resume Analyzer",
)

st.markdown(""" <style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style> """, unsafe_allow_html=True)


def run():
    st.title("Resume Parser Project")
    st.sidebar.markdown("# Choose User")
    activities = ["Normal User", "Recruiter"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    # st.sidebar.markdown(link, unsafe_allow_html=True)

    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS SRA;"""
    cursor.execute(db_sql)

    # Create table
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                     Name varchar(100) NOT NULL,
                     Email_ID VARCHAR(50) NOT NULL,
                     Timestamp VARCHAR(50) NOT NULL,
                     Page_no VARCHAR(5) NOT NULL,
                     Actual_skills VARCHAR(300) NOT NULL,
                     PRIMARY KEY (ID));
                    """
    cursor.execute(table_sql)
    if choice == 'Normal User':
        # st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>* Upload your resume, and get smart recommendation based on it."</h4>''',
        #             unsafe_allow_html=True)
        file = st.file_uploader("Choose your Resume", type=["pdf", "doc", "docx", "txt"])
        if file is not None:
            # with st.spinner('Uploading your Resume....'):
            #     time.sleep(4)

            save_image_path = './Uploaded_Resumes/'+file.name
            with open(save_image_path, "wb") as f:
                f.write(file.getbuffer())
            if file.name.endswith('pdf'):
                show_pdf(save_image_path)
            '''else:
                show_doc(save_image_path)'''
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                ## Get the whole resume data

                st.header("**Resume Analysis**")
                st.success("Hello "+ resume_data['name'])
                st.subheader("**Your Basic info**")
                try:
                    st.text('Name: '+resume_data['name'])
                    st.text('Email: ' + resume_data['email'])
                    st.text('Contact: ' + resume_data['mobile_number'])
                    st.text('Resume pages: '+str(resume_data['no_of_pages']))
                    st.text('Skills: ' + str(resume_data['skills']))

                except:
                    pass

                #
                ## Insert into table
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date+'_'+cur_time)
                insert_data(resume_data['name'], resume_data['email'], timestamp, str(resume_data['no_of_pages']), str(resume_data['skills']))
            else:
                st.error('Something went wrong..')
    else:
        ## Admin Side
        st.success('Welcome to Recruiter Side')
                # Display Data
        cursor.execute('''SELECT*FROM user_data''')
        data = cursor.fetchall()
        st.header("**User's👨‍💻 Data**")
        
        df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Timestamp', 'Total Page', 'Actual Skills'])

        test = []
        selected_skills = df['Actual Skills'].unique()

        for x in selected_skills:
            myVal = filter(lambda y : y not in ["[", "]", "'"], x)
            myVal = "".join(myVal)
            myVal = myVal.split(",")
            for i in myVal:
                test.append(i.strip())
            
        test = set(test)

        mySkills = st.sidebar.multiselect('Skills', test)
        print(mySkills)

        def Filter(myList):
            if mySkills == []:
                return True
            for x in mySkills:
                if x in myList:
                    return True

            return False
        
        filtered_df = df[df['Actual Skills'].apply(lambda x : Filter(x))]
        pd.set_option("display.max_rows", None, "display.max_columns", None)
 


        st.dataframe(filtered_df)
        st.markdown(get_table_download_link(df,'User_Data.csv','Download Report'), unsafe_allow_html=True)
        ## Admin Side Data
        query = 'select * from user_data;'
        plot_data = pd.read_sql(query, connection)
run()