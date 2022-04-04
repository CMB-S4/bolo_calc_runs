import numpy as np
import yaml
import toml
from datetime import datetime
import matplotlib
import matplotlib.pyplot as plt
import pdb

# bolo-calc import
from bolo import Top

""" Functions to drive bolo-calc, varying inputs and saving/plotting inputs and outputs """

def vary_param_at_fixed_psat(xparam_name,xparam_vec,yparam_name,dd,psat,optical_element=None):
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

    #different procedure if xparam is at instrument or channel level
    instrument_params = ['site', 'sky_temp', 'elevation', 'pwv', 'obs_time', 'sky_fraction', 'obs_effic', 'NET']
    channel_params = ['band_response','num_wafer_per_optics_tube','num_optics_tube','det_eff','waist_factor','psat','psat_factor','carrier_index','Tc','Tc_fraction','G','Flink','Yield','response_factor','bolo_resistance','read_frac']

    if xparam_name in channel_params:

        # Find the default (base) value for the varying parameter.
        base_value = dict.fromkeys(ch_names)
        try:
            for channel in ch_names:
                base_value[channel] = dd['instrument']['channel_default'][xparam_name]
        except:
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

    elif xparam_name in instrument_params:

        # Find the default (base) value for the varying parameter.
        base_value = dict.fromkeys(ch_names)
        for channel in ch_names:
            base_value[channel] = dd['instrument'][xparam_name]

        # Create dictionary to store output vectors in.
        outputs = {}
        outputs[yparam_name]={}
        for chan in ch_names:
            outputs[yparam_name][chan]=np.array([])

        # Call bolo-calc for each value of the x
        for param_value in xparam_vec:
            for chan in ch_names:
                dd['instrument'][xparam_name] = param_value
            top = Top(**dd)
            top.run()
            tabs = top.instrument.tables
            for chan in ch_names:
                outputs[yparam_name][chan] = np.append(outputs[yparam_name][chan], tabs['cam_1_%s_sims' % chan][yparam_name].quantity[0])

    elif optical_element != None:

        # Find the default (base) value for the varying parameter.
        base_value = dict.fromkeys(ch_names)
        for channel in ch_names:
            base_value[channel] = dd['instrument']['optics_config']['elements'][optical_element][xparam_name]

        # Create dictionary to store output vectors in.
        outputs = {}
        outputs[yparam_name]={}
        for chan in ch_names:
            outputs[yparam_name][chan]=np.array([])

        # Call bolo-calc for each value of the x
        for param_value in xparam_vec:
            for chan in ch_names:
                dd['instrument']['optics_config']['elements'][optical_element][xparam_name] = param_value
            top = Top(**dd)
            top.run()
            tabs = top.instrument.tables
            for chan in ch_names:
                outputs[yparam_name][chan] = np.append(outputs[yparam_name][chan], tabs['cam_1_%s_sims' % chan][yparam_name].quantity[0])

        # Find the default (base) value for the output parameter.

    #save inputs & outputs to tesescope dictionary
    io_dict = dict.fromkeys([xparam_name, yparam_name])
    channel_dict = dict.fromkeys(ch_names)

    for chan in ch_names:
        channel_dict[chan] = io_dict.copy()
        channel_dict[chan][xparam_name] = xparam_vec
        channel_dict[chan][yparam_name] = np.array(outputs[yparam_name][chan])
        channel_dict[chan]['xdefault']=base_value[chan]




    #plot
    plt.clf()
    n_chan = len(ch_names)
    ii = 2*n_chan

    for chan in ch_names:
        #print(chan+' '+str(ii))
        plt.subplot(2*n_chan,2,ii)
        plt.plot(xparam_vec,outputs[yparam_name][chan])
        plt.axvline(x = base_value[chan], color="red")
        plt.ylabel(yparam_name)
        if (ii >=2*n_chan-1):
            plt.xlabel(xparam_name)
        xmin, xmax, ymin, ymax = plt.axis()
        #plt.plot([base_value,base_value],[ymin,ymax],'r')
        xloc = xmin + 0.8*(xmax-xmin)
        yloc = ymin + 0.6*(ymax-ymin)
        plt.text(xloc,yloc,chan,color='r')
        plt.grid()
        ii = ii-1

        #print(chan+' '+str(ii))
        plt.subplot(2*n_chan,2,ii)
        plt.plot(xparam_vec,outputs[yparam_name][chan]/np.min(outputs[yparam_name][chan]))
        plt.axvline(x = base_value[chan], color="red")
        ylabelstring = yparam_name+'/NET_min'
        plt.ylabel(ylabelstring)
        if (ii >=2*n_chan-1):
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

def net_v_elevation(xparam_vec, yaml_list, psat):
    xparam_name = 'elevation'
    yparam_name = 'NET'
    telescopes = dict.fromkeys(yaml_list)
    for telescope in telescopes:

        yaml_file = telescope
        dd = yaml.safe_load(open(yaml_file))
        version_date = str(dd['version']['date'])
        version_telescope = str(dd['version']['name'])
        dd['sim_config']['config_dir'] = '../../bolo-calc/config'
        dd['version']['yaml']=yaml_file
        del dd['version']
        ch_names = list(dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'].keys())

        #convert to Watts
        for channel in ch_names:
            psat[yaml_file.partition('.')[0]][channel] *= 1e-12

        #set psat factor to None & delete psat entry from channel default
        dd['instrument']['channel_default']['psat_factor'] = None
        del dd['instrument']['channel_default']['psat']

        # Find the default (base) value for the varying parameter.
        base_value = dict.fromkeys(ch_names)
        for channel in ch_names:
            base_value[channel] = dd['instrument'][xparam_name]



        #assign SI psat values at the channel level
        for channel in ch_names:
            dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'][channel]['psat'] = psat[yaml_file.partition('.')[0]][channel]

            # Create dictionary to store output vectors in.
            outputs = {}
            outputs[yparam_name]={}
            for chan in ch_names:
                outputs[yparam_name][chan]=np.array([])

            # Call bolo-calc for each value of the x
            for param_value in xparam_vec:
                for chan in ch_names:
                    dd['instrument'][xparam_name] = param_value
                top = Top(**dd)
                top.run()
                tabs = top.instrument.tables
                for chan in ch_names:
                    outputs[yparam_name][chan] = np.append(outputs[yparam_name][chan], tabs['cam_1_%s_sims' % chan][yparam_name].quantity[0])

        #plot
        plt.ioff()
        plt.rcParams.update({'font.size': 18})
        plt.rcParams['figure.figsize'] = [20, 40]
        plt.clf()
        n_chan = len(ch_names)
        ii = 2*n_chan

        for chan in ch_names:
            #print(chan+' '+str(ii))
            plt.subplot(2*n_chan,2,ii)
            plt.plot(xparam_vec,outputs[yparam_name][chan])
            plt.axvline(x = base_value[chan], color="red")
            plt.ylabel(yparam_name)
            if (ii >=2*n_chan-1):
                plt.xlabel(xparam_name)
            xmin, xmax, ymin, ymax = plt.axis()
            #plt.plot([base_value,base_value],[ymin,ymax],'r')
            xloc = xmin + 0.8*(xmax-xmin)
            yloc = ymin + 0.6*(ymax-ymin)
            plt.text(xloc,yloc,chan,color='r')
            plt.grid()
            ii = ii-1

            #print(chan+' '+str(ii))
            plt.subplot(2*n_chan,2,ii)
            plt.plot(xparam_vec,outputs[yparam_name][chan]/np.min(outputs[yparam_name][chan]))
            plt.axvline(x = base_value[chan], color="red")
            ylabelstring = yparam_name+'/NET_min'
            plt.ylabel(ylabelstring)
            if (ii >=2*n_chan-1):
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


        #save inputs & outputs to tesescope dictionary
        io_dict = dict.fromkeys([xparam_name, yparam_name])
        channel_dict = dict.fromkeys(ch_names)

        for chan in ch_names:
            channel_dict[chan] = io_dict.copy()
            channel_dict[chan][xparam_name] = xparam_vec
            channel_dict[chan][yparam_name] = np.array(outputs[yparam_name][chan])
            channel_dict[chan]['xdefault']=base_value[chan]
        telescopes[yaml_file] = channel_dict

    telescopes["runtime"] = datetime.today().strftime('%Y/%m/%d %H:%M:%S')
    #telescopes["input_id"] = version_date
    telescopes["variation"] = yparam_name + '_v_' + xparam_name

    output_file_name = telescopes['variation'] + '.toml'

    with open('outputs/' + output_file_name, "w") as toml_file:
        toml.dump(telescopes, toml_file, encoder=toml.TomlNumpyEncoder())

def popt_v_elevation(xparam_vec, yaml_list, psat):
    xparam_name = 'elevation'
    yparam_name = 'opt_power'
    telescopes = dict.fromkeys(yaml_list)
    for telescope in telescopes:

        yaml_file = telescope
        dd = yaml.safe_load(open(yaml_file))
        version_date = str(dd['version']['date'])
        version_telescope = str(dd['version']['name'])
        dd['sim_config']['config_dir'] = '../../bolo-calc/config'
        dd['version']['yaml']=yaml_file
        del dd['version']
        ch_names = list(dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'].keys())

        #convert to Watts
        for channel in ch_names:
            psat[yaml_file.partition('.')[0]][channel] *= 1e-12

        #set psat factor to None & delete psat entry from channel default
        dd['instrument']['channel_default']['psat_factor'] = None
        del dd['instrument']['channel_default']['psat']

        # Find the default (base) value for the varying parameter.
        base_value = dict.fromkeys(ch_names)
        for channel in ch_names:
            base_value[channel] = dd['instrument'][xparam_name]


        #assign SI psat values at the channel level
        for channel in ch_names:
            dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'][channel]['psat'] = psat[yaml_file.partition('.')[0]][channel]

            # Create dictionary to store output vectors in.
            outputs = {}
            outputs[yparam_name]={}
            for chan in ch_names:
                outputs[yparam_name][chan]=np.array([])

            # Call bolo-calc for each value of the x
            for param_value in xparam_vec:
                for chan in ch_names:
                    dd['instrument'][xparam_name] = param_value
                top = Top(**dd)
                top.run()
                tabs = top.instrument.tables
                for chan in ch_names:
                    outputs[yparam_name][chan] = np.append(outputs[yparam_name][chan], tabs['cam_1_%s_sims' % chan][yparam_name].quantity[0])

        #plot
        plt.ioff()
        plt.rcParams.update({'font.size': 18})
        plt.rcParams['figure.figsize'] = [20, 40]
        plt.clf()
        n_chan = len(ch_names)
        ii = 2*n_chan

        for chan in ch_names:
            #print(chan+' '+str(ii))
            plt.subplot(2*n_chan,2,ii)
            plt.plot(xparam_vec,outputs[yparam_name][chan])
            plt.axvline(x = base_value[chan], color="red")
            plt.ylabel(yparam_name)
            if (ii >=2*n_chan-1):
                plt.xlabel(xparam_name)
            xmin, xmax, ymin, ymax = plt.axis()
            #plt.plot([base_value,base_value],[ymin,ymax],'r')
            xloc = xmin + 0.8*(xmax-xmin)
            yloc = ymin + 0.6*(ymax-ymin)
            plt.text(xloc,yloc,chan,color='r')
            plt.grid()
            ii = ii-1

            #print(chan+' '+str(ii))
            plt.subplot(2*n_chan,2,ii)
            plt.plot(xparam_vec,outputs[yparam_name][chan]/np.min(outputs[yparam_name][chan]))
            plt.axvline(x = base_value[chan], color="red")
            ylabelstring = yparam_name+'/NET_min'
            plt.ylabel(ylabelstring)
            if (ii >=2*n_chan-1):
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


        #save inputs & outputs to tesescope dictionary
        io_dict = dict.fromkeys([xparam_name, yparam_name])
        channel_dict = dict.fromkeys(ch_names)

        for chan in ch_names:
            channel_dict[chan] = io_dict.copy()
            channel_dict[chan][xparam_name] = xparam_vec
            channel_dict[chan][yparam_name] = np.array(outputs[yparam_name][chan])
            channel_dict[chan]['xdefault']=base_value[chan]
        telescopes[yaml_file] = channel_dict

    telescopes["runtime"] = datetime.today().strftime('%Y/%m/%d %H:%M:%S')
    #telescopes["input_id"] = version_date
    telescopes["variation"] = yparam_name + '_v_' + xparam_name

    output_file_name = telescopes['variation'] + '.toml'

    with open('outputs/' + output_file_name, "w") as toml_file:
        toml.dump(telescopes, toml_file, encoder=toml.TomlNumpyEncoder())

def net_v_pwv(xparam_vec, yaml_list, psat):
    xparam_name = 'pwv'
    yparam_name = 'NET'
    telescopes = dict.fromkeys(yaml_list)
    for telescope in telescopes:

        yaml_file = telescope
        dd = yaml.safe_load(open(yaml_file))
        version_date = str(dd['version']['date'])
        version_telescope = str(dd['version']['name'])
        dd['sim_config']['config_dir'] = '../../bolo-calc/config'
        dd['version']['yaml']=yaml_file
        del dd['version']
        ch_names = list(dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'].keys())

        #convert to Watts
        for channel in ch_names:
            psat[yaml_file.partition('.')[0]][channel] *= 1e-12

        #set psat factor to None & delete psat entry from channel default
        dd['instrument']['channel_default']['psat_factor'] = None
        del dd['instrument']['channel_default']['psat']

        # Find the default (base) value for the varying parameter.
        base_value = dict.fromkeys(ch_names)
        for channel in ch_names:
            base_value[channel] = dd['instrument'][xparam_name]

        #assign SI psat values at the channel level
        for channel in ch_names:
            dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'][channel]['psat'] = psat[yaml_file.partition('.')[0]][channel]

            # Create dictionary to store output vectors in.
            outputs = {}
            outputs[yparam_name]={}
            for chan in ch_names:
                outputs[yparam_name][chan]=np.array([])

            # Call bolo-calc for each value of the x
            for param_value in xparam_vec:
                for chan in ch_names:
                    dd['instrument'][xparam_name] = param_value
                top = Top(**dd)
                top.run()
                tabs = top.instrument.tables
                for chan in ch_names:
                    outputs[yparam_name][chan] = np.append(outputs[yparam_name][chan], tabs['cam_1_%s_sims' % chan][yparam_name].quantity[0])

        #plot
        plt.ioff()
        plt.rcParams.update({'font.size': 18})
        plt.rcParams['figure.figsize'] = [20, 40]
        plt.clf()
        n_chan = len(ch_names)
        ii = 2*n_chan

        for chan in ch_names:
            #print(chan+' '+str(ii))
            plt.subplot(2*n_chan,2,ii)
            plt.plot(xparam_vec,outputs[yparam_name][chan])
            plt.axvline(x = base_value[chan], color="red")
            plt.ylabel(yparam_name)
            if (ii >=2*n_chan-1):
                plt.xlabel(xparam_name)
            xmin, xmax, ymin, ymax = plt.axis()
            #plt.plot([base_value,base_value],[ymin,ymax],'r')
            xloc = xmin + 0.8*(xmax-xmin)
            yloc = ymin + 0.6*(ymax-ymin)
            plt.text(xloc,yloc,chan,color='r')
            plt.grid()
            ii = ii-1

            #print(chan+' '+str(ii))
            plt.subplot(2*n_chan,2,ii)
            plt.plot(xparam_vec,outputs[yparam_name][chan]/np.min(outputs[yparam_name][chan]))
            plt.axvline(x = base_value[chan], color="red")
            ylabelstring = yparam_name+'/NET_min'
            plt.ylabel(ylabelstring)
            if (ii >=2*n_chan-1):
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


        #save inputs & outputs to tesescope dictionary
        io_dict = dict.fromkeys([xparam_name, yparam_name])
        channel_dict = dict.fromkeys(ch_names)

        for chan in ch_names:
            channel_dict[chan] = io_dict.copy()
            channel_dict[chan][xparam_name] = xparam_vec
            channel_dict[chan][yparam_name] = np.array(outputs[yparam_name][chan])
            channel_dict[chan]['xdefault']=base_value[chan]
        telescopes[yaml_file] = channel_dict

    telescopes["runtime"] = datetime.today().strftime('%Y/%m/%d %H:%M:%S')
    #telescopes["input_id"] = version_date
    telescopes["variation"] = yparam_name + '_v_' + xparam_name

    output_file_name = telescopes['variation'] + '.toml'

    with open('outputs/' + output_file_name, "w") as toml_file:
        toml.dump(telescopes, toml_file, encoder=toml.TomlNumpyEncoder())

def popt_v_pwv(xparam_vec, yaml_list, psat):
    xparam_name = 'pwv'
    yparam_name = 'opt_power'
    telescopes = dict.fromkeys(yaml_list)
    for telescope in telescopes:

        yaml_file = telescope
        dd = yaml.safe_load(open(yaml_file))
        version_date = str(dd['version']['date'])
        version_telescope = str(dd['version']['name'])
        dd['sim_config']['config_dir'] = '../../bolo-calc/config'
        dd['version']['yaml']=yaml_file
        del dd['version']
        ch_names = list(dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'].keys())

        #convert to Watts
        for channel in ch_names:
            psat[yaml_file.partition('.')[0]][channel] *= 1e-12

        #set psat factor to None & delete psat entry from channel default
        dd['instrument']['channel_default']['psat_factor'] = None
        del dd['instrument']['channel_default']['psat']

        # Find the default (base) value for the varying parameter.
        base_value = dict.fromkeys(ch_names)
        for channel in ch_names:
            base_value[channel] = dd['instrument'][xparam_name]


        #assign SI psat values at the channel level
        for channel in ch_names:
            dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'][channel]['psat'] = psat[yaml_file.partition('.')[0]][channel]

            # Create dictionary to store output vectors in.
            outputs = {}
            outputs[yparam_name]={}
            for chan in ch_names:
                outputs[yparam_name][chan]=np.array([])

            # Call bolo-calc for each value of the x
            for param_value in xparam_vec:
                for chan in ch_names:
                    dd['instrument'][xparam_name] = param_value
                top = Top(**dd)
                top.run()
                tabs = top.instrument.tables
                for chan in ch_names:
                    outputs[yparam_name][chan] = np.append(outputs[yparam_name][chan], tabs['cam_1_%s_sims' % chan][yparam_name].quantity[0])

        #plot
        plt.ioff()
        plt.rcParams.update({'font.size': 18})
        plt.rcParams['figure.figsize'] = [20, 40]
        plt.clf()
        n_chan = len(ch_names)
        ii = 2*n_chan

        for chan in ch_names:
            #print(chan+' '+str(ii))
            plt.subplot(2*n_chan,2,ii)
            plt.plot(xparam_vec,outputs[yparam_name][chan])
            plt.axvline(x = base_value[chan], color="red")
            plt.ylabel(yparam_name)
            if (ii >=2*n_chan-1):
                plt.xlabel(xparam_name)
            xmin, xmax, ymin, ymax = plt.axis()
            #plt.plot([base_value,base_value],[ymin,ymax],'r')
            xloc = xmin + 0.8*(xmax-xmin)
            yloc = ymin + 0.6*(ymax-ymin)
            plt.text(xloc,yloc,chan,color='r')
            plt.grid()
            ii = ii-1

            #print(chan+' '+str(ii))
            plt.subplot(2*n_chan,2,ii)
            plt.plot(xparam_vec,outputs[yparam_name][chan]/np.min(outputs[yparam_name][chan]))
            plt.axvline(x = base_value[chan], color="red")
            ylabelstring = yparam_name+'/NET_min'
            plt.ylabel(ylabelstring)
            if (ii >=2*n_chan-1):
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


        #save inputs & outputs to tesescope dictionary
        io_dict = dict.fromkeys([xparam_name, yparam_name])
        channel_dict = dict.fromkeys(ch_names)

        for chan in ch_names:
            channel_dict[chan] = io_dict.copy()
            channel_dict[chan][xparam_name] = xparam_vec
            channel_dict[chan][yparam_name] = np.array(outputs[yparam_name][chan])
            channel_dict[chan]['xdefault']=base_value[chan]
        telescopes[yaml_file] = channel_dict

    telescopes["runtime"] = datetime.today().strftime('%Y/%m/%d %H:%M:%S')
    #telescopes["input_id"] = version_date
    telescopes["variation"] = yparam_name + '_v_' + xparam_name

    output_file_name = telescopes['variation'] + '.toml'

    with open('outputs/' + output_file_name, "w") as toml_file:
        toml.dump(telescopes, toml_file, encoder=toml.TomlNumpyEncoder())

def net_v_tc(xparam_vec, yaml_list, psat):
    xparam_name = 'Tc'
    yparam_name = 'NET'
    telescopes = dict.fromkeys(yaml_list)
    for telescope in telescopes:

        yaml_file = telescope
        dd = yaml.safe_load(open(yaml_file))
        version_date = str(dd['version']['date'])
        version_telescope = str(dd['version']['name'])
        dd['sim_config']['config_dir'] = '../../bolo-calc/config'
        dd['version']['yaml']=yaml_file
        del dd['version']
        ch_names = list(dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'].keys())

        #convert to Watts
        for channel in ch_names:
            psat[yaml_file.partition('.')[0]][channel] *= 1e-12

        #set psat factor to None & delete psat entry from channel default
        dd['instrument']['channel_default']['psat_factor'] = None
        del dd['instrument']['channel_default']['psat']

        # Find the default (base) value for the varying parameter.
        base_value = dict.fromkeys(ch_names)
        try:
            for channel in ch_names:
                base_value[channel] = dd['instrument']['channel_default'][xparam_name]
        except:
            for channel in ch_names:
                base_value[channel] = dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'][channel][xparam_name]

        #assign SI psat values at the channel level
        for channel in ch_names:
            dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'][channel]['psat'] = psat[yaml_file.partition('.')[0]][channel]


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

        #plot
        plt.ioff()
        plt.rcParams.update({'font.size': 18})
        plt.rcParams['figure.figsize'] = [20, 40]
        plt.clf()
        n_chan = len(ch_names)
        ii = 2*n_chan

        for chan in ch_names:
            #print(chan+' '+str(ii))
            plt.subplot(2*n_chan,2,ii)
            plt.plot(xparam_vec,outputs[yparam_name][chan])
            plt.axvline(x = base_value[chan], color="red")
            plt.ylabel(yparam_name)
            if (ii >=2*n_chan-1):
                plt.xlabel(xparam_name)
            xmin, xmax, ymin, ymax = plt.axis()
            #plt.plot([base_value,base_value],[ymin,ymax],'r')
            xloc = xmin + 0.8*(xmax-xmin)
            yloc = ymin + 0.6*(ymax-ymin)
            plt.text(xloc,yloc,chan,color='r')
            plt.grid()
            ii = ii-1

            #print(chan+' '+str(ii))
            plt.subplot(2*n_chan,2,ii)
            plt.plot(xparam_vec,outputs[yparam_name][chan]/np.min(outputs[yparam_name][chan]))
            plt.axvline(x = base_value[chan], color="red")
            ylabelstring = yparam_name+'/NET_min'
            plt.ylabel(ylabelstring)
            if (ii >=2*n_chan-1):
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


        #save inputs & outputs to tesescope dictionary
        io_dict = dict.fromkeys([xparam_name, yparam_name])
        channel_dict = dict.fromkeys(ch_names)

        for chan in ch_names:
            channel_dict[chan] = io_dict.copy()
            channel_dict[chan][xparam_name] = xparam_vec
            channel_dict[chan][yparam_name] = np.array(outputs[yparam_name][chan])
            channel_dict[chan]['xdefault']=base_value[chan]
        telescopes[yaml_file] = channel_dict

    telescopes["runtime"] = datetime.today().strftime('%Y/%m/%d %H:%M:%S')
    #telescopes["input_id"] = version_date
    telescopes["variation"] = yparam_name + '_v_' + xparam_name

    output_file_name = telescopes['variation'] + '.toml'

    with open('outputs/' + output_file_name, "w") as toml_file:
        toml.dump(telescopes, toml_file, encoder=toml.TomlNumpyEncoder())

def net_v_beta(xparam_vec, yaml_list, psat):
    xparam_name = 'carrier_index'
    yparam_name = 'NET'
    telescopes = dict.fromkeys(yaml_list)
    for telescope in telescopes:

        yaml_file = telescope
        dd = yaml.safe_load(open(yaml_file))
        version_date = str(dd['version']['date'])
        version_telescope = str(dd['version']['name'])
        dd['sim_config']['config_dir'] = '../../bolo-calc/config'
        dd['version']['yaml']=yaml_file
        del dd['version']
        ch_names = list(dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'].keys())

        #convert to Watts
        for channel in ch_names:
            psat[yaml_file.partition('.')[0]][channel] *= 1e-12

        #set psat factor to None & delete psat entry from channel default
        dd['instrument']['channel_default']['psat_factor'] = None
        del dd['instrument']['channel_default']['psat']

        # Find the default (base) value for the varying parameter.
        base_value = dict.fromkeys(ch_names)
        try:
            for channel in ch_names:
                base_value[channel] = dd['instrument']['channel_default'][xparam_name]
        except:
            for channel in ch_names:
                base_value[channel] = dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'][channel][xparam_name]

        #assign SI psat values at the channel level
        for channel in ch_names:
            dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'][channel]['psat'] = psat[yaml_file.partition('.')[0]][channel]


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

        #plot
        plt.ioff()
        plt.rcParams.update({'font.size': 18})
        plt.rcParams['figure.figsize'] = [20, 40]
        plt.clf()
        n_chan = len(ch_names)
        ii = 2*n_chan

        for chan in ch_names:
            #print(chan+' '+str(ii))
            plt.subplot(2*n_chan,2,ii)
            plt.plot(xparam_vec,outputs[yparam_name][chan])
            plt.axvline(x = base_value[chan], color="red")
            plt.ylabel(yparam_name)
            if (ii >=2*n_chan-1):
                plt.xlabel(xparam_name)
            xmin, xmax, ymin, ymax = plt.axis()
            #plt.plot([base_value,base_value],[ymin,ymax],'r')
            xloc = xmin + 0.8*(xmax-xmin)
            yloc = ymin + 0.6*(ymax-ymin)
            plt.text(xloc,yloc,chan,color='r')
            plt.grid()
            ii = ii-1

            #print(chan+' '+str(ii))
            plt.subplot(2*n_chan,2,ii)
            plt.plot(xparam_vec,outputs[yparam_name][chan]/np.min(outputs[yparam_name][chan]))
            plt.axvline(x = base_value[chan], color="red")
            ylabelstring = yparam_name+'/NET_min'
            plt.ylabel(ylabelstring)
            if (ii >=2*n_chan-1):
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


        #save inputs & outputs to tesescope dictionary
        io_dict = dict.fromkeys([xparam_name, yparam_name])
        channel_dict = dict.fromkeys(ch_names)

        for chan in ch_names:
            channel_dict[chan] = io_dict.copy()
            channel_dict[chan][xparam_name] = xparam_vec
            channel_dict[chan][yparam_name] = np.array(outputs[yparam_name][chan])
            channel_dict[chan]['xdefault']=base_value[chan]
        telescopes[yaml_file] = channel_dict

    telescopes["runtime"] = datetime.today().strftime('%Y/%m/%d %H:%M:%S')
    #telescopes["input_id"] = version_date
    telescopes["variation"] = yparam_name + '_v_' + xparam_name

    output_file_name = telescopes['variation'] + '.toml'

    with open('outputs/' + output_file_name, "w") as toml_file:
        toml.dump(telescopes, toml_file, encoder=toml.TomlNumpyEncoder())

def net_v_AfTemp(xparam_vec, yaml_list, psat):
    xparam_name = 'temperature'
    yparam_name = 'NET'
    optical_element = 'alumina_filt'
    telescopes = dict.fromkeys(yaml_list)
    for telescope in telescopes:

        yaml_file = telescope
        dd = yaml.safe_load(open(yaml_file))
        version_date = str(dd['version']['date'])
        version_telescope = str(dd['version']['name'])
        dd['sim_config']['config_dir'] = '../../bolo-calc/config'
        dd['version']['yaml']=yaml_file
        del dd['version']
        ch_names = list(dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'].keys())

        #convert to Watts
        for channel in ch_names:
            psat[yaml_file.partition('.')[0]][channel] *= 1e-12

        #set psat factor to None & delete psat entry from channel default
        dd['instrument']['channel_default']['psat_factor'] = None
        del dd['instrument']['channel_default']['psat']

        # Find the default (base) value for the varying parameter.
        base_value = dict.fromkeys(ch_names)
        for channel in ch_names:
            base_value[channel] = dd['instrument']['optics_config']['elements'][optical_element][xparam_name]

        #assign SI psat values at the channel level
        for channel in ch_names:
            dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'][channel]['psat'] = psat[yaml_file.partition('.')[0]][channel]

        # Find the default (base) value for the varying parameter.
        base_value = dict.fromkeys(ch_names)
        for channel in ch_names:
            base_value[channel] = dd['instrument']['optics_config']['elements'][optical_element][xparam_name]

        # Create dictionary to store output vectors in.
        outputs = {}
        outputs[yparam_name]={}
        for chan in ch_names:
            outputs[yparam_name][chan]=np.array([])

        # Call bolo-calc for each value of the x
        for param_value in xparam_vec:
            for chan in ch_names:
                dd['instrument']['optics_config']['elements'][optical_element][xparam_name] = param_value
            top = Top(**dd)
            top.run()
            tabs = top.instrument.tables
            for chan in ch_names:
                outputs[yparam_name][chan] = np.append(outputs[yparam_name][chan], tabs['cam_1_%s_sims' % chan][yparam_name].quantity[0])

        #plot
        plt.ioff()
        plt.rcParams.update({'font.size': 18})
        plt.rcParams['figure.figsize'] = [20, 40]
        plt.clf()
        n_chan = len(ch_names)
        ii = 2*n_chan

        for chan in ch_names:
            #print(chan+' '+str(ii))
            plt.subplot(2*n_chan,2,ii)
            plt.plot(xparam_vec,outputs[yparam_name][chan])
            plt.axvline(x = base_value[chan], color="red")
            plt.ylabel(yparam_name)
            if (ii >=2*n_chan-1):
                plt.xlabel(xparam_name)
            xmin, xmax, ymin, ymax = plt.axis()
            #plt.plot([base_value,base_value],[ymin,ymax],'r')
            xloc = xmin + 0.8*(xmax-xmin)
            yloc = ymin + 0.6*(ymax-ymin)
            plt.text(xloc,yloc,chan,color='r')
            plt.grid()
            ii = ii-1

            #print(chan+' '+str(ii))
            plt.subplot(2*n_chan,2,ii)
            plt.plot(xparam_vec,outputs[yparam_name][chan]/np.min(outputs[yparam_name][chan]))
            plt.axvline(x = base_value[chan], color="red")
            ylabelstring = yparam_name+'/NET_min'
            plt.ylabel(ylabelstring)
            if (ii >=2*n_chan-1):
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

        plt.savefig('plots/' + yaml_file.partition('.')[0] + '_' + yparam_name + '_v_' + optical_element + '_' + xparam_name + '.png', dpi=300)


        #save inputs & outputs to tesescope dictionary
        io_dict = dict.fromkeys([xparam_name, yparam_name])
        channel_dict = dict.fromkeys(ch_names)

        for chan in ch_names:
            channel_dict[chan] = io_dict.copy()
            channel_dict[chan][xparam_name] = xparam_vec
            channel_dict[chan][yparam_name] = np.array(outputs[yparam_name][chan])
            channel_dict[chan]['xdefault']=base_value[chan]
        telescopes[yaml_file] = channel_dict

    telescopes["runtime"] = datetime.today().strftime('%Y/%m/%d %H:%M:%S')
    #telescopes["input_id"] = version_date
    telescopes["variation"] =  yparam_name + '_v_' + optical_element + '_' + xparam_name

    output_file_name = telescopes['variation'] + '.toml'

    with open('outputs/' + output_file_name, "w") as toml_file:
        toml.dump(telescopes, toml_file, encoder=toml.TomlNumpyEncoder())

def net_v_AfLt(xparam_vec, yaml_list, psat):
    xparam_name = 'loss_tangent'
    yparam_name = 'NET'
    optical_element = 'alumina_filt'
    telescopes = dict.fromkeys(yaml_list)
    for telescope in telescopes:

        yaml_file = telescope
        dd = yaml.safe_load(open(yaml_file))
        version_date = str(dd['version']['date'])
        version_telescope = str(dd['version']['name'])
        dd['sim_config']['config_dir'] = '../../bolo-calc/config'
        dd['version']['yaml']=yaml_file
        del dd['version']
        ch_names = list(dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'].keys())

        #convert to Watts
        for channel in ch_names:
            psat[yaml_file.partition('.')[0]][channel] *= 1e-12

        #set psat factor to None & delete psat entry from channel default
        dd['instrument']['channel_default']['psat_factor'] = None
        del dd['instrument']['channel_default']['psat']

        # Find the default (base) value for the varying parameter.
        base_value = dict.fromkeys(ch_names)
        for channel in ch_names:
            base_value[channel] = dd['instrument']['optics_config']['elements'][optical_element][xparam_name]

        #assign SI psat values at the channel level
        for channel in ch_names:
            dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'][channel]['psat'] = psat[yaml_file.partition('.')[0]][channel]

        # Find the default (base) value for the varying parameter.
        base_value = dict.fromkeys(ch_names)
        for channel in ch_names:
            base_value[channel] = dd['instrument']['optics_config']['elements'][optical_element][xparam_name]

        # Create dictionary to store output vectors in.
        outputs = {}
        outputs[yparam_name]={}
        for chan in ch_names:
            outputs[yparam_name][chan]=np.array([])

        # Call bolo-calc for each value of the x
        for param_value in xparam_vec:
            for chan in ch_names:
                dd['instrument']['optics_config']['elements'][optical_element][xparam_name] = param_value
            top = Top(**dd)
            top.run()
            tabs = top.instrument.tables
            for chan in ch_names:
                outputs[yparam_name][chan] = np.append(outputs[yparam_name][chan], tabs['cam_1_%s_sims' % chan][yparam_name].quantity[0])

        #plot
        plt.ioff()
        plt.rcParams.update({'font.size': 18})
        plt.rcParams['figure.figsize'] = [20, 40]
        plt.clf()
        n_chan = len(ch_names)
        ii = 2*n_chan

        for chan in ch_names:
            #print(chan+' '+str(ii))
            plt.subplot(2*n_chan,2,ii)
            plt.plot(xparam_vec,outputs[yparam_name][chan])
            plt.axvline(x = base_value[chan], color="red")
            plt.ylabel(yparam_name)
            if (ii >=2*n_chan-1):
                plt.xlabel(xparam_name)
            xmin, xmax, ymin, ymax = plt.axis()
            #plt.plot([base_value,base_value],[ymin,ymax],'r')
            xloc = xmin + 0.8*(xmax-xmin)
            yloc = ymin + 0.6*(ymax-ymin)
            plt.text(xloc,yloc,chan,color='r')
            plt.grid()
            ii = ii-1

            #print(chan+' '+str(ii))
            plt.subplot(2*n_chan,2,ii)
            plt.plot(xparam_vec,outputs[yparam_name][chan]/np.min(outputs[yparam_name][chan]))
            plt.axvline(x = base_value[chan], color="red")
            ylabelstring = yparam_name+'/NET_min'
            plt.ylabel(ylabelstring)
            if (ii >=2*n_chan-1):
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

        plt.savefig('plots/' + yaml_file.partition('.')[0] + '_' + yparam_name + '_v_' + optical_element + '_' + xparam_name + '.png', dpi=300)


        #save inputs & outputs to tesescope dictionary
        io_dict = dict.fromkeys([xparam_name, yparam_name])
        channel_dict = dict.fromkeys(ch_names)

        for chan in ch_names:
            channel_dict[chan] = io_dict.copy()
            channel_dict[chan][xparam_name] = xparam_vec
            channel_dict[chan][yparam_name] = np.array(outputs[yparam_name][chan])
            channel_dict[chan]['xdefault']=base_value[chan]
        telescopes[yaml_file] = channel_dict

    telescopes["runtime"] = datetime.today().strftime('%Y/%m/%d %H:%M:%S')
    #telescopes["input_id"] = version_date
    telescopes["variation"] =  yparam_name + '_v_' + optical_element + '_' + xparam_name

    output_file_name = telescopes['variation'] + '.toml'

    with open('outputs/' + output_file_name, "w") as toml_file:
        toml.dump(telescopes, toml_file, encoder=toml.TomlNumpyEncoder())

def net_v_DetEff(xparam_vec, yaml_list, psat):
    xparam_name = 'det_eff'
    yparam_name = 'NET'
    telescopes = dict.fromkeys(yaml_list)
    for telescope in telescopes:

        yaml_file = telescope
        dd = yaml.safe_load(open(yaml_file))
        version_date = str(dd['version']['date'])
        version_telescope = str(dd['version']['name'])
        dd['sim_config']['config_dir'] = '../../bolo-calc/config'
        dd['version']['yaml']=yaml_file
        del dd['version']
        ch_names = list(dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'].keys())

        #convert to Watts
        for channel in ch_names:
            psat[yaml_file.partition('.')[0]][channel] *= 1e-12

        #set psat factor to None & delete psat entry from channel default
        dd['instrument']['channel_default']['psat_factor'] = None
        del dd['instrument']['channel_default']['psat']

        # Find the default (base) value for the varying parameter.
        base_value = dict.fromkeys(ch_names)
        try:
            for channel in ch_names:
                base_value[channel] = dd['instrument']['channel_default'][xparam_name]
        except:
            for channel in ch_names:
                base_value[channel] = dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'][channel][xparam_name]

        #assign SI psat values at the channel level
        for channel in ch_names:
            dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'][channel]['psat'] = psat[yaml_file.partition('.')[0]][channel]


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

        #plot
        plt.ioff()
        plt.rcParams.update({'font.size': 18})
        plt.rcParams['figure.figsize'] = [20, 40]
        plt.clf()
        n_chan = len(ch_names)
        ii = 2*n_chan

        for chan in ch_names:
            #print(chan+' '+str(ii))
            plt.subplot(2*n_chan,2,ii)
            plt.plot(xparam_vec,outputs[yparam_name][chan])
            plt.axvline(x = base_value[chan], color="red")
            plt.ylabel(yparam_name)
            if (ii >=2*n_chan-1):
                plt.xlabel(xparam_name)
            xmin, xmax, ymin, ymax = plt.axis()
            #plt.plot([base_value,base_value],[ymin,ymax],'r')
            xloc = xmin + 0.8*(xmax-xmin)
            yloc = ymin + 0.6*(ymax-ymin)
            plt.text(xloc,yloc,chan,color='r')
            plt.grid()
            ii = ii-1

            #print(chan+' '+str(ii))
            plt.subplot(2*n_chan,2,ii)
            plt.plot(xparam_vec,outputs[yparam_name][chan]/np.min(outputs[yparam_name][chan]))
            plt.axvline(x = base_value[chan], color="red")
            ylabelstring = yparam_name+'/NET_min'
            plt.ylabel(ylabelstring)
            if (ii >=2*n_chan-1):
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


        #save inputs & outputs to tesescope dictionary
        io_dict = dict.fromkeys([xparam_name, yparam_name])
        channel_dict = dict.fromkeys(ch_names)

        for chan in ch_names:
            channel_dict[chan] = io_dict.copy()
            channel_dict[chan][xparam_name] = xparam_vec
            channel_dict[chan][yparam_name] = np.array(outputs[yparam_name][chan])
            channel_dict[chan]['xdefault']=base_value[chan]
        telescopes[yaml_file] = channel_dict

    telescopes["runtime"] = datetime.today().strftime('%Y/%m/%d %H:%M:%S')
    #telescopes["input_id"] = version_date
    telescopes["variation"] = yparam_name + '_v_' + xparam_name

    output_file_name = telescopes['variation'] + '.toml'

    with open('outputs/' + output_file_name, "w") as toml_file:
        toml.dump(telescopes, toml_file, encoder=toml.TomlNumpyEncoder())



def net_v_PsatFac(xparam_vec, yaml_list):
    xparam_name = 'psat_factor'
    yparam_name = 'NET'
    telescopes = dict.fromkeys(yaml_list)
    for telescope in telescopes:

        yaml_file = telescope
        dd = yaml.safe_load(open(yaml_file))
        version_date = str(dd['version']['date'])
        version_telescope = str(dd['version']['name'])
        dd['sim_config']['config_dir'] = '../../bolo-calc/config'
        dd['version']['yaml']=yaml_file
        del dd['version']
        ch_names = list(dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'].keys())

        # #convert to Watts
        # for channel in ch_names:
        #     psat[yaml_file.partition('.')[0]][channel] *= 1e-12

        #set psat factor to None & delete psat entry from channel default
        #dd['instrument']['channel_default']['psat_factor'] = None
        del dd['instrument']['channel_default']['psat']

        # Find the default (base) value for the varying parameter.
        base_value = dict.fromkeys(ch_names)
        for channel in ch_names:
            base_value[channel] = dd['instrument']['channel_default'][xparam_name]

        #assign SI psat values at the channel level
        # for channel in ch_names:
        #     dd['instrument']['camera_config']['elements']['cam_1']['chan_config']['elements'][channel]['psat'] = psat[yaml_file.partition('.')[0]][channel]


        # Create dictionary to store output vectors in.
        outputs = {}
        outputs[yparam_name]={}
        outputs['psat']={}
        for chan in ch_names:
            outputs[yparam_name][chan]=np.array([])
            outputs['psat'][chan]=np.array([])

        # Call bolo-calc for each value of the x
        for param_value in xparam_vec:
            for chan in ch_names:
                dd['instrument']['channel_default'][xparam_name] = param_value
            top = Top(**dd)
            top.run()
            tabs = top.instrument.tables
            for chan in ch_names:
                outputs[yparam_name][chan] = np.append(outputs[yparam_name][chan], tabs['cam_1_%s_sims' % chan][yparam_name].quantity[0])
                outputs['psat'][chan] = np.append(outputs['psat'][chan], tabs['cam_1_%s_sims' % chan]['P_sat'].quantity[0])
                #pdb.set_trace()
        #plot
        plt.ioff()
        plt.rcParams.update({'font.size': 18})
        plt.rcParams['figure.figsize'] = [20, 40]
        plt.clf()
        n_chan = len(ch_names)
        ii = 2*n_chan

        for chan in ch_names:
            #print(chan+' '+str(ii))
            plt.subplot(2*n_chan,2,ii)
            plt.plot(xparam_vec,outputs[yparam_name][chan])
            plt.axvline(x = base_value[chan], color="red")
            plt.ylabel(yparam_name)
            if (ii >=2*n_chan-1):
                plt.xlabel(xparam_name)
            xmin, xmax, ymin, ymax = plt.axis()
            #plt.plot([base_value,base_value],[ymin,ymax],'r')
            xloc = xmin + 0.8*(xmax-xmin)
            yloc = ymin + 0.6*(ymax-ymin)
            plt.text(xloc,yloc,chan,color='r')
            plt.grid()
            ii = ii-1

            #print(chan+' '+str(ii))
            plt.subplot(2*n_chan,2,ii)
            plt.plot(xparam_vec,outputs[yparam_name][chan]/np.min(outputs[yparam_name][chan]))
            plt.axvline(x = base_value[chan], color="red")
            ylabelstring = yparam_name+'/NET_min'
            plt.ylabel(ylabelstring)
            if (ii >=2*n_chan-1):
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


        #save inputs & outputs to tesescope dictionary
        io_dict = dict.fromkeys([xparam_name, yparam_name, 'psat'])
        channel_dict = dict.fromkeys(ch_names)

        for chan in ch_names:
            channel_dict[chan] = io_dict.copy()
            channel_dict[chan][xparam_name] = xparam_vec
            channel_dict[chan][yparam_name] = np.array(outputs[yparam_name][chan])
            channel_dict[chan]['psat'] = np.array(outputs['psat'][chan])
            channel_dict[chan]['xdefault']=base_value[chan]

        telescopes[yaml_file] = channel_dict

    telescopes["runtime"] = datetime.today().strftime('%Y/%m/%d %H:%M:%S')
    #telescopes["input_id"] = version_date
    telescopes["variation"] = yparam_name + '_v_' + xparam_name

    output_file_name = telescopes['variation'] + '.toml'

    with open('outputs/' + output_file_name, "w") as toml_file:
        toml.dump(telescopes, toml_file, encoder=toml.TomlNumpyEncoder())
