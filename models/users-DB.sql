CREATE DATABASE users_hack; -- Create a new database
USE users_hack; 


CREATE TABLE users_hack (
    UserID INT PRIMARY KEY,
    Username VARCHAR(50),
    Password VARCHAR(255),
    UserType ENUM('Student', 'Teacher') NOT NULL
);


INSERT INTO users_hack (UserID, Username, Password, UserType) VALUES
    (1, 'alanka', 'pass', 'Student'),
    (2, 'jpatel', 'pass', 'Teacher');
    
SELECT * FROM users_hack

