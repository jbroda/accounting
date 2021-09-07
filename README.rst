======================
Accounting Application
======================

Working Environment
-------------------

Perform the following steps:

#. Download and install Elastic Search from http://www.elasticsearch.org/download/:

    - unzip elasticsearch-1.x.x.zip
    
    - set JAVA_HOME to the location of 'java.exe'
    
    - type 'start elasticsearch-1.x.x\\bin\\elasticsearch.bat'
    
    |

#. Download and install PostgreSQL 9.6 from http://www.postgresql.org/download/:

    - add 'C:\\Program Files\\PostgreSQL\\9.6\\bin' to PATH

    - create a new database user with the username 'hiddenpond':
       - createuser -U postgres hiddenpond
    
    - set the password for 'hiddenpond' from the psql shell:
       - psql -U postgres
       - psql=# alter user hiddenpond with encrypted password '<password>';        
       
    - make 'hiddenpond' a super user:
       - psql -U postgres
       - psql=# alter user hiddenpond superuser;       
       
    - create a database called 'hiddenpond_db' with the 'hiddenpond' super user:
       - createdb -U hiddenpond hiddenpond_db   
   |
                 
#. Download and install Python 2.7.x from http://www.python.org/downloads/

#. Download and install Git from http://git-scm.com/downloads

#. Download and install Microsoft Visual C++ Compiler for Python 2.7 from http://aka.ms/vcpython27

#. mkdir hp

#. cd hp

#. run 'git clone https://mihamih@bitbucket.org/hiddenpond/accounting.git'

#. cd accounting

#. download and install Pip from http://pip.readthedocs.org/en/latest/installing.html:

   - python.exe get-pip.py   
   |   

#. download and install Virtualenv: 

   - pip.exe install virtualenv
   |   

#. create a virtual environment

   - virtualenv.exe venv
   |   

#. activate the virtual environment:

   - venv\\scripts\\activate.bat
   |   

#. install required packages with Pip:

   - pip.exe install -r requirements\\local.txt
   |   

#. type 'sync_db.bat deb'

#. Restore the database from a file. In a Git Bash shell, from the 'accounting' directory:
 
   - cd db

   - ./db_restore.sh rel_dump__<date>__<time>.sql.gz
   |   

#. type 'run_deb.bat'
