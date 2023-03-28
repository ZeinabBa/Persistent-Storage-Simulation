import re

log_file_path = "path/to/log/file.log"

# Regular expression patterns to match the relevant information in the log file
app_pattern = re.compile(r"App = (\d+)")
node_pattern = re.compile(r"nodeId: (\d+)")
stage_pattern = re.compile(r"Stage: (\d+)")
time_pattern = re.compile(r"\d+\.\d+")

# Dictionaries to store the outage times for each node, application, and SC
node_outages = {}
app_outages = {}
sc_outages = {}

# Open the log file for reading
with open(log_file_path, "r") as log_file:
    # Read each line of the log file
    for line in log_file:
        # Check if the line contains information about an application outage
        if "App =" in line:
            # Extract the application ID from the line
            app_id = int(app_pattern.search(line).group(1))
            # Check if the application outage has ended
            if "set to fail" not in line:
                # Extract the time the application outage ended from the line
                end_time = float(time_pattern.search(line).group())
                # Calculate the duration of the outage
                duration = end_time - start_time
                # Add the duration of the outage to the total outage time for the application
                app_outages[app_id] = app_outages.get(app_id, 0) + duration
            else:
                # Extract the node ID from the line
                node_id = int(node_pattern.search(line).group(1))
                # Extract the stage number from the line
                stage = int(stage_pattern.search(line).group(1))
                # Extract the time the application outage started from the line
                start_time = float(time_pattern.search(line).group())
                # Add the start time of the outage to the node's outage dictionary
                node_outages.setdefault(node_id, {}).setdefault(stage, []).append(start_time)

        # Check if the line contains information about a node outage
        elif "nodeId:" in line:
            # Extract the node ID from the line
            node_id = int(node_pattern.search(line).group(1))
            # Extract the stage number from the line
            stage = int(stage_pattern.search(line).group(1))
            # Extract the time the node outage started or ended from the line
            time = float(time_pattern.search(line).group())
            # Check if the node outage has ended
            if "rds = [" in line:
                # Get the start time of the outage from the node's outage dictionary
                start_time = node_outages[node_id][stage].pop()
                # Calculate the duration of the outage
                duration = time - start_time
                # Add the duration of the outage to the total outage time for the node
                node_outages.setdefault(node_id, {}).setdefault("total", 0)
                node_outages[node_id]["total"] += duration
            else:
                # Add the start time of the outage to the node's outage dictionary
                node_outages.setdefault(node_id, {}).setdefault(stage, []).append(time)

        # Check if the line contains information about an SC outage
        elif "SCId:" in line:
            # Extract the SC ID from the line
            sc_id = int(re.search(r"SCId: (\d+)", line).group(1))
            # Extract the time the SC outage started or ended from the line
            time = float(time_pattern.search(line).group())
            # Check if the SC outage has ended

