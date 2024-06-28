import h5py
import os
import pyspecdata as psd
import subprocess
import pyspecProcSripts


def save_data(dataset, my_exp_type, config_dict, counter_type):
    """save data to an h5 file with appropriately labeled nodename and performs
    rough processing

    Parameters
    ==========
    dataset: nddata
        acquired data in nddata format
    my_exp_type: str
        directory on the share drive you want to save to
    config_dict: dict
        config_dict pulled from the active.ini file
    counter_type: str
        type of counter you are incrementing

    Returns
    =======
    config_dict: dict
        the updated config dict after appropriately incrementing the counter
    """
    target_directory = psd.getDATADIR(exp_type=my_exp_type)
    # {{{ create filename
    filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
    # }}}
    nodename = (
        config_dict["type"]
        + "_"
        + str(config_dict["%s_counter" % counter_type])
    )
    dataset.name(nodename)
    filename_out = filename + ".h5"
    if os.path.exists(f"{filename_out}"):
        print("this file already exists so we will add a node to it!")
        with h5py.File(
            os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
        ) as fp:
            while nodename in fp.keys():
                config_dict["%s_counter" % counter_type] += 1
                nodename = (
                    config_dict["type"]
                    + "_"
                    + str(config_dict["%s_counter" % counter_type])
                )
            dataset.name(nodename)
    dataset.hdf5_write(f"{filename_out}", directory=target_directory)
    print("\n** FILE SAVED IN TARGET DIRECTORY ***\n")
    print(
        "saved data to (node, file, exp_type):",
        dataset.name(),
        filename_out,
        my_exp_type,
    )
    subprocess.call(
        " ".join(
            [
                "python ",
                os.path.join(
                    os.path.split(os.path.split(pyspecProcSripts.__file__)[0])[
                        0
                    ],
                    "examples",
                    "proc_raw.py",
                ),
                "%s %s %s" % (dataset.name(), filename_out, my_exp_type),
            ],
            shell=True,
        )
    )
    return config_dict
