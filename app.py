import streamlit as st
import pandas as pd
import plotly.express as px
from github import Github
import datetime
import smtplib
from email.message import EmailMessage
import io

# Initialize an empty DataFrame
if 'df_applications' not in st.session_state:
    st.session_state.df_applications = pd.DataFrame(columns=['Application Date', 'Company', 'Position', 'Platform', 'Salary Range', 'Status', 'CV File'])

# Helper functions
def update_status(index, new_status):
    st.session_state.df_applications.at[index, 'Status'] = new_status

def generate_summary(df):
    status_counts = df['Status'].value_counts()
    return status_counts

def plot_summary(summary):
    fig = px.pie(names=summary.index, values=summary.values, title='Application Status Distribution')
    fig.update_traces(textinfo='percent+label', pull=[0.1]*len(summary))
    st.plotly_chart(fig, use_container_width=True)

def download_csv(df):
    return df.to_csv(index=False)

def send_email(subject, body, to_email, attachment=None):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = 'your_email@example.com'  # Replace with your email
    msg['To'] = to_email
    
    if attachment:
        # Attach the CSV file with appropriate MIME type
        msg.add_attachment(attachment, filename='weekly_job_applications.csv', mimetype='text/csv')

    try:
        with smtplib.SMTP('smtp.example.com', 587) as server:  # Replace with your SMTP server
            server.starttls()
            server.login('your_email@example.com', 'your_password')  # Replace with your email and password
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

# Streamlit app
st.title('Job Application Dashboard')
st.markdown("<style>body {font-family: 'Arial', sans-serif;}</style>", unsafe_allow_html=True)

# User input for new job application
st.subheader('Add New Job Application')
with st.form(key='application_form'):
    company = st.text_input('Company Name')
    job_title = st.text_input('Job Title')
    applied_date = st.date_input('Applied Date', min_value=datetime.date(2000, 1, 1))
    platform = st.text_input('Platform Applied On')
    salary_range = st.text_input('Salary Range')
    status = st.selectbox('Status', options=['Applied', 'Interview', 'Offer', 'Rejected'])
    cv_file = st.file_uploader('Upload CV (optional)', type=['pdf', 'docx'])
    
    submit_button = st.form_submit_button(label='Add Application')

    if submit_button:
        # Prepare data for new application
        new_application = {
            'Application Date': applied_date,
            'Company': company,
            'Position': job_title,
            'Platform': platform,
            'Salary Range': salary_range,
            'Status': status,
            'CV File': cv_file.name if cv_file else ''
        }
        
        # Create DataFrame for new application and concatenate with existing DataFrame
        new_application_df = pd.DataFrame([new_application])
        st.session_state.df_applications = pd.concat([st.session_state.df_applications, new_application_df], ignore_index=True)
        st.success('Job application added successfully!')

# Display job application data
st.subheader('Job Applications')
st.dataframe(st.session_state.df_applications, use_container_width=True)

# Amend status of an existing application
st.subheader('Amend Application Status')
if not st.session_state.df_applications.empty:
    st.write("Select an application to amend its status:")
    application_index = st.selectbox('Select Application Index to Amend', options=st.session_state.df_applications.index)
    new_status = st.selectbox('Select New Status', options=['Applied', 'Interview', 'Offer', 'Rejected'], key='status_update')
    
    if st.button('Amend Status'):
        update_status(application_index, new_status)
        st.success(f"Status amended to {new_status}")

# Generate and display summary
st.subheader('Application Summary')
summary = generate_summary(st.session_state.df_applications)
plot_summary(summary)

# Download CSV
st.subheader('Download CSV Reports')
today = datetime.date.today()
week_start = today - pd.to_timedelta(today.weekday(), unit='D')

# Filter Data
df_weekly = st.session_state.df_applications[st.session_state.df_applications['Application Date'] >= week_start]
df_monthly = st.session_state.df_applications[st.session_state.df_applications['Application Date'] >= today.replace(day=1)]

# Generate and save reports
weekly_csv = download_csv(df_weekly)
monthly_csv = download_csv(df_monthly)

st.download_button(
    label='Download Weekly Report',
    data=weekly_csv,
    file_name='weekly_job_applications.csv',
    mime='text/csv'
)

st.download_button(
    label='Download Monthly Report',
    data=monthly_csv,
    file_name='monthly_job_applications.csv',
    mime='text/csv'
)

# GitHub Integration
st.subheader('Track GitHub Projects')
github_token = st.text_input('Enter your GitHub token', type='password', help='Generate a GitHub token with repo access from your GitHub settings.')

if github_token:
    try:
        g = Github(github_token)
        user = g.get_user()
        repos = user.get_repos()
        repo_list = [repo.name for repo in repos]
        st.write('Your GitHub Repositories:')
        st.write(repo_list)

        repo_name = st.selectbox('Select a repository to view details', options=repo_list)
        if repo_name:
            repo = g.get_repo(f"{user.login}/{repo_name}")
            st.write(f"Repository {repo_name} details:")
            st.write(f"Stars: {repo.stargazers_count}")
            st.write(f"Forks: {repo.forks_count}")
            st.write(f"Open Issues: {repo.open_issues_count}")
    except Exception as e:
        st.error(f"Failed to fetch GitHub data: {e}")

# Send Weekly Report via Email
st.subheader('Send Weekly Report via Email')
to_email = st.text_input('Recipient Email Address', 'your_email@example.com')  # Default to your email

if st.button('Send Weekly Report'):
    success = send_email(
        subject='Weekly Job Application Report',
        body='Please find attached the weekly job application report.',
        to_email=to_email,
        attachment=weekly_csv
    )
    if success:
        st.success('Weekly report sent successfully!')
