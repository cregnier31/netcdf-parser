#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from glob import glob
import os
import sys
import itertools
import operator,getopt
import re

def main():
    '''Generates XML file to be displayed by MyOcean2 site. 

    Files are parsed by splitting basenames by underscore,
    grouping the results into a tree and mapping that tree
    into an XML data file.

    Requirements
    ------------
        plot_dir: specifies the location of the plots
        text_dir: specifies the location of the text descriptions.
        search_pattern: way of locating the required files.

    '''
    options=sys.argv[1:]
    print "options %s " %(options)
    keywords = ['site-dir=']
    cla_opts = getopt.getopt(options,'',keywords)
    for o,p in cla_opts[0] :
       if o in ['--site-dir'] :
           ll_path=True
           site_dir = p
           if ll_path :
               print "PATH %s " %(site_dir)
               # Settings
               plot_dir = os.path.join(site_dir, 'plot')
               text_dir = os.path.join(site_dir, 'text')
               xml_name = 'myo2_site_menu.xml'
               xml_path = os.path.join(site_dir, xml_name)
               # Plot files
               search_pattern = os.path.join(plot_dir, '*.png')
               print "search pattern %s " %(search_pattern)
               plot_files = sorted(glob(search_pattern))
               # Text files
               search_pattern = os.path.join(text_dir, 'product*.xml')
               text_files = sorted(glob(search_pattern))
               # Generate the required xml
               doc = generate_xml(plot_files, text_files,
                                  plot_dir='plot', text_dir='text')

               # Write to file
               # write to xml file
               xml_file = open(xml_path,"w")
               doc.writexml(xml_file)
               xml_file.close()

def generate_xml(plot_files, text_files,
                 plot_dir='', text_dir=''):
    '''Parses the input lists into a predesigned xml layout.

    Description
        A swiss army knife XML builder. It ingests names and
        generates a XML tree with the input.

    Arguments
        plot_files: files which follow the MyOcean2 naming conventions.
        text_files: files which follow the MyOcean2 naming conventions.

    Options
        plot_dir: a prefix to help the website locate the files 
                  relative to the website top level URL. 
        text_dir: a prefix to help the website locate the files
                  relative to the website top level URL. 

    Returns
        doc: XML Document object with the input specified in a convenient
             manner.

    '''
    import xml.dom.minidom

    grid_files = [file for file in plot_files if 'grid' in file]
    oc_files = [file for file in plot_files if 'oc-plot' in file]
    insitu_files = [file for file in plot_files if 'insitu-plot' in file]
    metric_files = [file for file in plot_files if 'novelmetrics-plot' in file] 
    plot_files = [file for file in plot_files if 'grid' not in file and 'novelmetrics-plot' not in file and 'insitu-plot' not in file and 'oc-plot' not in file and 'Contingency' not in file and 'Discriminant' not in file]
    
    # Initialise XML Document
    doc = xml.dom.minidom.Document()
    menu_elem = makeTrunk(doc, "menu")

    # Build plot file XML
    rel_names = switch_dirnames(plot_files, plot_dir)
    database = split_names(rel_names, sep='_', elems=[0, 1, 3, 4, 6])
    database.append(rel_names)
    database = zip(*database)
    master_dict = {}
    get_item = operator.itemgetter(0)
    for pc, pc_group in itertools.groupby(sorted(database, key=get_item), get_item):
        master_dict[str(pc)] = {}
        get_item = operator.itemgetter(1)
        for prod, prod_group in itertools.groupby(sorted(pc_group, key=get_item), get_item):
            master_dict[str(pc)][str(prod)]= {}
            get_item = operator.itemgetter(2)
            for var, var_group in itertools.groupby(sorted(prod_group, key=get_item), get_item):
                master_dict[str(pc)][str(prod)][str(var)] = {}
                get_item = operator.itemgetter(3)
                #if pc != 'oceancolour':
                for reg, reg_group in itertools.groupby(sorted(var_group, key=get_item), get_item):
                    master_dict[str(pc)][str(prod)][str(var)][str(reg)] = {}
                    get_item = operator.itemgetter(4)
                    for dpth, dpth_group in itertools.groupby(sorted(reg_group, key=get_item), get_item):
                        master_dict[str(pc)][str(prod)][str(var)][str(reg)][str(dpth)] = {}
                        data = list(dpth_group)
                        files = list(zip(*data)[-1])
                        for plotfile in files:  #get all plots ito next dictionatry level, key is plotname
                            master_dict[str(pc)][str(prod)][str(var)][str(reg)][str(dpth)][str(plotfile)] = {}
                            master_dict[str(pc)][str(prod)][str(var)][str(reg)][str(dpth)][str(plotfile)]=plotfile

    
    pc_keys=sorted(master_dict.keys())  # PC
    print pc_keys
    #sort here PCs into model and obs for top banner order
    pc_keys=['global','arctic','balticsea','nws','ibi','medsea','blacksea','sealevel','sst','wind']
    pc_keys=['global','arctic','balticsea','nws','ibi','medsea','sealevel','sst','wind']  # Black Sea no longer in MyOcean
    for pc2 in pc_keys:
        print "key : "+pc2
        pc_elem = appendName(doc, menu_elem, 'pc', pc2)
        prod_keys=sorted(master_dict[pc2].keys())
        for prod2 in prod_keys:
            prod_elem = appendName(doc, pc_elem, 'product', prod2)  
            var_keys=sorted(master_dict[pc2][prod2].keys())             
            for var2 in var_keys:
                var_elem = appendName(doc, prod_elem, 'variable', var2)
                reg_keys=sorted(master_dict[pc2][prod2][var2].keys()) #alphabetic sort
                #sort regions here so full-domain first
                sorted_reg_keys=[]
                for reg2 in reg_keys:
                    if reg2 == 'full-domain':
                         sorted_reg_keys.insert(0, reg2)
                    else:
                         sorted_reg_keys.append(reg2)
                for reg2 in sorted_reg_keys:
                    reg_elem = appendName(doc, var_elem, 'area', reg2)
                    dep_keys=master_dict[pc2][prod2][var2][reg2].keys()
                    #sort depths here something special needed
                    sorted_depth_keys=[]
                    if (len(dep_keys) is 1) and dep_keys[0] == 'surface':
                        sorted_dep_keys = ['surface',]
                    else:
                        sorted_dep_keys=sorted(master_dict[pc2][prod2][var2][reg2].keys(), key = lambda x: int(x.split("-")[0]))
                    for dep2 in sorted_dep_keys:
                        if dep2 != 'surface':
                        # strip leading zeros off depth value for div
                            LHS_depstrip=dep2.split('-')[0]
                            if LHS_depstrip == "0000":
                                LHS_depstrip_str="0"
                            else:
                                LHS_depstrip_str=LHS_depstrip.lstrip("0")
                            RHS_depstrip=dep2.split('-')[1]
                            RHS_depstrip=re.sub('m','',RHS_depstrip)
                            if RHS_depstrip == "0000":
                                RHS_depstrip_str="0"
                            else:
                                RHS_depstrip_str=RHS_depstrip.lstrip("0")
                            depstrip=LHS_depstrip_str+'-'+RHS_depstrip_str+'m'
                        else:
                            depstrip='surface'
                        dpth_elem = appendName(doc, reg_elem, 'depth', depstrip)
                        sorted_file_keys=sorted(master_dict[pc2][prod2][var2][reg2][dep2].keys(), reverse=True)
                        for plotfile2 in sorted_file_keys:
                            appendName(doc, dpth_elem, 'plot', master_dict[pc2][prod2][var2][reg2][dep2][plotfile2])


    # Build grid file XML                    
    rel_names = switch_dirnames(grid_files, plot_dir)
    database = split_names(rel_names, sep='_', elems=[0, 1, 3])
    database.append(rel_names)
    database = zip(*database)

    get_item = operator.itemgetter(0)
    for pc, pc_group in itertools.groupby(sorted(database, key=get_item), get_item):
        pc_elem = updateTree(doc, menu_elem, 'pc', tag_name=pc) 
        get_item = operator.itemgetter(1)
        for prod, prod_group in itertools.groupby(sorted(pc_group, key=get_item), get_item):
            prod_elem = updateTree(doc, pc_elem, 'product', tag_name=prod) 
            get_item = operator.itemgetter(2)
            for var, var_group in itertools.groupby(sorted(prod_group, key=get_item), get_item):
                var_elem = updateTree(doc, prod_elem, 'variable', tag_name=var) 
                data = list(var_group)
                files = list(zip(*data)[-1])
                for file in files:
                    updateTree(doc, var_elem, 'bar', tag_name=file)

###############

    # Build pre-created OC TAC plots    
    rel_names = switch_dirnames(oc_files, plot_dir)
    database = split_names(rel_names, sep='_', elems=[0, 1, 3, 4])
    database.append(rel_names)
    database = zip(*database)
    master_dict2 = {}
    get_item = operator.itemgetter(0)
    for pc, pc_group in itertools.groupby(sorted(database, key=get_item), get_item):
        master_dict2[str(pc)] = {}
        get_item = operator.itemgetter(1)
        for prod, prod_group in itertools.groupby(sorted(pc_group, key=get_item), get_item):
            master_dict2[str(pc)][str(prod)]= {}
            get_item = operator.itemgetter(2)
            for var, var_group in itertools.groupby(sorted(prod_group, key=get_item), get_item):
                master_dict2[str(pc)][str(prod)][str(var)] = {}
                data = list(var_group)
                files = list(zip(*data)[-1])
                for plotfile in files:  #get all plots ito next dictionatry level, key is plotname
                    master_dict2[str(pc)][str(prod)][str(var)][str(plotfile)] = {}
                    master_dict2[str(pc)][str(prod)][str(var)][str(plotfile)]=plotfile
    pc_keys2=['oceancolour',]
    for pc2 in pc_keys2:
        pc_elem = appendName(doc, menu_elem, 'pc', pc2)
        prod_keys=sorted(master_dict2[pc2].keys())
        for prod2 in prod_keys:
            prod_elem = appendName(doc, pc_elem, 'product', prod2)  
            var_keys=sorted(master_dict2[pc2][prod2].keys())             
            for var2 in var_keys:
                var_elem = appendName(doc, prod_elem, 'variable', var2)
                sorted_file_keys=sorted(master_dict2[pc2][prod2][var2].keys(), reverse=True)
                for plotfile2 in sorted_file_keys:
                    appendName(doc, var_elem, 'bar', master_dict2[pc2][prod2][var2][plotfile2])

###############

    # Build pre-created insitu TAC plots
    print "TAC plots"
    rel_names = switch_dirnames(insitu_files, plot_dir)
    print rel_names
    database = split_names(rel_names, sep='_', elems=[0, 3, 4])
    database.append(rel_names)
    database = zip(*database)
    master_dict2 = {}
    get_item = operator.itemgetter(0)
    for pc, pc_group in itertools.groupby(sorted(database, key=get_item), get_item):
        master_dict2[str(pc)] = {}
        get_item = operator.itemgetter(1)
        for prod, prod_group in itertools.groupby(sorted(pc_group, key=get_item), get_item):
            master_dict2[str(pc)][str(prod)]= {}
            get_item = operator.itemgetter(2)
            for var, var_group in itertools.groupby(sorted(prod_group, key=get_item), get_item):

                master_dict2[str(pc)][str(prod)][str(var)] = {}
                data = list(var_group)
                files = list(zip(*data)[-1])
                for plotfile in files:  #get all plots ito next dictionatry level, key is plotname
                    master_dict2[str(pc)][str(prod)][str(var)][str(plotfile)] = {}
                    master_dict2[str(pc)][str(prod)][str(var)][str(plotfile)]=plotfile
    pc_keys2=['insitu',]
    for pc2 in pc_keys2:
        pc_elem = appendName(doc, menu_elem, 'pc', pc2)
        prod_keys=sorted(master_dict2[pc2].keys()) # not important sorted here, but keep orig line
        prod_ids=['013-030','013-031','013-032','013-036','013-033','013-035','013-034'] #required order
        #prod_ids=['013-030','013-031','013-032','013-036','013-033','013-035',] #required order ignoring Black Sea plots
        prod_keys2=list(prod_ids) # set as list here and re-write with sorted list of long names later
        print prod_keys2
        for pi in range(len(prod_ids)):
            print "pi : "+prod_ids[pi]
            print 'Prod key : ',prod_keys
            print 'Prod ids :',prod_ids
            matching = [s for s in prod_keys if prod_ids[pi] in s] # full name capture
            ip = prod_keys.index(matching[0]) # where matching element is
            prod_keys2[pi]=prod_keys[ip] # reorder and set prod_keys2 from short to long names
        for prod2 in prod_keys2:
            print "Key :"+prod2
            prod_elem = appendName(doc, pc_elem, 'product', prod2)  
            var_keys=sorted(master_dict2[pc2][prod2].keys()) 
            #set required order of variables
            #var_ids=['obs-location','obs-depth','platform-per-parameter','platform-quality-per-parameter',
             #       'platformperparameter','platformqualityperparameter','obsdepth','obslocation']
            var_ids=['obs-location','obs-depth','platform-per-parameter','platform-quality-per-parameter']
            var_keys2=list(var_ids)
            for vi in range(len(var_ids)):
                matching = [s for s in var_keys if var_ids[vi] in s] # full name capture
                if len(matching) > 0 : 
                    iv = var_keys.index(matching[0]) # where matching element is
                    var_keys2[vi]=var_keys[iv] # reorder and set prod_keys2 from short to long names
            for var2 in var_keys2:
                print var2
                var_elem = appendName(doc, prod_elem, 'variable', var2)
                sorted_file_keys=sorted(master_dict2[pc2][prod2][var2].keys(), reverse=True)
                for plotfile2 in sorted_file_keys:
                    appendName(doc, var_elem, 'bar', master_dict2[pc2][prod2][var2][plotfile2])

###############

    # Build pre-created Novel Metrics plots 

    # Going to need Area itemgetter here
   
    rel_names = switch_dirnames(metric_files, plot_dir)
    database = split_names(rel_names, sep='_', elems=[0, 1, 3, 4, 5])
    database.append(rel_names)
    database = zip(*database)
    master_dict2 = {}
    get_item = operator.itemgetter(0)
    for pc, pc_group in itertools.groupby(sorted(database, key=get_item), get_item):
        master_dict2[str(pc)] = {}
        get_item = operator.itemgetter(1)
        for prod, prod_group in itertools.groupby(sorted(pc_group, key=get_item), get_item):
            master_dict2[str(pc)][str(prod)]= {}
            get_item = operator.itemgetter(2)
            for var, var_group in itertools.groupby(sorted(prod_group, key=get_item), get_item):
                master_dict2[str(pc)][str(prod)][str(var)] = {}
                get_item = operator.itemgetter(3)
                for reg, reg_group in itertools.groupby(sorted(var_group, key=get_item), get_item):
                    master_dict2[str(pc)][str(prod)][str(var)][str(reg)] = {}
                    get_item = operator.itemgetter(4)
                    for dpth, dpth_group in itertools.groupby(sorted(reg_group, key=get_item), get_item):
                        master_dict2[str(pc)][str(prod)][str(var)][str(reg)][str(dpth)] = {}
                        data = list(dpth_group)
                        files = list(zip(*data)[-1])
                        for plotfile in files:  #get all plots ito next dictionatry level, key is plotname
                            master_dict2[str(pc)][str(prod)][str(var)][str(reg)][str(dpth)][str(plotfile)] = {}
                            master_dict2[str(pc)][str(prod)][str(var)][str(reg)][str(dpth)][str(plotfile)]=plotfile

###############
        
    pc_keys2=['novelmetrics',]
    for pc2 in pc_keys2:
        pc_elem = appendName(doc, menu_elem, 'pc', pc2)
        prod_keys=sorted(master_dict2[pc2].keys())
        for prod2 in prod_keys:
            prod_elem = appendName(doc, pc_elem, 'product', prod2)  
            var_keys=sorted(master_dict2[pc2][prod2].keys())   
            #sort variables into order of increasing complexity
            if (prod2 == 'ocean-currents'):
                var_ids=['observation-model','continuous-statistics','categorical-statistics','gerrity-skill-score']
            if (prod2 == 'triple-collocation'):
                var_ids=['sst']
            if (prod2 == 'biogeochemistry'):
                var_ids=['continuous-metrics','categorical-metrics','p90']
            var_keys2=list(var_ids)
            for var2 in var_keys2:
                var_elem = appendName(doc, prod_elem, 'variable', var2)
                if (prod2 == 'ocean-currents'):
                    reg_keys=sorted(master_dict2[pc2][prod2][var2].keys()) #alphabetic sort
                if (prod2 == 'triple-collocation'):
                    reg_keys=['insitu-locations','measurements-per-month','error-variance-triplets']
                if (prod2 == 'biogeochemistry'):
                    if (var2 == 'categorical-metrics'):
                        reg_keys=['baltic-sea-flexible-translation','med-sea-flexible-translation','north-sea-flexible-translation']
                    if (var2 == 'continuous-metrics'):
                        reg_keys=['baltic-sea-flexible-translation','baltic-sea-mediumcoarse-translation','baltic-sea-coarse-translation','med-sea-flexible-translation','med-sea-mediumcoarse-translation','med-sea-coarse-translation','north-sea-flexible-translation','north-sea-mediumcoarse-translation','north-sea-coarse-translation']
                    if (var2 == 'p90'):
                        reg_keys=['baltic-sea-model','baltic-sea-satellite','med-sea-model','med-sea-satellite','north-sea-model','north-sea-satellite']
                for reg2 in reg_keys:
                    reg_elem = appendName(doc, var_elem, 'area', reg2)
                    dep_keys=master_dict2[pc2][prod2][var2][reg2].keys()
                    #sort depths here something special needed
                    sorted_depth_keys=[]
                    if (len(dep_keys) is 1) and dep_keys[0] == 'surface':
                        sorted_dep_keys = ['surface',]
                    else:
                        sorted_dep_keys=sorted(master_dict2[pc2][prod2][var2][reg2].keys(), key = lambda x: int(x.split("-")[0]))
                    for dep2 in sorted_dep_keys:
                        if dep2 != 'surface':
                        # strip leading zeros for div
                            LHS_depstrip=dep2.split('-')[0]
                            if LHS_depstrip == "0000":
                                LHS_depstrip_str="0"
                            else:
                                LHS_depstrip_str=LHS_depstrip.lstrip("0")
                            RHS_depstrip=dep2.split('-')[1]
                            RHS_depstrip=re.sub('m','',RHS_depstrip)
                            if RHS_depstrip == "0000":
                                RHS_depstrip_str="0"
                            else:
                                RHS_depstrip_str=RHS_depstrip.lstrip("0")
                            depstrip=LHS_depstrip_str+'-'+RHS_depstrip_str+'m'
                        else:
                            depstrip='surface'
                        dpth_elem = appendName(doc, reg_elem, 'depth', depstrip)
                        sorted_file_keys=sorted(master_dict2[pc2][prod2][var2][reg2][dep2].keys(), reverse=True)
                        for plotfile2 in sorted_file_keys:
                            appendName(doc, dpth_elem, 'plot', master_dict2[pc2][prod2][var2][reg2][dep2][plotfile2])
#


########

    # Build text file XML
    branch_names = ['pc', 'product', 'variable']
    text_files = switch_dirnames(text_files, text_dir)
    products, = split_names(text_files, sep='_', elems=[3])
    pcs = get_pcs(products)
    params = [pcs, products, text_files]
    database = zip(*params)
    get_item = operator.itemgetter(0)
    for pc, pc_group in itertools.groupby(sorted(database, key=get_item), get_item):
        pc_elem = updateTree(doc, menu_elem, 'pc', tag_name=pc) 
        get_item = operator.itemgetter(1)
        for prod, prod_group in itertools.groupby(sorted(pc_group, key=get_item), get_item):
            prod_elem = updateTree(doc, pc_elem, 'product', tag_name=prod) 
            data = list(prod_group)
            files = list(zip(*data)[-1])  
            for file in files:  
                prod_elem =  updateTree(doc, prod_elem, 'txt', tag_name=file)
    
    #return entire xml file
    return doc

def get_pcs(products):
    '''Converts product names to production centre.

    Description
        In nearly all cases the production centre can
        be extracted from the product name. However, in
        some cases a translation is necessary.
    '''
    lookup = {'northwestshelf': 'nws', 'ocean' : 'novelmetrics', 'triple' : 'novelmetrics' , 'biogeochemistry' : 'novelmetrics'}
    pcs = []
    for product in products:
        pc = product.split('-')[0]
        pc = lookup.get(pc, pc)
        pcs.append(pc)
    return pcs

def makeTrunk(doc, trunk):
    trunk_elem = doc.createElement(trunk)
    doc.appendChild(trunk_elem)
    return trunk_elem

def updateTree(doc, parent, tag, tag_name=None):
    '''Adds branches as necessary to a Tree.

    Given a parent branch, either the first child
    is returned or a search for the correct child 
    is performed and the missing child filled in.

    Options
    -------
        tag_name: if present not only will the correct
                  branch be added to the parent, but 
                  also a name tag with the corresponding
                  nodeValue as :tag_name:
    '''
    # Find/create child tag
    tag_elems = parent.getElementsByTagName(tag)
    result = findName(tag_elems, tag_name)
    if result is False:
        # Generate tag with correct name
        tag_elem = doc.createElement(tag)
        name_elem = doc.createElement("name")
        text_elem = doc.createTextNode(tag_name)
        parent.appendChild(tag_elem)
        tag_elem.appendChild(name_elem)
        name_elem.appendChild(text_elem)
        result = tag_elem
    return result

def findName(tags, match):
    # Complicated but does the trick
    result = False
    for tag in tags:
        for childNode in tag.childNodes:
            if childNode.nodeName == 'name':
                for subNode in childNode.childNodes:
                    if subNode.nodeType == subNode.TEXT_NODE:
                        if subNode.nodeValue == match:
                            result = tag
    return result

def appendBranch(doc, parent, child):
    '''Links child to parent by tag name.

    Arguments
    ---------
        doc: xml Document
        parent: parent xml node
        child: child tag name

    Returns
    -------
        child_elem: can be used as parent for next level.

    '''
    child_elem = doc.createElement(child)
    parent.appendChild(child_elem)
    return child_elem

def appendName(doc, parent, tag, text, name=True):
    '''Handles named nodes.

    E.g. <parent>
            <tag>
               <name>text</name>
            </tag>
         </parent>

    '''
    tag_elem = doc.createElement(tag)
    name_elem = doc.createElement("name")
    text_node = doc.createTextNode(text)
    parent.appendChild(tag_elem)
    tag_elem.appendChild(name_elem)
    name_elem.appendChild(text_node)
    return tag_elem

def switch_dirnames(files, dirname):
    '''Replaces dirname.

    Description
        While publishing websites it is often useful to reference
        files relative to the top level of the site and not in
        a framework that the file system understands. This routine
        quickly swaps the dirnames of the input `files` with the
        second positional argument `dirname`.

    Returns
        List of files with specified dirname.

    '''
    basenames = map(os.path.basename, files)
    paths = [os.path.join(dirname, name) for name in basenames]
    return paths

def split_names(paths, sep='_', elems=[]):
    '''Splits text file names into relevant components.

    Description
        A typical file name excluding its extension which describes
        it's file type and it's dirname which describes it's 
        location in the file system is composed of words which
        indicate what the file contains. By selecting a separation
        character and a list of indices those individual words can
        be pulled out.

    Returns
        List of lists of filename components.

    '''
    no_exts = [os.path.splitext(name)[0] for name in paths]
    basenames = map(os.path.basename, no_exts)

    results = []
    for index in elems:
        parts = [name.split(sep)[index] for name in basenames]
        results.append(parts)
    return results

def xml_updater(doc, parent_group, parent_elem, branch_names, ibranch=0):
    '''Recursively moves through search keys updating the
       branches on route.''' 
    if ibranch < len(branch_names):
        # Intermediate levels
        get_item = operator.itemgetter(ibranch)
        for child, child_group in itertools.groupby(sorted(parent_group, key=get_item), get_item):
            child_elem = updateTree(doc, parent_elem, branch_names[ibranch], tag_name=child)
            return xml_updater(doc, child_group, child_elem, branch_names, ibranch+1)
        return doc
    else:
        # Final level
        data = list(parent_group)
        files = list(zip(*data)[-1])
        for file in files:
            updateTree(doc, parent_elem, 'txt', tag_name=file)
        return doc

if __name__ == '__main__':
    main()