-- Seeding script for AI Voice-to-SQL Generator
-- Creates tables and inserts sample data

DROP TABLE IF EXISTS employee_projects;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS departments;

-- 1. Departments Table
CREATE TABLE departments (
    department_id INT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL
);

-- 2. Employees Table
CREATE TABLE employees (
    employee_id INT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone_number VARCHAR(20),
    hire_date DATE,
    job_title VARCHAR(50) NOT NULL,
    salary DECIMAL(10, 2) NOT NULL,
    manager_id INT,
    department_id INT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

-- 3. Projects Table
CREATE TABLE projects (
    project_id INT PRIMARY KEY,
    project_name VARCHAR(100) NOT NULL,
    budget DECIMAL(15, 2) NOT NULL,
    start_date DATE,
    end_date DATE
);

-- 4. Employee Projects Table (Many-to-Many relationship)
CREATE TABLE employee_projects (
    employee_id INT,
    project_id INT,
    hours_worked INT DEFAULT 0,
    PRIMARY KEY (employee_id, project_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

-- ==========================================
-- Insert Seeding Data (Only if tables are empty)
-- ==========================================

-- Seeding Departments
INSERT INTO departments (department_id, department_name, location) VALUES
(1, 'Engineering', 'San Francisco'),
(2, 'Human Resources', 'New York'),
(3, 'Sales & Marketing', 'Chicago'),
(4, 'Finance', 'Boston'),
(5, 'Legal', 'Washington D.C.');

-- Seeding Employees
INSERT INTO employees (employee_id, first_name, last_name, email, phone_number, hire_date, job_title, salary, manager_id, department_id) VALUES
(101, 'Arjun', 'Mehta', 'arjun.mehta@company.com', '555-0101', '2021-03-15', 'Engineering Director', 145000.00, NULL, 1),
(102, 'Priya', 'Sharma', 'priya.sharma@company.com', '555-0102', '2022-06-01', 'Senior Software Engineer', 98000.00, 101, 1),
(103, 'Rahul', 'Nair', 'rahul.nair@company.com', '555-0103', '2023-01-10', 'Junior Developer', 65000.00, 101, 1),
(104, 'Sarah', 'Connor', 'sarah.connor@company.com', '555-0104', '2020-11-15', 'HR Manager', 85000.00, NULL, 2),
(105, 'Michael', 'Scott', 'michael.scott@company.com', '555-0105', '2019-04-01', 'Sales Manager', 90000.00, NULL, 3),
(106, 'Dwight', 'Schrute', 'dwight.schrute@company.com', '555-0106', '2020-02-15', 'Senior Sales Rep', 78000.00, 105, 3),
(107, 'Jim', 'Halpert', 'jim.halpert@company.com', '555-0107', '2021-08-20', 'Sales Representative', 62000.00, 105, 3),
(108, 'Pam', 'Beesly', 'pam.beesly@company.com', '555-0108', '2021-09-01', 'HR Assistant', 50000.00, 104, 2),
(109, 'Oscar', 'Martinez', 'oscar.martinez@company.com', '555-0109', '2018-05-12', 'Chief Accountant', 105000.00, NULL, 4),
(110, 'Kevin', 'Malone', 'kevin.malone@company.com', '555-0110', '2020-10-01', 'Accountant', 55000.00, 109, 4),
(111, 'Angela', 'Martin', 'angela.martin@company.com', '555-0111', '2019-07-22', 'Accounting Supervisor', 80000.00, 109, 4),
(112, 'Harvey', 'Specter', 'harvey.specter@company.com', '555-0112', '2015-06-15', 'Senior Legal Counsel', 160000.00, NULL, 5);

-- Seeding Projects
INSERT INTO projects (project_id, project_name, budget, start_date, end_date) VALUES
(501, 'Project Alpha (Web App)', 120000.00, '2026-01-01', '2026-12-31'),
(502, 'Project Beta (AI Model)', 250000.00, '2026-03-01', '2027-02-28'),
(503, 'Sales Campaign Q3', 45000.00, '2026-07-01', '2026-09-30'),
(504, 'Financial Audit 2026', 15000.00, '2026-10-01', '2026-12-15');

-- Seeding Employee Projects mapping
INSERT INTO employee_projects (employee_id, project_id, hours_worked) VALUES
(101, 501, 120),
(101, 502, 200),
(102, 501, 350),
(102, 502, 150),
(103, 501, 400),
(105, 503, 80),
(106, 503, 160),
(107, 503, 140),
(109, 504, 100),
(110, 504, 180),
(111, 504, 150);
