import numpy as np
import yaml
import toml
from datetime import datetime
import matplotlib
import matplotlib.pyplot as plt

# bolo-calc import
from bolo import Top

""" Functions to drive bolo-calc, varying inputs and saving/plotting inputs and outputs """

def vary_param_at_fixed_psat(xparam_name,xparam_vec,yparam_name,dd,psat):
    """ Run bolocalc and plot and save x vs y, for one telescope.

    version_date, channel_dict = vary_param_at_fixed_psat(x,y,yname,dd,psat)

    xparam_name:  name of input parameter to vary.
    xparam_vec:  values of input parameter to use.
    yparam_name: name of output parameter to plot on the y-axis.
    dd : the dictionary that bolo-calc uses as an input;  must include version field,
        which will be stripped out before passing to bolo-calc.
    psat:  dictionary of P_sat values to use, keyed by channel name.

    Returns:
      version_date:  a string containing the date code for the model version.
      channel_dict:  a dictionary containing the inputs and outputs necessary for packing later into a toml file.

    The function also make a plots and saves it as a png.
        (We should consider moving that functionality to post-processing)
    """
    version_date = str(dd['version']['date'])
    version_telescope = str(dd['version']['name'])
    yaml_file = dd['version']['yaml']
    del dd['version']

    ch_names = list(dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'].keys())

    #convert to Watts
    for channel in ch_names:
        psat[yaml_file.partition('.')[0]][channel] *= 1e-12

    #set psat factor to None & delete psat entry from channel default
    dd['instrument']['channel_default']['psat_factor'] = None
    del dd['instrument']['channel_default']['psat']

    #assign SI psat values at the channel level
    for channel in ch_names:
        dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'][channel]['psat'] = psat[yaml_file.partition('.')[0]][channel]

    # Find the default (base) value for the varying parameter.
    base_value = dict.fromkeys(ch_names)
    for channel in ch_names:
        base_value[channel] = dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'][channel][xparam_name]

    # Create dictionary to store output vectors in.
    outputs = {}
    outputs[yparam_name]={}
    for chan in ch_names:
        outputs[yparam_name][chan]=np.array([])

    # Call bolo-calc for each value of the x
    for param_value in xparam_vec:
        for chan in ch_names:
            dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'][chan][xparam_name] = param_value
        top = Top(**dd)
        top.run()
        tabs = top.instrument.tables
        for chan in ch_names:
            outputs[yparam_name][chan] = np.append(outputs[yparam_name][chan], tabs['cam_1_%s_sims' % chan][yparam_name].quantity[0])


    #save inputs & outputs to tesescope dictionary
    io_dict = dict.fromkeys([xparam_name, yparam_name])
    channel_dict = dict.fromkeys(ch_names)

    for chan in ch_names:
        channel_dict[chan] = io_dict
        channel_dict[chan][xparam_name] = xparam_vec
        channel_dict[chan][yparam_name] = np.array(outputs[yparam_name][chan])
        channel_dict[chan]['xdefault']=base_value[chan]

    #plot
    plt.clf()
    n_chan = len(ch_names)
    ii = n_chan

    for chan in ch_names:
        plt.subplot(n_chan,1,ii)
        plt.plot(xparam_vec,outputs[yparam_name][chan])
        plt.axvline(x = base_value[chan], color="red")
        plt.ylabel(yparam_name)
        if ii == n_chan:
            plt.xlabel(xparam_name)
        xmin, xmax, ymin, ymax = plt.axis()
        #plt.plot([base_value,base_value],[ymin,ymax],'r')
        xloc = xmin + 0.8*(xmax-xmin)
        yloc = ymin + 0.6*(ymax-ymin)
        plt.text(xloc,yloc,chan,color='r')
        plt.grid()
        ii = ii-1
    titlestring = 'Telescope: '+version_telescope+',   Version:'+version_date
    plt.title(titlestring)

    plt.savefig('plots/' + yaml_file.partition('.')[0] + '_' + yparam_name + '_v_' + xparam_name + '.png', dpi=300)

    return version_date,channel_dict

##############################3



