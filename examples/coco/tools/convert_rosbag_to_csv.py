# source : https://github.com/ros2/rosbag2/issues/473#issuecomment-669509525
# modified for execution of crazyflie ROS bag files

import glob
import os
import sqlite3
from argparse import ArgumentParser
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message

matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42

sns.set_theme(style="ticks", rc={"legend.title_fontsize": 15})  # "figure.figsize": (10, 4)
sns.set_style({"font.family": "serif", "font.serif": "Times New Roman", "font.scale": 5})


class BagFileParser:
    def __init__(self, bag_file):
        self.conn = sqlite3.connect(bag_file)
        self.cursor = self.conn.cursor()

        ## create a message type map
        topics_data = self.cursor.execute("SELECT id, name, type FROM topics").fetchall()
        self.topic_type = {name_of: type_of for id_of, name_of, type_of in topics_data}
        self.topic_id = {name_of: id_of for id_of, name_of, type_of in topics_data}
        self.topic_msg_message = {
            name_of: get_message(type_of) for id_of, name_of, type_of in topics_data
        }

    def __del__(self):
        self.conn.close()

    # Return [(timestamp0, message0), (timestamp1, message1), ...]
    def get_messages(self, topic_name):
        topic_id = self.topic_id[topic_name]
        # Get from the db
        rows = self.cursor.execute(
            "SELECT timestamp, data FROM messages WHERE topic_id = {}".format(topic_id)
        ).fetchall()
        # Deserialise all and timestamp them
        return [
            (timestamp, deserialize_message(data, self.topic_msg_message[topic_name]))
            for timestamp, data in rows
        ]


def createDataFrameFromBag(bag_file, cf_id: int = 10):
    # read out bagfile with BagFileParser (source to github given above)
    parser = BagFileParser(bag_file)

    # get the /tf data which includes cf positions
    trajectory = parser.get_messages("/tf")

    # timestamps of bag
    timestamps = []

    # state estimation data (including position and velocity estimations in global frame)
    stateEstimateX = []
    stateEstimateY = []
    stateEstimateZ = []
    stateEstimateVX = []
    stateEstimateVY = []
    stateEstimateVZ = []

    # PID target position
    posCtltargetX = []
    posCtltargetY = []
    posCtltargetZ = []
    posCtltargetVX = []
    posCtltargetVY = []
    posCtltargetVZ = []

    # kalman Data (Estimate and Covariance)
    kalmanStateX = []
    kalmanStateY = []
    kalmanStateZ = []
    kalmanVarX = []
    kalmanVarY = []
    kalmanVarZ = []

    # get msgs from rosbag
    stateEstimate = parser.get_messages(f"/cf{cf_id}/stateEstimate")
    posCtltarget = parser.get_messages(f"/cf{cf_id}/pid")
    kalman = parser.get_messages(f"/cf{cf_id}/kalman")

    for i in range(len(stateEstimate) - 1):
        timestamps.append(stateEstimate[i][0])
        stateEstimateX.append(stateEstimate[i][1].values[0])
        stateEstimateY.append(stateEstimate[i][1].values[1])
        stateEstimateZ.append(stateEstimate[i][1].values[2])
        stateEstimateVX.append(stateEstimate[i][1].values[3])
        stateEstimateVY.append(stateEstimate[i][1].values[4])
        stateEstimateVZ.append(stateEstimate[i][1].values[5])

        posCtltargetX.append(posCtltarget[i][1].values[0])
        posCtltargetY.append(posCtltarget[i][1].values[1])
        posCtltargetZ.append(posCtltarget[i][1].values[2])

        posCtltargetVX.append(posCtltarget[i][1].values[3])
        posCtltargetVY.append(posCtltarget[i][1].values[4])
        posCtltargetVZ.append(posCtltarget[i][1].values[5])

        kalmanStateX.append(kalman[i][1].values[0])
        kalmanStateY.append(kalman[i][1].values[1])
        kalmanStateZ.append(kalman[i][1].values[2])
        kalmanVarX.append(kalman[i][1].values[3])
        kalmanVarY.append(kalman[i][1].values[4])
        kalmanVarZ.append(kalman[i][1].values[5])

    data_df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "stateEstimateX": stateEstimateX,
            "stateEstimateY": stateEstimateY,
            "stateEstimateZ": stateEstimateZ,
            "stateEstimateVX": stateEstimateVX,
            "stateEstimateVY": stateEstimateVY,
            "stateEstimateVZ": stateEstimateVZ,
            "posCtltargetX": posCtltargetX,
            "posCtltargetY": posCtltargetY,
            "posCtltargetZ": posCtltargetZ,
            "posCtltargetVX": posCtltargetVX,
            "posCtltargetVY": posCtltargetVY,
            "posCtltargetVZ": posCtltargetVZ,
            "kalmanStateX": kalmanStateX,
            "kalmanStateY": kalmanStateY,
            "kalmanStateZ": kalmanStateZ,
            "kalmanVarX": kalmanVarX,
            "kalmanVarY": kalmanVarY,
            "kalmanVarZ": kalmanVarZ,
        }
    )

    return data_df


def calculateAbsVelocity(data_df):
    data_df["velocity"] = np.sqrt(
        data_df["stateEstimateVX"] ** 2
        + data_df["stateEstimateVY"] ** 2
        + data_df["stateEstimateVZ"] ** 2
    )


def calculateAbsVelocityTarget(data_df):
    data_df["velocity_target"] = np.sqrt(
        data_df["posCtltargetVX"] ** 2
        + data_df["posCtltargetVY"] ** 2
        + data_df["posCtltargetVZ"] ** 2
    )


def calculateError(data_df):
    data_df["errorX"] = data_df["posCtltargetX"] - data_df["stateEstimateX"]
    data_df["errorY"] = data_df["posCtltargetY"] - data_df["stateEstimateY"]
    data_df["errorZ"] = data_df["posCtltargetZ"] - data_df["stateEstimateZ"]
    data_df["error"] = np.sqrt(
        data_df["errorX"] ** 2 + data_df["errorY"] ** 2 + data_df["errorZ"] ** 2
    )


def calculateMultivariateGaussianFromData(x, y):
    # rv = multivariate_normal.fit([x, y])
    data = np.column_stack((x, y))
    mean = np.mean(data, axis=0)
    cov = np.cov(data, rowvar=False)
    return mean, cov


def plotVelocityOverTime(data_timescale1, data_timescale2, data_timescale3):
    # Plotting the velocity over time
    fig_velocity, ax_velocity = plt.subplots(3, 1, figsize=(18, 10))
    ax_velocity[0].set_xlabel("Timestamp")
    ax_velocity[1].set_xlabel("Timestamp")
    ax_velocity[2].set_xlabel("Timestamp")
    ax_velocity[0].set_ylabel("Velocity")
    ax_velocity[1].set_ylabel("Velocity")
    ax_velocity[2].set_ylabel("Velocity")
    # plt.title('Velocity of the Drone over Time')
    plt.legend()

    ax_velocity[0].plot(data_timescale1["timestamp"], data_timescale1["velocity"], color="red")
    ax_velocity[1].plot(data_timescale2["timestamp"], data_timescale2["velocity"], color="blue")
    ax_velocity[2].plot(data_timescale3["timestamp"], data_timescale3["velocity"], color="green")

    plt.show()


def load_bagfiles(base_dirs):
    bagfiles = []
    for k, base in enumerate(base_dirs, start=1):
        # search for all files that match the pattern
        pattern = os.path.join(str(base), "**", "*.db3")
        matching_files = glob.glob(pattern, recursive=True)
        print(f"Found: {matching_files}")

        # initialize empty lists
        velocity_values = []
        error_values = []

        velocity_values = []
        position_x_values = []
        position_y_values = []
        position_x_target_values = []
        position_y_target_values = []

        dfs = []
        # ##print the list of matching files
        for j, file in enumerate(matching_files, start=1):
            bag_file = file

            data_df = createDataFrameFromBag(bag_file)
            calculateAbsVelocity(data_df)
            calculateError(data_df)

            velocity_array = data_df["velocity"].to_numpy()
            error_array = data_df["error"].to_numpy()

            position_x_array = data_df["stateEstimateX"].to_numpy()
            position_y_array = data_df["stateEstimateY"].to_numpy()

            position_x_target_array = data_df["posCtltargetX"].to_numpy()
            position_y_target_array = data_df["posCtltargetY"].to_numpy()

            velocity_values.extend(velocity_array.flatten())
            error_values.extend(error_array.flatten())

            position_x_values.extend(position_x_array.flatten())
            position_y_values.extend(position_y_array.flatten())

            position_x_target_values.extend(position_x_target_array.flatten())
            position_y_target_values.extend(position_y_target_array.flatten())

            dfs.append(data_df)

        bagfiles.append(dfs)

    return bagfiles


if __name__ == "__main__":
    parser = ArgumentParser(description="Convert rosbag files to CSV and amend error metrics.")
    parser.add_argument("input", type=str)
    args = parser.parse_args()

    path = Path(args.input)
    assert path.exists()

    dfs = load_bagfiles([path])[0]
    for i, df in enumerate(dfs):
        df.to_csv(path / f"{i}.csv")
