"""
This apex script component helps add secondary and offset controls to an already defined transform.
Pretty common operation. 

I added the header and footer, but could just be deleted, and use header + template as component
"""
HoudiniVersion("21.0.440")
rigname: String = BindInput()
character: Geometry = BindInput()
graph: ApexGraphHandle = BindInput(rig=ApexGraphHandle())
bypass: Bool = BindInput()
rigname, graph = character.getRig(graph_name=rigname, graph=graph, bypass=bypass)
##### header end #####


def addExtraControls(graph: ApexGraphHandle, 
                     guides: Geometry,
                     setups: DictArray) -> tuple[ApexGraphHandle, Geometry]:
    
    for setup in setups:
    
        target : String = setup["TargetControlName#"]
        trf_pos : Int = setup["NewTransformPosition#"]
        after_prefix : String = setup["PrefixAfterControl#"]
        before_prefix : String = setup["PrefixBeforeControl#"]
        promote_t : Bool = setup["PromoteT#"]
        promote_r : Bool = setup["PromoteR#"]
        promote_s : Bool = setup["PromoteS#"]
        
        # gather data
        target_node = graph.findNode(target)
        parent_node = graph.GetTransformParent(target_node)
        children_node_array : ApexNodeIDArray = graph.GetTransformChildren(target_node)
        
        new_controls : ApexNodeIDArray = []
        # if we building an after control (or both)
        if trf_pos == 0 or trf_pos==2:
            pos = guides.getPointTransform(name=target)
            _, driverpt, drivername = guides.findOrAddGuide(name=f"{target}{after_prefix}",
                                  xform=pos,
                                  parent=target,
                                  promote="t r s",
                                  shapescale=(10,10,10),
                                  shape="cross_wires",
                                  overridecontrol=True,
                                  setshapedata=True,
                                  )
            guides.updateJoint(ptnum=driverpt, name=drivername, xform=pos)
            
            pattern = f'@name={drivername}'
            #parentname = NodeFromPattern(driverparent)
            #guides.SetParent(pattern, driverpt)
            guides = graph.controlsFromGuides(geo=guides, group=pattern)
            
            #guides.AddSetPointTransforms(name=drivername)
            
            graph.layout()
            
            
        """
            beforeCtrl = graph.addNode(f"{target}{after_prefix}", callback="TransformObject")
            #graph.UpdateNodeParms(beforeCtrl, {"properties":{shapescale:(10,10,10)}})
            if promote_t:
                beforeCtrl.t_in.promote(f"{target}{after_prefix}_t")
            if promote_r:
                beforeCtrl.r_in.promote(f"{target}{after_prefix}_r")
            if promote_s:
                beforeCtrl.s_in.promote(f"{target}{after_prefix}_s")
            
            target_node.xform_out.connect(beforeCtrl.parent_in)
            
            for child_node in children_node_array:
                beforeCtrl.xform_out.connect(child_node.parent_in)
                target_node.localxform_out.connect(child_node.parentlocal_in)
                
            
            new_controls.append(beforeCtrl)
        """ 
        #graph.AddSetPointTransforms("pointtransform", new_controls, srcport="xform")
    
    graph.layout()
    
    return graph, guides

# create a bind multiparam
setups = bindMultiparm(preset_kwargs={"label":"test"})

addToMultiparm(setups, "TargetControlName", "")
addToMultiparm(setups, "NewTransformPosition", 0, 
               preset='menu',
               preset_kwargs={'menu_labels':['after', 'before', 'both'],
                              'menu_items':[0,1,2]})
addToMultiparm(setups, "PrefixAfterControl", "_secondary",preset_kwargs={'joins_with_next':1})
addToMultiparm(setups, "PrefixBeforeControl", "_offset", preset_kwargs={"disable_when":"{NewTransformPosition==2}"})

# could maybe split this up as well.. 
addToMultiparm(setups, "PromoteT", True, preset_kwargs={'joins_with_next':1})
addToMultiparm(setups, "PromoteR", True, preset_kwargs={'joins_with_next':1})
addToMultiparm(setups, "PromoteS", False)

guidesource: String = bindInput()

#Setup
guides = character.findCharacterElement(guidesource)
guides = graph.addExtraControls(guides=guides, setups=setups)
character.updateCharacterElement(guidesource, guides)




### footer end
character.updateRig(graph_name=rigname, graph=graph, bypass=bypass)
BindOutput(character)
BindOutput(rig=graph)

