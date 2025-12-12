

CREATE DATA_SUBJECT TABLE students (
  email TEXT PRIMARY KEY,
  name TEXT
);





CREATE TABLE assignments (
  ID INT AUTO_INCREMENT,
  Name TEXT,

  
  PRIMARY KEY(ID)

  

  
);



CREATE TABLE submissions (
  ID INT AUTO_INCREMENT,
  student_id TEXT,
  assignment_id INT,
  answer TEXT,

  
  PRIMARY KEY(ID),

  
  FOREIGN KEY (student_id) OWNED_BY students(email),

  
  FOREIGN KEY (assignment_id) REFERENCES assignments(ID)
);



-- Ownership: rows in submissions belong to data subject students
-- via foreign key column student_id.


