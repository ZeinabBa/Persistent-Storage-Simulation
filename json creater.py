import json

# Create empty dictionary for node and application data
data = {}

# Add nodes
data["Nodes"] = []
num_nodes = int(input("Enter the number of nodes: "))
for i in range(num_nodes):
    node = {}
    node["NodeID"] = i
    node["CpuSpeed"] = float(input(f"Enter CPU speed for Node {i}: "))
    node["Ram"] = float(input(f"Enter RAM for Node {i}: "))
    node["Storage"] = float(input(f"Enter storage for Node {i}: "))
    node["Failure"] = False
    node["Item"] = "Node"
    node["Iteration"] = 1
    node["Stage"] = 1
    node["Leader"] = False
    data["Nodes"].append(node)

# Add applications
data["Applications"] = []
num_apps = int(input("Enter the number of applications: "))
for i in range(num_apps):
    app = {}
    app["AppID"] = i
    app["CpuSpeed"] = float(input(f"Enter CPU speed for Application {i}: "))
    app["Ram"] = float(input(f"Enter RAM for Application {i}: "))
    app["Storage"] = float(input(f"Enter storage for Application {i}: "))
    app["DeploymentTime"] = int(input(f"Enter deployment time for Application {i}: "))
    app["ExecutionTime"] = int(input(f"Enter execution time for Application {i}: "))
    app["NumberOfIterations"] = int(input(f"Enter number of iterations for Application {i}: "))
    app["Failure"] = False
    app["OnIteration"] = 1
    app["Stage"] = 1
    data["Applications"].append(app)

# Write data to JSON file
with open("node_and_application_data.json", "w") as outfile:
    json.dump(data, outfile, indent=4)