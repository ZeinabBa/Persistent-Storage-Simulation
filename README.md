# Persistent-Storage-Simulation
This repository contains a Python implementation of a simulation for a persistent storage system for container-based architectures. The simulation consists of a cluster of nodes that use consensus algorithms to achieve data consistency.
It aims to demonstrate how data is written to and read from a replicated data structure (RDS), as well as how data is managed and controlled by Storage Containers (SC). 


# Getting Started
To run the simulation, we recommend you to have a Linux operating system installed on your machine. You can download the latest version of Ubuntu from the [official website](https://ubuntu.com/download).

Once you have Linux installed, clone this repository to your local machine by running the following command in your terminal:


`git clone https://github.com/ZeinabBa/Persistent-Storage-Simulation.git`

* NOTE: Python version used to implement this simulator is: Python 3.10.6

# Usage and Description
The simulation files provided in this repository allows you to perform the following operations:

- Creating your own cluster with any number of nodes (lower limit is recommended to be 10)

- By creating each node, one SC will be automatically deployed on that node

- Deploying any type and number of applications with the upper limit of node's capacities currently existing the cluster as per defined earlier

- By creating a cluster of nodes and applications, one RDS will be created on each node. The size of the RDS is determined based on the total number of Applications in the cluster





# Instructions
To use the simulation files, please follow these instructions: 

1- Clone/download the repository

2- Make sure all files are located in one folder

3- If using windows, add the folder address to PATH

4- Open a CLI (PowerShell recommended for windows OS)

5- Run the command  `python cluster.py input_file output_file percentage_of_failure` $${\color{red}inputfile \space must \space be \space located \space in \space the \space same \space folder \space as \space the \space cluster.py \space file}$$
Replace `input_file` with the name of the input file you want to use, `output_file` with the desired name for the output log file, and `percentage_of_failure` with the desired percentage of nodes to simulate as failed (e.g. 10 for 10%).
  - NOTE: Please note that if output file name is not specified either in command line or in the main code then the new results will be added (not overwritten) to the results of the previous experiment.

6- Use the input files given in the repository or make your own input file using the python file called `json creator`
* NOTE: this an interactive program that needs user input to specify the details.

  a. Enter the number of nodes and specify the configuration of each node (You can add your own data for devices rather than what is given in the table in the paper)
  
  b. Make sure to enter all the requested entries such as data relevant to failure, SC, leader, etc.
  
  c. Repeat the above steps for applications (You can add any application specifications, not limited to the ones given in the table in the paper)
  
  d. When done, save the file with a `.json` or `.txt` extension in the same directory. (the default format that is automatically saved is `.json` and you can rename it to `.txt`)
  
  e. Use the created JSON file as the input file to run the simulation explained in item number 5
  
* A number of pre-created input files and their respected logs are available in the repository.

7- Use the file Outage.py to calculate outage of each component for each operation recorded in the log file.
  a- Make sure your have a log file to start with
  
  b- Run the command `python outage.py input_file output_file`
  
  * NOTE: It is very important to know that the input file in this specific command is the "log file" in Number 5, explained above and output file is different from the log generated before.

# Interpretation of log files
The simulation generates log files that contain the result of each operation. Here are some tips for interpreting the log files generated by the simulation:

- Each log file contains the result of one operation

- Synchronization times are given based on numbers (`sync 1`, `sync 2`, etc.)
  - NOTE: synchronization time calculated in the log files is the Response-time (on the paper) of the applications including application execution, data transfer and failure, recovery times for any entities.

- The biggest value is the worst case, the smallest is the best. There is also an average time calculated in the same file

- Each array is showing the data of one node

- Each value in each array is for one app

- A matrix of 30 columns and 20 rows means there are 20 nodes and 30 applications deployed on them

- By following the values on the matrix, you can see how the data changes after each iteration of application execution and how the cluster goes to sync (values of one array are horizontally equal to the other one.)

- Operation time is also given in the log file

- Failure details are also included 
  - The details are about failed entities, what stage, what component and if it is SC and App then what Node they where deployed on and if it is an application then which itteration the failure has occured.

# Examples with Images
Here is a screenshot of the JSON creator program and its interactive pannel:

![json_creator](https://github.com/ZeinabBa/Persistent-Storage-Simulation/blob/main/Pictures/JSON%20for%20inputfile%20creator.jpg?raw=true)

When the input file is saved run the command given in Step 5 (Instruction Section in this READ ME).
* NOTE: After adding Nodes you need to add Applications as the interactive pannel requests you.
Here is a screenshot of running program and when it's run:

![CLI_and_Program_RUN](https://github.com/ZeinabBa/Persistent-Storage-Simulation/blob/main/Pictures/Program%20Run.jpg?raw=true)

* NOTE: It is very improtant to add the files extentions if they have one. For instance if you save the JSON file as .txt then you need to enter the complete file name including its extention (.txt in this case).
* NOTE: As shown in this image output file is not specified, therefore, it writes in the deafult file: Syslog.txt (in the same folder). Details are mentioned in Step number 5.

Example fo input and output files are given in the folder named "Sample Test Codes and Log Files" in this repository. Files their names include the word "test" are input files and files their names inlcude the word"log" are output files.
