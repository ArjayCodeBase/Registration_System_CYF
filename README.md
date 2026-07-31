# System Package Needed

pip install fastapi uvicorn sqlalchemy pymysql passlib[bcrypt] python-multipart email-validator

# to start server:
uvicorn main:app --reload  

# to stop server: 
Ctrl + C 

# System Environment 
python -m venv myenv
myenv\Scripts\activate
deactivate
