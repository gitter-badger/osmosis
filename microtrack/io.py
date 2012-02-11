"""

=====================
File input and output
=====================

The *nominal* PDB file format specification is as follows, but note that some
of these things are not implemented in PDB version 3. For example, there are no
algorithms to speak of, so that whole bit is completely ignored. 

 The file-format is organized as a semi-hierarchical data-base, according to
    the following specification:
    [ header size] - int
    -- HEADER FOLLOWS --
    [4x4 xform matrix ] - 16 doubles
    [ number of pathway statistics ] - int
    for each statistic:
        [ currently unused ] - bool
        [ is stat stored per point, or aggregate per path? ] - bool
        [ currently unused ] - bool
        [ name of the statistic ] - char[255]
        [ currently unused ] - char[255]
        [ unique ID - unique identifier for this stat across files ] - int

    ** The algorithms bit is not really working as advertised: **
    [ number of algorithms ] - int
    for each algorithm:
       [ algorithm name ] - char[255]
       [ comments about the algorithm ] - char[255]
       [ unique ID -  unique identifier for this algorithm, across files ] - int

    [ version number ] - int
    -- HEADER ENDS --
    [ number of pathways ] - int
    [ pts per fiber ] - number of pathways integers
    for each pathway:
       [ header size ] - int
       -- PATHWAY HEADER FOLLOWS --
        ** The following are not actually encoded in the fiber header and are
         currently set in an arbitrary fashion: **
       [ number of points ] - int
       [ algorithm ID ] - int
       [ seed point index ] - int

       for each statistic:
          [ precomputed statistical value ] - double
       -- PATHWAY HEADER ENDS --
       for each point:
            [ position of the point ] - 3 doubles (ALREADY TRANSFORMED from
                                                   voxel space!)  
          for each statistic:
             IF computed per point (see statistics header, second bool field):
             for each point:
               [ statistical value for this point ] - double


"""

# Import from standard lib: 
import struct 
import os

import numpy as np
import microtrack.fibers as mtf


# XXX The following function is way too long. Break it up!
def fg_from_pdb(file_name, verbose=True):
    """
    Read the definition of a fiber-group from a .pdb file
    Parameters
    ----------
    file_name: str
       Full path to the .pdb file
    Returns
    -------
    A FiberGroup object

    Note
    ----
    This only reads Version 3 PDB. For the full file-format spec, see the
    microtrack.io module top-level docstring
    
    """
    # Read the file as binary info:
    f_obj = file(file_name, 'r')
    f_read = f_obj.read()
    f_obj.close()
    # This is an updatable index into this read:
    idx = 0
    
    # First part is an int encoding the offset to the fiber part: 
    offset, idx = _unpacker(f_read, idx, 1)  

    # Next bit are doubles, encoding the xform (4 by 4 = 16 of them):
    xform, idx  = _unpacker(f_read, idx, 16, 'double')
    xform = np.reshape(xform, (4, 4))
   
    # Next is an int encoding the number of stats: 
    numstats, idx = _unpacker(f_read, idx, 1)

    # The stats header is a dict with lists holding the stat per 
    stats_header = dict(luminance_encoding=[],  # int => bool
                        computed_per_point=[],  # int => bool
                        viewable=[],  # int => bool
                        agg_name=[],  # char array => string
                        local_name=[],  # char array => string
                        uid=[]  # int
        )

    # Read the stats header:
    counter = 0
    while counter < numstats:
        counter += 1
        for k in ["luminance_encoding",
                  "computed_per_point",
                  "viewable"]:
            this, idx = _unpacker(f_read, idx, 1)
            stats_header[k].append(np.bool(this))

        for k in ["agg_name", "local_name"]:
            this, idx = _unpacker(f_read, idx, 255, 'char')
            stats_header[k].append(_word_maker(this))
        # Must have integer reads be word aligned (?): 
        idx += 2
        this, idx = _unpacker(f_read, idx, 1)
        stats_header["uid"].append(this)
    
    # We skip the whole bit with the algorithms and go straight to the version
    # number, which is one int length before the fibers:  
    idx = offset - 4
    version, idx = _unpacker(f_read, idx, 1)
    if version != 3:
        raise ValueError("Can only read PDB version 3 files")
    elif verbose:
        print("Loading a PDB version 3 file from: %s"%file_name)

    # How many fibers?
    numpaths, idx = _unpacker(f_read, idx, 1)
    # The next few bytes encode the number of points in each fiber:
    pts_per_fiber, idx = _unpacker(f_read, idx, numpaths)
    total_pts = np.sum(pts_per_fiber)
    # Next we have the xyz coords of the nodes in all fibers: 
    fiber_pts, idx = _unpacker(f_read, idx, total_pts * 3, 'double')

    # We extract the information on a fiber-by-fiber basis
    pts_read = 0 
    pts = []
    for p_idx in range(numpaths):
        n_nodes = pts_per_fiber[p_idx]
        pts.append(np.reshape(
                   fiber_pts[pts_read * 3:(pts_read + n_nodes) * 3],
                   (n_nodes, 3)).T)
        pts_read += n_nodes
        if verbose and np.mod(p_idx, 1000)==0:
            print("Loaded %s of %s paths"%(p_idx, numpaths[0]))            

    f_stats_dict = {}
    for stat_idx in range(numstats):
        per_fiber_stat, idx = _unpacker(f_read, idx, numpaths, 'double')
        f_stats_dict[stats_header["local_name"][stat_idx]] = per_fiber_stat
    
    n_stats_dict = {}
    for stat_idx in range(numstats):
        pts_read = 0
        if stats_header["computed_per_point"][stat_idx]:
            name = stats_header["local_name"][stat_idx]
            n_stats_dict[name] = []
            per_point_stat, idx = _unpacker(f_read, idx, total_pts, 'double')
            for p_idx in range(numpaths):
                n_stats_dict[name].append(
                    per_point_stat[pts_read : pts_read + pts_per_fiber[p_idx]])
                
                pts_read += pts_per_fiber[p_idx]
        else:
            per_point_stat.append([])

    fibers = []
    # Initialize all the fibers:
    for p_idx in range(numpaths):
        f_stat_k = f_stats_dict.keys()
        f_stat_v = [f_stats_dict[k][p_idx] for k in f_stat_k]
        n_stats_k = n_stats_dict.keys()
        n_stats_v = [n_stats_dict[k][p_idx] for k in n_stats_k]
        fibers.append(mtf.Fiber(pts[p_idx],
                            xform,
                            fiber_stats=dict(zip(f_stat_k, f_stat_v)),
                            node_stats=dict(zip(n_stats_k, n_stats_v))))
    if verbose:
        print("Done reading from file")
        
    name = os.path.split(file_name)[-1].split('.')[0]
    return mtf.FiberGroup(fibers, name=name)
    
# This one's a global used in both packing and unpacking the data 
    
_fmt_dict = {'int':['=i', 4],
             'double':['=d', 8],
             'char':['=c', 1],
             'bool':['=?', 1],
             #'uint':['=I', 4],
                }

def pdb_from_fg(fg, file_name='fibers.pdb', verbose=True):
    """
    Create a pdb file from a microtrack.fibers.FiberGroup class instance.

    Parameters
    ----------
    fg: a FiberGroup object

    file_name: str
       Full path to the pdb file to be saved.
    
    """

    fwrite = file(file_name, 'w')
    int_size = _fmt_dict['int'][1]
    double_size = _fmt_dict['double'][1]
    stats_hdr_sz = (3 * _fmt_dict['bool'][1] +
                    int_size +
                    2 * _fmt_dict['char'][1] * 255)
    

    # The total number of stats are both node-stats and fiber-stats:
    n_stats = len(fg[0].fiber_stats.keys()) + len(fg[0].node_stats.keys())
    n_algs = 0  # Always 0. This seems like a misimplementation of the spec
    
    # This is the 'offset' to the beginning of the fiber-data. Note that we are
    # just skipping the whole algorithms thing, since that seems to be unused
    # in mrDiffusion anyway. 
    hdr_sz = (4 * int_size + # ints: hdr_sz itself, n_stats, n_algs (always 0),
                             # version
             16 * double_size + # doubles: the 4 by 4 affine
             n_stats * stats_hdr_sz) # The stats part of the header
    
    _packer(fwrite, hdr_sz)
    if fg.affine is None:
        affine = tuple(np.eye(4).ravel().squeeze())
    else:
        affine = tuple(np.array(fg.affine).ravel().squeeze())

    _packer(fwrite, affine, 'double')
    _packer(fwrite, n_stats)

    # This is the number of algorithms. Always 0.
    _packer(fwrite, 0)
    # This is the PDB file version:
    _packer(fwrite, 3)

    # We are going to assume that fibers are homogenous on the following
    # properties. XXX Should we check that when making FiberGroup instances? 
    uid = 0
    for f_stat in fg[0].fiber_stats:
        _packer(fwrite, True, 'bool')   # currently unused
        _packer(fwrite, False, 'bool')  # Is this per-point
        _packer(fwrite, True, 'bool')   # currently unused
        _stat_hdr_set(fwrite, f_stat, uid)
        uid += 1  # We keep tracking that across fiber and node stats

    for n_stat in fg[0].node_stats:
        # Three True bools for this one:
        for x in range(3):
            _packer(fwrite, True, 'bool')

        _stat_hdr_set(fwrite, n_stat, uid)
        uid += 1
    
    _packer(fwrite, fg.n_fibers)
    for fib in fg.fibers:
        # How many coords in each fiber:
        _packer(fwrite, fib.coords.shape[-1])

    # x,y,z coords in each fiber:
    for fib in fg.fibers:
        _packer(fwrite, fib.coords.T, 'double')

    if verbose:
        "Done saving data in file%s"%file_name

    fwrite.close()

def _unpacker(file_read, idx, obj_to_read, fmt='int'):

    """
    Helper function to unpack binary data from files with the struct library.

    Relies on http://docs.python.org/library/struct.html

    Parameters
    ----------
    file_read: The output of file.read() from a file object
    idx: An index into x
    obj_to_read: How many objects to read
    fmt: A format string, telling us what to read from there 
    """
    # For each one, this is [fmt_string, size] 
    
    fmt_str = _fmt_dict[fmt][0]
    fmt_sz = _fmt_dict[fmt][1]
    
    out = np.array([struct.unpack(fmt_str,
                    file_read[idx + fmt_sz * j:idx + fmt_sz + fmt_sz * j])[0]
        for j in range(obj_to_read)])
                         
    idx += obj_to_read * fmt_sz
    return out, idx

def _packer(file_write, vals, fmt='int'):
    """
    Helper function to pack binary data to files, using the struct library:

    Relies on http://docs.python.org/library/struct.html    
    
    """
    fmt_str = _fmt_dict[fmt][0]
    if np.iterable(vals):
        for pack_this in vals:
            s = struct.pack(fmt_str, pack_this)
            file_write.write(s)

    else:
        s = struct.pack(fmt_str, vals)
        file_write.write(s)
    
def _word_maker(arr):
    """
    Helper function Make a string out of pdb stats header "name" variables 
    """
    make_a_word = []
    for this in arr:
        if this: # The sign that you reached the end of the word is an empty
                 # char
            make_a_word.append(this)
        else:
            break
    return ''.join(make_a_word)
    
def _char_list_maker(name):
    """
    Helper function that does essentially the opposite of _word_maker. Takes a
    string and makes it into a 255 long list of characters with the name of a
    stat, followed by a single white-space and then 'g' for the rest of the 255 
    """

    l = list(name)
    l.append('\x00')  # The null character
    x = len(l)
    while x<255:
        l.append('g')
        x += 1
    return l 

def _stat_hdr_set(fwrite, stat, uid):
    """
    Helper function for writing stuff into stats header portion of pdb files
    """
    # Name of the stat: 
    char_list = _char_list_maker(stat)
    _packer(fwrite, char_list, 'char')  
    _packer(fwrite, char_list, 'char')  # Twice for some reason
    _packer(fwrite, uid) # These might get reordered upon
                                    # resaving on different platforms, because
                                    # dict keys come in no particular order...

    