# Trade Compliance Monitor API
This project serves as my Capstone project for Udacitys' Full Stack Web Developer Nanodegree Program



## Background and requirements

Employees within certain types of companies operating on the Swedish financial market are required to:
* report all personal transactions in financial instruments.
* hold any profitable positions for at least a month before closing them.



The API will be called from a frontend by users with two distinct roles.

An **Employee** will:
* report,
* list,
* change,
* delete her own trades

A **Compliance Officer** will:
* be shown an overview of whether any employees (and relevant trades) are violating rules.



## Authorization, Permissions and Roles

The API requires an authorization and permission mechanism and is handling this by a JSON Web Token (JWT). Illustrated by a live application running on Heroku a JWT can be requested either from a [Portal](https://erigre.herokuapp.com/) using [Authorization Code Flow](https://auth0.com/docs/flows/concepts/auth-code) or from the [Swagger UI](https://erigre.herokuapp.com/apidocs/) using [Implicit Flow](https://auth0.com/docs/flows/concepts/implicit). The JWT carries permissions to represent the two above mentioned roles.

Permissions:

* **Employee**
  * post:trades
  * get:trades
  * patch:trades
  * delete:trades
  * get:violations


* **Compliance Officer** (in *addition* to above)
  * get:all-trades
  * get:all-violations

For the application running live on Heroku any user logging in for the first time will be assigned the role **Employee** automatically. This is accomplished within the Auth0.com service (example code [here](https://community.auth0.com/t/how-do-i-add-a-default-role-to-a-new-user-on-first-login/25857)). Assigning a user the role **Compliance Officer** is done manually.


## API Documentation

The API becomes "Swagger documented" when the application is installed and running. For the application running live on Heroku look [here](https://erigre.herokuapp.com/apidocs/).


## Stack

* [python](https://www.python.org/) programming language
* [PostgreSQL](https://www.postgresql.org/) relational database
* [Auth0.com](https://auth0.com/) identity platform
* [Swagger UI](https://swagger.io/tools/swagger-ui/) API documenter

##### Dependencies

* Please refer to `requirements.txt`


# Setting up the application

Create a project folder named whatever you prefer.
Within this folder, execute:

```
virtualenv env
source env/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

# Setting up local PostgreSQL database
If not already on your system, download and install [PostgreSQL](https://www.postgresql.org/download/)
Instructions below involves a user called "postgres". If your user is named differently, change accordingly. If you prefer a different database name than "trade_compliance_monitor_dev", change accordingly.
Execute:

```bash
export DB_NAME=trade_compliance_monitor_dev
export DATABASE_URL="postgresql://postgres@localhost:5432/${DB_NAME}"
dropdb -U postgres $DB_NAME
createdb -U postgres $DB_NAME
export FLASK_APP=tcm_app
flask db init
flask db migrate
flask db upgrade
```


# Running the application
Example below uses development configuration.
Execute:
```bash
export APP_SETTINGS="config.DevelopmentConfig"
export AUTH0_CLIENT_SECRET="a_secret_will_be_provided_by_auth0_at_app_setup"
export APP_BASE_URL="http://127.0.0.1:5000"
flask run
```


# Testing the application
Execute:
```bash
export EMPLOYEE_ROLE_ACCESS_TOKEN=<jwt_for_user_with_employee_role>
export CO_ROLE_ACCESS_TOKEN=<jwt_for_user_with_employee_role>
python -m unittest tests.test_api
```


# Misc improvements

- Lookup instrument name from ISIN by using https://www.openfigi.com/api
- Send email when violations occur.
- Build a frontend.
