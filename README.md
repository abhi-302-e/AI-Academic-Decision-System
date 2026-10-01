# AI-Based Autonomous Academic Decision System

**Domain:** Artificial Intelligence, Machine Learning, and Data Analytics

**Real-world application:** Self-learning ERP intelligence

**Theme:** AI Academic Governance

**Faculty guides:** Mrs. Madhusmita Majhi and Dr. D. Krishna Madhuri

## Project Overview

Educational institutions collect attendance, assessment, assignment, and learning-activity data, but many academic decisions are still manual. This Streamlit application organizes student and faculty records, analyzes academic performance, estimates risk, and presents recommendations through role-based dashboards.

The system is a decision-support tool. Predictions should inform, not replace, faculty judgment or institutional policy.

## Problem and Objectives

- Organize academic profiles, courses, timetables, marks, and attendance in SQLite.
- Identify students who may need academic support.
- Provide analytics for administrators and faculty.
- Generate personalized intervention recommendations.
- Give students access to registration, results, and notifications.

## Architecture

```text
+-------------------------------+
| Excel schedules and records   |
+---------------+---------------+
                |
                v
+-------------------------------+
| SQLite academic database      |
+---------------+---------------+
                |
                v
+-------------------------------+
| Preprocessing and features    |
+---------------+---------------+
                |
                v
+-------------------------------+
| Performance and risk models   |
+---------------+---------------+
                |
                v
+-------------------------------+
| Recommendations and alerts    |
+---------------+---------------+
                |
                v
| Admin | Faculty | Student UI  |
```

## User Workflows

### Administrator

- Review and approve or reject student registrations, individually or in bulk.
- Review faculty registrations and approve timetable-derived faculty in bulk.
- Manage student year, semester, section, academic profile, marks, and attendance.
- Manage faculty profile, account status, course assignments, and schedule requests.
- Import and publish course and timetable workbooks.
- Reset account passwords, view analytics, and export student reports.

Passwords are stored as bcrypt hashes. Administrators can reset passwords but cannot read existing or newly set passwords.

### Faculty

- Self-register with qualifications, experience, and requested courses; accounts need Admin approval.
- Request a published course, section A–J, weekday, room, and a 50-minute period.
- Record each enrolled student's attendance once per scheduled class session and date.
- Enter Internal marks out of 60 and External marks out of 40.
- Send academic updates to the student dashboard, email, and SMS when delivery services are configured.

### Student

- Register and wait for Admin approval.
- View their profile, year, semester, assigned section, marks, attendance, predictions, recommendations, and notifications.
- Register for a published semester using their assigned section. Sections A–J are capped at 75 students each.
- Request a password reset using the mobile/email registered to their account.

### Grading and Payment

- **Internal:** assignments, quizzes, and mid exam; maximum 60 marks.
- **External:** end-semester exam; maximum 40 marks.
- **Total:** Internal + External; maximum 100 marks.
- Semester payment is simulated. The app does not collect bank/card data or charge money.

## Machine Learning

The repository includes Decision Tree, Random Forest, and Logistic Regression workflows. Performance categories are Fail, Pass, and Distinction; risk categories are Low, Medium, and High. Recommendations use performance and risk results to suggest possible support actions.

Training/evaluation scripts are in `models/`. Cleaning and feature engineering are in `preprocessing/`. Included datasets and the current local roster are synthetic demo data; performance on synthetic data does not demonstrate real-world accuracy. Production use requires approved representative data, validation, and fairness review.

## Import Courses and Timetable

1. Sign in as Admin and open **Course Management**.
2. Upload the Master course workbook and the Sectionwise timetable workbook.
3. Review the preview counts, warnings, and conflicting periods.
4. Confirm the academic batch and choose **Import and publish courses and timetable**.

The importer preserves repeated catalog codes across programs and avoids duplicate records on re-import. Conflicting section-period assignments are skipped and reported. The supplied filenames indicate 2026–2027, while timetable sheets contain 2025–2026 headings; verify the warning before publishing.

## Local Demo Data

The current local SQLite database has 500 synthetic student records, 79 timetable-derived faculty profiles, 63 course offerings, 9 published structures, 27 sections, and 472 timetable periods. Student contact information is placeholder/demo data; it must not be used for real notifications. Timetable-derived faculty accounts require Admin review and verified contact details before real use.

The imported schedule covers B.Tech Years II–IV. The current demo students are Year I/Semester 1, so a Year I curriculum workbook is required before they can register for matching courses.

## Run Locally

From the project root, install dependencies and start Streamlit:

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

The local app opens at [http://localhost:8501](http://localhost:8501). All Streamlit pages are routed from `app.py` and stored in `dashboard/`. The SQLite database is `dataset/student.db`.

## Email and SMS Setup

Dashboard notifications are saved locally even if external delivery is unavailable. For real delivery, configure these environment variables before starting the app. Keep secrets out of source control and never share them in chat.

- `EMAIL_ADDRESS` and `EMAIL_APP_PASSWORD` for Gmail SMTP.
- `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` for Twilio.
- `TWILIO_MESSAGING_SERVICE_SID` or `TWILIO_FROM_NUMBER` for SMS.

Password-reset OTPs are sent to the registered email and mobile number, expire after 10 minutes, and allow five attempts. The OTP is not shown in dashboard notifications. Passwords remain one-way bcrypt hashes.

## Project Structure

```text
app.py                         Streamlit router and database startup
auth.py                        Authentication and role checks
database.py                    SQLite schema and academic operations
prediction.py                  Model inference
recommendation_engine.py       Intervention recommendations
email_service.py               Gmail delivery
sms_service.py                 SMS delivery
dashboard/                     Admin, Faculty, Student, Reports, Analytics
preprocessing/                 Cleaning, features, workbook parser
models/                        Training scripts, saved models, evaluations
dataset/                       SQLite DB, datasets, academic workbooks
assets/                        Shared styling
```

## Learning Outcomes and Deliverables

This project demonstrates educational-data preprocessing, predictive analytics, model evaluation, dashboard design, and AI-supported academic governance. Suggested deliverables are source code, dataset, trained models, Streamlit dashboard, project report, presentation, demo video, and repository.

Future enhancements include explainable AI, LMS/ERP integration, live attendance systems, validated institution data, fairness monitoring, and audited notifications.

## Links

- Repository: [AI Academic Decision System](https://github.com/abhi-302-e/AI-Academic-Decision-System)
