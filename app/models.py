from app import mysql

def create_tables():
    cursor = mysql.connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(200) NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            content TEXT NOT NULL,
            author_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES users (id)
        )
    ''')
    mysql.connection.commit()
    cursor.close()

# Manual User class for authentication
class User:
    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.email = email
        self.password = password

    @staticmethod
    def get_by_id(user_id):
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT id, username, email, password FROM users WHERE id = %s', (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        if user_data:
            return User(*user_data)
        return None

    @staticmethod
    def get_by_email(email):
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT id, username, email, password FROM users WHERE email = %s', (email,))
        user_data = cursor.fetchone()
        cursor.close()
        if user_data:
            return User(*user_data)
        return None

    def check_password(self, password):
        return self.password == password
