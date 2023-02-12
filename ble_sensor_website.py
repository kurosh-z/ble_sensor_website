# /* cSpell:disable */

import time  # to simulate a real time data, time loop
from datetime import datetime
import requests as rq
import urllib.parse
import pytz
import numpy as np  # np mean, np random
import pandas as pd  # read csv, df manipulation
import plotly.express as px  # interactive charts
import streamlit as st  # 🎈 data web app development


BASE_URL = "http://212.227.175.162:1880/drone-data?"
TIME_ZONE = pytz.timezone("Europe/Berlin")


def create_url(params):
    return BASE_URL + urllib.parse.urlencode(params)


def parse_response(response):
    if response.status_code == 200:
        try:
            resp_dict = response.json()
            # TODO: change print to some console error or ...
            if "Error" in resp_dict:
                return {"ERROR": resp_dict["Error"]}
            else:
                return resp_dict["data"]

        except Exception as e:
            return {"ERROR": str(e)}
    else:
        return {"ERROR": response.status_code}


st.set_page_config(
    page_title="Real-Time Drone Data Dashboard",
    page_icon=":-)",
    layout="wide",
)


# read csv from a URL


def get_data_from_server(gasname, addr_str, last_rows, dd, mm, yyyy):
    params = {"gas": gasname, "dd": dd, "mm": mm, "yyyy": yyyy, "last_rows": last_rows, "addr": addr_str}
    url = create_url(params)
    response = rq.request(method="GET", url=url, timeout=5, headers={}, data={})
    data = parse_response(response)

    if "ERROR" in data:
        return data

    data_dict = {
        "address": [],
        "timestamp": [],
        "datetime": [],
        "gas": [],
        "unit": [],
        "float_value": [],
        "warmup1": [],
        "warmup2": [],
    }
    for d in data:
        data_dict["address"].append(int(d["address"]))
        data_dict["gas"].append(d["gas"])
        data_dict["timestamp"].append(d["timestamp"])
        data_dict["datetime"].append(datetime.fromtimestamp(float(d["timestamp"]), TIME_ZONE).isoformat())
        data_dict["unit"].append(d["unit"])
        data_dict["float_value"].append(d["float_value"])
        data_dict["warmup1"].append(d["warmup1"])
        data_dict["warmup2"].append(d["warmup2"])
    return pd.DataFrame.from_dict(data_dict)


# @st.experimental_memo
def get_data_all(gas, addr_str, mm, dd, yyyy, last_rows) -> pd.DataFrame:
    return get_data_from_server(
        gasname=gas,
        addr_str=addr_str,
        last_rows=last_rows,
        dd=dd,
        mm=mm,
        yyyy=yyyy,
    )


def number_to_str(number):
    return "{:02d}".format(number)


def parse_datetime(date):
    dd = number_to_str(date.day)
    mm = number_to_str(date.month)
    yy = str(date.year)

    return [dd, mm, yy]


def main(desired_date, num_of_sensors, last_rows, addr_list, name_list):

    dd, mm, yyyy = parse_datetime(desired_date)
    addr_list_str = [number_to_str(addr_list[0]), number_to_str(addr_list[1])]
    df1 = get_data_all(
        gas=name_list[0],
        addr_str=addr_list_str[0],
        last_rows=last_rows,
        mm=mm,
        dd=dd,
        yyyy=yyyy,
    )
    if "ERROR" in df1:
        error_text = f"""<p style= color:Red; font-size: 20px;">ERROR in sensor1: {df1["ERROR"]}  </p>"""
        st.write(error_text, unsafe_allow_html=True)

    if num_of_sensors == 2:
        df2 = get_data_all(
            gas=name_list[1],
            addr_str=addr_list_str[1],
            last_rows=last_rows,
            mm=mm,
            dd=dd,
            yyyy=yyyy,
        )
        if "ERROR" in df2:
            error_text = f"""<p style= color:Red; font-size: 20px;"> ERROR in sensor2: {df2["ERROR"]}  </p>"""
            st.write(error_text, unsafe_allow_html=True)

    # dashboard title
    st.title("Real-Time BLE Seonsr Dashboard")

    # top-level filters
    # job_filter = st.selectbox("Select the Job", pd.unique(df["job"]))

    # creating a single-element container
    placeholder = st.empty()

    # dataframe filter
    # df = df[df["job"] == job_filter]

    # near real-time / live feed simulation
    while True:

        if not ("ERROR" in df1):
            df1_new = get_data_from_server(name_list[0], addr_list_str[0], 1, dd, mm, yyyy)
            df1 = pd.concat([df1, df1_new]).drop_duplicates().reset_index(drop=True)
            df1.sort_values(by=["timestamp"])

        if num_of_sensors == 2 and not ("ERROR" in df2):
            df2_new = get_data_from_server(name_list[1], addr_list_str[1], 1, dd, mm, yyyy)
            df2 = pd.concat([df2, df2_new]).drop_duplicates().reset_index(drop=True)
            df2.sort_values(by=["timestamp"])

        with placeholder.container():

            st.markdown("----")
            st.markdown("### Plots:")

            fig_col1, fig_col2, fig_col3 = st.columns([1, 3, 1])
            if not ("ERROR" in df1):
                with fig_col2:
                    fig1 = px.line(
                        data_frame=df1,
                        y="float_value",
                        x="datetime",
                        markers=True,
                        labels={
                            "float_value": f"""<b>{df1['gas'].values[-1:][0]} [ {df1['unit'].values[-1:][0]}]</b>""",
                            "datetime": "Date and Time",
                        },
                        template="plotly_dark",
                        color_discrete_sequence=["blue"],
                    )
                    fig1.update_layout(title={"text": f"Time series {df1['gas'].values[-1:][0]}"})

                    st.plotly_chart(fig1, use_container_width=True)

            if num_of_sensors == 2 and not ("ERROR" in df2):
                with fig_col2:
                    fig2 = px.line(
                        data_frame=df2,
                        y="float_value",
                        x="datetime",
                        labels={
                            "float_value": f"""{df2['gas'].values[-1:][0]} [{df2['unit'].values[-1:][0]}]""",
                            "datetime": "Date and Time",
                        },
                        markers=True,
                        template="ggplot2",
                        color_discrete_sequence=["#cc422f"],
                    )
                    fig2.update_layout(title={"text": f"Time series {df2['gas'].values[-1:][0]}"})
                    st.plotly_chart(fig2, use_container_width=True)

            st.markdown("----")
            st.markdown("### Detailed Data")
            dt_col1, dt_col2, dt_col3 = st.columns([1, 4, 1])
            
            with dt_col2:
                if not ("ERROR" in df1):
                    st.markdown(f"""#### Table View of {name_list[0]}""")
                    st.dataframe(df1)
                if num_of_sensors == 2 and not ("ERROR" in df2):
                    st.markdown(f"""#### Table View of {name_list[1]}""")
                    st.dataframe(df2)

            time.sleep(1)


st.markdown("#### Please configure the dasboard:")

submitted = False
with st.form(key="plot_form"):

    cc1 = st.columns([1, 2, 2, 8])
    with cc1[1]:
        desired_date = st.date_input("Choose the date", datetime.today())
    with cc1[2]:
        number_of_rows = st.number_input("Number of past measurements:", value=1, min_value=1, step=1)

    ## here I want to add the option to change the name of the sensor
    cc2 = st.columns([1, 2, 2, 8])
    with cc2[1]:
        num_of_sensors = st.selectbox("How many active sensors do you have?", (1, 2))

    cc3 = st.columns([1, 2, 2, 8])
    with cc3[1]:
        sensor1_addr = st.number_input("Sensor1 address:", value=1, min_value=1, step=1, format="%d")

    with cc3[2]:
        sensor2_addr = st.number_input("Sensor2 address:", value=2, min_value=1, step=1, format="%d")

    cols = st.columns([1, 2, 2, 8])
    with cols[1]:
        senosr1_name = st.radio(
            "Set sensor1 name ",
            ["CO2", "O2"],
            key="senor1_name",
        )
    with cols[2]:
        senosr2_name = st.radio(
            "Set sensor2 name ",
            ["CO2", "O2"],
            key="senor2_name",
        )

    cc = st.columns([1, 2, 2, 8])
    with cc[1]:
        submitted = st.form_submit_button("Submit")


if submitted:
    addr_list = [sensor1_addr, sensor2_addr]
    name_list = [senosr1_name, senosr2_name]
    main(desired_date, num_of_sensors, number_of_rows, addr_list, name_list)
