# AI-Based Autonomous Academic Decision System

## Project Description

The AI-Based Autonomous Academic Decision System is a Streamlit-based web application that helps educational institutions manage students, faculty, and academic performance using Machine Learning.

## Features

- Role-based Student, Faculty, and Admin login
- Student registration with administrator approval and no Gmail verification step
- Faculty self-registration with qualifications and requested courses
- Admin approval and section/year/semester assignment for faculty
- Student Management
- Faculty Management
- Academic Analytics
- Performance Prediction
- Risk Prediction
- Personalized recommendations saved to the student notification inbox
- Academic update emails to students when Gmail delivery is configured
- Report Generation

## Run the Application

Install the packages in `requirements.txt`, then start the app from the project root:

```powershell
streamlit run app.py
```

All Streamlit pages are stored in `dashboard/` and routed through `app.py`.

Configure these environment variables before starting Streamlit to enable real password-reset OTPs and academic alerts:

- `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`
- `TWILIO_MESSAGING_SERVICE_SID` or `TWILIO_FROM_NUMBER` for academic SMS alerts
- `EMAIL_ADDRESS` and `EMAIL_APP_PASSWORD` for student email alerts

Password-reset OTPs are sent to the registered email and mobile number. They expire after 10 minutes, allow five attempts, and are stored only as bcrypt hashes in the active server session. Student dashboard notifications record that a reset was requested but never include the OTP. Academic notifications remain in the student dashboard if SMS or email delivery is unavailable. Student semester registration does not collect real payment information or charge money.

## Technologies Used

- Python
- Streamlit
- SQLite
- Pandas
- NumPy
- Scikit-learn
- Joblib
- Bcrypt

## Folder Structure

- dashboard/
- dataset/
- preprocessing/
- models/
- reports/
- assets/

## Machine Learning Algorithms

- Decision Tree
- Random Forest
- Logistic Regression

## Developed For

Academic Decision Support System