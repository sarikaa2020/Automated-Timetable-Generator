# Automated Timetable Generator

An intelligent academic scheduling system designed to automatically generate optimized timetables while minimizing clashes and improving schedule quality. The system applies algorithmic optimization techniques to efficiently allocate classes, teachers, and time slots under real-world constraints.

## Key Features

- Automated timetable generation using optimization algorithms  
- Teacher and class clash detection with validation  
- Teacher-wise timetable visualization  
- Timetable quality evaluation using defined metrics  
- Graphical analysis of timetable performance  
- Clean, modular, and scalable code structure  

## Technology Stack

- Python  
- Genetic Algorithm for optimization  
- Data processing and visualization libraries  
- HTML for timetable visualization  

## Project Overview

The system models timetable generation as a constrained optimization problem. A genetic algorithm iteratively improves schedule quality by evaluating fitness metrics and reducing conflicts. Validation modules ensure clash-free schedules, while visualization components present the generated timetables in an interpretable format.

## Project Structure

Automated-Timetable-Generator/
├── data/ # Input datasets
├── visualization/ # Timetable visualizations
├── timetable_ga.py # Genetic algorithm implementation
├── validation.py # Clash detection and validation
├── metrics.py # Timetable quality evaluation


1. Clone the repository:
   git clone https://github.com/sarikaa2020/Automated-Timetable-Generator.git
2. Navigate to the project directory:
   cd Automated-Timetable-Generator
3. Run the timetable generator:
   python timetable_ga.py

Future Enhancements:

- Web-based timetable management interface

- Support for multiple departments and institutions

- Dynamic constraint customization

- Database integration for large-scale deployment


Author:

Sarika
GitHub: https://github.com/sarikaa2020

This project demonstrates strong proficiency in algorithm design, optimization techniques, and Python-based system development.
