pip install fastapi uvicorn sqlalchemy pymysql passlib[bcrypt] python-multipart email-validator


uvicorn main:app --reload  (to start server)

Ctrl + C (to stop server)

python -m venv myenv

myenv\Scripts\activate

deactivate

ngrok http 8000