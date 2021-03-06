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
The API requires an authorization and permission mechanism and is handling this by a JSON Web Token (JWT). Illustrated by a live mock application running on Heroku a JWT can be requested either from a [Portal](https://trade-compliance-monitor.herokuapp.com/) using [Authorization Code Flow](https://auth0.com/docs/flows/concepts/auth-code) or from the [Swagger UI](https://trade-compliance-monitor.herokuapp.com/apidocs/) using [Implicit Flow](https://auth0.com/docs/flows/concepts/implicit). The JWT carries permissions to represent the two above mentioned roles.

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

For the live mock application running on Heroku any user logging in for the first time will be assigned the role **Employee** automatically. This is accomplished within the Auth0.com service (example code [here](https://community.auth0.com/t/how-do-i-add-a-default-role-to-a-new-user-on-first-login/25857)). Assigning a user the role **Compliance Officer** is done manually. Read section *Testing the application* for info on a dummy Compliance Officer.


## API Documentation
The API becomes "Swagger documented" when the application is installed and running. For the application running live on Heroku look [here](https://trade-compliance-monitor.herokuapp.com/apidocs/).


## Stack
* [python](https://www.python.org/) programming language
* [PostgreSQL](https://www.postgresql.org/) relational database
* [Auth0.com](https://auth0.com/) identity platform
* [Swagger UI](https://swagger.io/tools/swagger-ui/) API documenter

##### Dependencies
* `flasgger`, `Flask`, `marshmallow`, `pandas`, `python-jose`, `SQLAlchemy`. Please refer to `requirements.txt` or [dependency graph](https://github.com/erikgrenfors/trade-compliance-monitor/network/dependencies) for complete list.



# Setting up the application
_**NOTE**: to be able to fully set up and run your own project you have to sign up (free) for [Auth0.com](https://auth0.com/) authorization and follow their instructions on how to authorize an application and API._

Create a project folder named whatever you prefer and enter into it.
Within this folder, execute:

```bash
git clone https://github.com/erikgrenfors/trade-compliance-monitor.git .
virtualenv env
source env/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```
Note: `gunicorn` isn't required for running the application locally.



# Setting up local PostgreSQL database
If not already on your system, download and install [PostgreSQL](https://www.postgresql.org/download/).
Instructions below involves a user called `postgres`. If your user is named differently, change accordingly. And if you prefer a different database name than `trade_compliance_monitor_dev`, change accordingly.

##### To set environment variables automatically using provided bash file
```bash
source setup.sh
```
Please **NOTE** that environment variable `AUTH0_CLIENT_SECRET` is **NOT** set. It is a secret you'll be provided by auth0 when setting up your API.

##### To set environment variables manually
```bash
export DB_NAME="trade_compliance_monitor_dev"
export DATABASE_URL="postgresql://postgres@localhost:5432/${DB_NAME}"
export FLASK_APP="tcm_app"
export APP_SETTINGS="config.DevelopmentConfig"
export APP_BASE_URL="http://127.0.0.1:5000"
export AUTH0_CLIENT_SECRET="a_secret_will_be_provided_by_auth0_at_app_setup"
```

##### To setup database
```
dropdb -U postgres $DB_NAME
createdb -U postgres $DB_NAME
flask db upgrade
```



# Running the application
Make sure you are in the same shell session as when setting up the database, otherwise you will have to set the environment variables again.
```bash
flask run
```



# Testing the application

I suggest a new shell session for a clean slate testing. Having said that, instructions below will overwrite applicable environment variables.
```bash
export AUTH0_CLIENT_SECRET="a_secret_will_be_provided_by_auth0_at_app_setup"
```
```bash
source setup_test.sh
dropdb -U postgres $DB_NAME
createdb -U postgres $DB_NAME
flask db upgrade
```

For testing two JWT will be required. Both can be acquired at the live mock application running on Heroku [here](https://trade-compliance-monitor.herokuapp.com/). An `EMPLOYEE_ROLE_ACCESS_TOKEN` can be acquired by logging in by any user. A `CO_ROLE_ACCESS_TOKEN` can be acquired by logging in by using email **john.doe@example.com** and password **verySimple1**. Make sure to logout between each login.

Set environment variables for two JWT.
```bash
export EMPLOYEE_ROLE_ACCESS_TOKEN="jwt_for_user_with_employee_role"
export CO_ROLE_ACCESS_TOKEN="jwt_for_user_with_employee_role"
```

Run test.
```bash
python -m unittest tests.test_api
```



# Misc improvements
- Lookup instrument name from ISIN by using https://www.openfigi.com/api
- Send email when violations occur.
- Build a frontend.
