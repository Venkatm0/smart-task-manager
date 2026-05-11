CREATE TABLE users (

    id SERIAL PRIMARY KEY,

    username VARCHAR(100) NOT NULL,

    email VARCHAR(100) UNIQUE NOT NULL,

    password VARCHAR(200) NOT NULL

);

CREATE TABLE tasks (

    id SERIAL PRIMARY KEY,

    title VARCHAR(200) NOT NULL,

    description TEXT,

    priority VARCHAR(50),

    status VARCHAR(50),

    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    user_id INTEGER REFERENCES users(id)

);