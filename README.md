# Trade Compliance Monitor API
This project serves as my Capstone project for Udacitys' Full Stack Web Developer Nanodegree Program



## Background and requirements

Employees within certain types of companies operating on the Swedish financial market are required to:
- report all personal transactions in financial instruments.
- hold any profitable positions for at least 30 days before closing them.



The API will be called from a frontend by two distinct users.

An **Employee** will:
  - report her own trades.

A **Compliance Officer** will:
  - be shown an overview of whether any employees (and relevant trades) are violating rules.



## Misc improvements
- Lookup instrument name from ISIN by using https://www.openfigi.com/api
- Send email when violations occur.
- Build a frontend.



# Setting up the application

Execute:
```
virtualenv env
source env/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Configuration
Rename `config.py.example` and input apropriate values.

# Running the application
Execute:
 ```
 export FLASK_APP=tcm_app
 flask run
 ```

# Testing the application
Execute:
```bash
export EMPLOYEE_ROLE_ACCESS_TOKEN=<jwt_for_user_with_employee_role>
export CO_ROLE_ACCESS_TOKEN=<jwt_for_user_with_employee_role>
python -m unittest tests.test_api
```