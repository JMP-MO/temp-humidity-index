from ecmwf.opendata import Client


def main():
    # Params
    parameters = ['2d', '2t', 'msl']
    filename = "ifs_2t_dp_msl.grib"
    step = 48

    # Instantiate the client
    client = Client(source="ecmwf")

    # Retrieve the data
    client.retrieve(
        stream="oper",
        type="fc",
        levtype="sfc",
        step=step,
        param=parameters,
        target=filename,
    )


if __name__ == "__main__":
    main()

