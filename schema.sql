DROP DATABASE IF EXISTS roundtable;
CREATE DATABASE roundtable;
USE roundtable;

CREATE TABLE Users (
  user_id int4 AUTO_INCREMENT,
  email varchar(255) UNIQUE,
  password varchar(255),
  username varchar(255),
  u_fname varchar(255),
  u_lname varchar(255),
  profile_url varchar(255),
  year_of_grad int4,
  university varchar(255),

  CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Courses (
  course_id int4 AUTO_INCREMENT,
  user_id int4,

  course_title varchar(255),
  course_number varchar(255),
  CONSTRAINT courses_pk PRIMARY KEY (course_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE User_Has_Courses (
  uc_id int4 AUTO_INCREMENT,
  user_id int4,
  course_id int4,

  INDEX upid_idx (user_id),
  CONSTRAINT user_has_courses_pk PRIMARY KEY (uc_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE
);


CREATE TABLE Messages (
  message_id int4 AUTO_INCREMENT,
  user_id int4,
  content varchar(255),
  creation_date datetime DEFAULT NOW(),
  time_interval varchar(255),

  CONSTRAINT messages_pk PRIMARY KEY (message_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE Map (
  map_id int4 AUTO_INCREMENT,
  user_id int4,
  message_id int4,

  latitude varchar(255),
  longitude varchar(255),
  message text,

  CONSTRAINT map_pk PRIMARY KEY (map_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (message_id) REFERENCES Messages(message_id) ON DELETE CASCADE
);
