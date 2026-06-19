Coursework for Coventry University, now forwarded to my main github from the coventry github
# How to Use

1-Create virtual environment: python -m venv venv

2-Activate virtual environment: venv\Scripts\activate

3-Install dependencies: pip install -r requirements.txt

4-Initialize database: python init_db.py

5-Run application: python app.py

6-Open browser: http://127.0.0.1:5000

# Default Accounts to use

Admin: username: admin | password: admin123

Seller: username: seller1 | password: seller123

# TroubleShoot

If venv Doesn't work run this before trying again

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

Run on Python 3.14.0

# to run bandit

bandit -r app.py -f txt -o bandit-report.txt

# to run safety

safety check

safety check > safety-report.txt
