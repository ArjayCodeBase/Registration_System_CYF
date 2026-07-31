# System Package Needed

pip install fastapi uvicorn sqlalchemy pymysql passlib[bcrypt] python-multipart email-validator

# To start server:
uvicorn main:app --reload  

# To stop server: 
Ctrl + C 

# System Environment 
python -m venv myenv
myenv\Scripts\activate
deactivate
